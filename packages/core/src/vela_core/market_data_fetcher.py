import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vela_core.data_quality import (
    EtfTradingDayGap,
    SystematicTradingDayGap,
    build_quality_warnings_json_from_sections,
    detect_duplicate_trade_dates,
    detect_etf_trading_day_gaps,
    detect_systematic_trading_day_gaps,
)
from vela_core.market_data_provider import MarketDataProvider
from vela_core.market_price_mapping import to_market_price
from vela_core.market_price_upsert import upsert_market_prices
from vela_core.models import DataFetchLog, ETFInfo, MarketPrice, TradingCalendar


@dataclass(frozen=True)
class MarketDataFetchResult:
    fetch_log_id: int
    status: str
    requested_symbol_count: int
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    failed_symbols: tuple[str, ...] = ()
    error_message: str | None = None
    quality_warnings: str | None = None


def fetch_full_market_prices(
    session: Session,
    *,
    provider: MarketDataProvider,
) -> MarketDataFetchResult:
    return _fetch_market_prices(
        session,
        provider=provider,
        fetch_mode="full",
        range_start=None,
        range_end=None,
    )


def fetch_incremental_market_prices(
    session: Session,
    *,
    provider: MarketDataProvider,
) -> MarketDataFetchResult:
    latest_trade_date = session.scalar(select(func.max(MarketPrice.trade_date)))
    range_start = latest_trade_date + timedelta(days=1) if latest_trade_date is not None else None
    return _fetch_market_prices(
        session,
        provider=provider,
        fetch_mode="incremental",
        range_start=range_start,
        range_end=_today(),
    )


def _fetch_market_prices(
    session: Session,
    *,
    provider: MarketDataProvider,
    fetch_mode: str,
    range_start: date | None,
    range_end: date | None,
) -> MarketDataFetchResult:
    active_etfs = _active_etfs(session)
    requested_symbols = [etf.symbol for etf in active_etfs]
    fetch_log = DataFetchLog(
        source=provider.name,
        target_type="market_price",
        fetch_mode=fetch_mode,
        range_start=range_start,
        range_end=range_end,
        requested_symbols=json.dumps(requested_symbols),
        started_at=_now(),
        status="running",
    )
    session.add(fetch_log)
    session.flush()

    if fetch_mode == "incremental" and range_start is None:
        no_baseline_error = "No local market price baseline found"
        _finish_log(
            fetch_log,
            status="failed",
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message=no_baseline_error,
            quality_warnings=None,
        )
        session.flush()
        return MarketDataFetchResult(
            fetch_log_id=fetch_log.id,
            status="failed",
            requested_symbol_count=len(requested_symbols),
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message=no_baseline_error,
            quality_warnings=None,
        )

    if not active_etfs:
        no_active_error = "No active ETFs found"
        _finish_log(
            fetch_log,
            status="failed",
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message=no_active_error,
            quality_warnings=None,
        )
        session.flush()
        return MarketDataFetchResult(
            fetch_log_id=fetch_log.id,
            status="failed",
            requested_symbol_count=0,
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message=no_active_error,
            quality_warnings=None,
        )

    market_prices: list[MarketPrice] = []
    errors: list[str] = []
    failed_symbols: list[str] = []

    for etf in active_etfs:
        try:
            daily_prices = provider.get_etf_daily_prices(
                etf.symbol,
                start_date=range_start,
                end_date=range_end,
            )
        except Exception as exc:
            failed_symbols.append(etf.symbol)
            errors.append(f"{etf.symbol}: {exc}")
            continue

        market_prices.extend(to_market_price(price, etf_id=etf.id) for price in daily_prices)

    rows_fetched = len(market_prices)
    duplicate_warnings = detect_duplicate_trade_dates(market_prices)
    rows_inserted = 0
    rows_updated = 0
    if market_prices:
        upsert_result = upsert_market_prices(session, market_prices)
        rows_inserted = upsert_result.rows_inserted
        rows_updated = upsert_result.rows_updated

    gap_result = _detect_fetch_gap_warnings(session, active_etfs, range_start, range_end)
    systematic_gaps, etf_gaps = gap_result if gap_result is not None else ([], [])
    quality_warnings = build_quality_warnings_json_from_sections(
        duplicate_warnings, systematic_gaps, etf_gaps
    )

    status = _final_status(rows_fetched=rows_fetched, has_errors=bool(errors))
    error_message = _error_message(errors=errors, rows_fetched=rows_fetched)
    _finish_log(
        fetch_log,
        status=status,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        error_message=error_message,
        quality_warnings=quality_warnings,
    )
    session.flush()

    return MarketDataFetchResult(
        fetch_log_id=fetch_log.id,
        status=status,
        requested_symbol_count=len(requested_symbols),
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        failed_symbols=tuple(failed_symbols),
        error_message=error_message,
        quality_warnings=quality_warnings,
    )


def _active_etfs(session: Session) -> list[ETFInfo]:
    return list(
        session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.symbol))
    )


def _detect_fetch_gap_warnings(
    session: Session,
    active_etfs: list[ETFInfo],
    range_start: date | None,
    range_end: date | None,
) -> tuple[list[SystematicTradingDayGap], list[EtfTradingDayGap]] | None:
    """Detect trading-day gaps against the calendar after a fetch upsert.

    Returns ``None`` when the trading calendar has no rows covering the
    effective range (calendar not synced) or when the local price table is
    empty, so callers fall back to duplicate-only warnings. Gap detection is
    warn-only; it never changes the fetch status.
    """
    start = range_start or session.scalar(select(func.min(MarketPrice.trade_date)))
    end = range_end or session.scalar(select(func.max(MarketPrice.trade_date)))
    if start is None or end is None or start > end:
        return None

    expected_dates = list(
        session.scalars(
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date >= start)
            .where(TradingCalendar.trade_date <= end)
            .order_by(TradingCalendar.trade_date)
        )
    )
    if not expected_dates:
        return None

    union_dates = list(
        session.scalars(
            select(MarketPrice.trade_date)
            .where(MarketPrice.trade_date >= start)
            .where(MarketPrice.trade_date <= end)
            .distinct()
            .order_by(MarketPrice.trade_date)
        )
    )

    etf_rows = session.execute(
        select(MarketPrice.etf_id, MarketPrice.trade_date)
        .where(MarketPrice.trade_date >= start)
        .where(MarketPrice.trade_date <= end)
    ).all()
    per_etf: dict[int, list[date]] = defaultdict(list)
    for etf_id, trade_date in etf_rows:
        per_etf[etf_id].append(trade_date)

    inception_boundaries: dict[int, date] = {}
    for etf in active_etfs:
        stored = per_etf.get(etf.id)
        if not stored:
            continue
        first_stored = min(stored)
        boundary = first_stored
        if etf.inception_date is not None and etf.inception_date > boundary:
            boundary = etf.inception_date
        inception_boundaries[etf.id] = boundary

    systematic_gaps = detect_systematic_trading_day_gaps(union_dates, expected_dates)
    etf_gaps = detect_etf_trading_day_gaps(per_etf, expected_dates, inception_boundaries)
    return systematic_gaps, etf_gaps


def _final_status(*, rows_fetched: int, has_errors: bool) -> str:
    if has_errors and rows_fetched > 0:
        return "partial"
    if has_errors or rows_fetched == 0:
        return "failed"
    return "success"


def _error_message(*, errors: list[str], rows_fetched: int) -> str | None:
    if errors:
        return "; ".join(errors)
    if rows_fetched == 0:
        return "No market prices fetched"
    return None


def _now() -> datetime:
    return datetime.now(UTC)


def _today() -> date:
    return date.today()


def _finish_log(
    fetch_log: DataFetchLog,
    *,
    status: str,
    rows_fetched: int,
    rows_inserted: int,
    rows_updated: int,
    error_message: str | None,
    quality_warnings: str | None,
) -> None:
    fetch_log.status = status
    fetch_log.finished_at = _now()
    fetch_log.rows_fetched = rows_fetched
    fetch_log.rows_inserted = rows_inserted
    fetch_log.rows_updated = rows_updated
    fetch_log.error_message = error_message
    fetch_log.quality_warnings = quality_warnings
