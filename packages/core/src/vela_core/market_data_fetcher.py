import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vela_core.data_quality import (
    CorporateActionFactorMismatchWarning,
    EtfTradingDayGap,
    SystematicTradingDayGap,
    build_quality_warnings_json_from_sections,
    detect_corporate_action_factor_mismatch,
    detect_duplicate_trade_dates,
    detect_etf_trading_day_gaps,
    detect_systematic_trading_day_gaps,
)
from vela_core.market_data_provider import MarketDataProvider
from vela_core.market_price_mapping import to_market_price
from vela_core.market_price_upsert import upsert_market_prices
from vela_core.models import DataFetchLog, ETFInfo, MarketPrice, TradingCalendar

logger = logging.getLogger(__name__)


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
    # ``range_start`` is the latest stored trade date (inclusive), used for the
    # fetch-log record and the no-baseline guard. Per-ETF fetches start at each
    # ETF's own last stored date so the stored last-row factor can be compared
    # against the upstream same-date factor to detect corporate actions.
    range_start = latest_trade_date
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
    started = time.perf_counter()
    logger.info("market_data.fetch.started provider=%s mode=%s", provider.name, fetch_mode)
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
        result = MarketDataFetchResult(
            fetch_log_id=fetch_log.id,
            status="failed",
            requested_symbol_count=len(requested_symbols),
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message=no_baseline_error,
            quality_warnings=None,
        )
        _log_fetch_completion(result, provider=provider.name, started=started)
        return result

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
        result = MarketDataFetchResult(
            fetch_log_id=fetch_log.id,
            status="failed",
            requested_symbol_count=0,
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message=no_active_error,
            quality_warnings=None,
        )
        _log_fetch_completion(result, provider=provider.name, started=started)
        return result

    corporate_action_warnings: list[CorporateActionFactorMismatchWarning] = []
    if fetch_mode == "incremental":
        market_prices, errors, failed_symbols, corporate_action_warnings = (
            _collect_incremental_prices(session, active_etfs, provider, range_end)
        )
    else:
        market_prices, errors, failed_symbols = _collect_full_prices(
            active_etfs, provider, range_start, range_end
        )

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
        duplicate_warnings,
        systematic_gaps,
        etf_gaps,
        corporate_action_warnings=corporate_action_warnings,
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

    result = MarketDataFetchResult(
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
    _log_fetch_completion(result, provider=provider.name, started=started)
    return result


def _log_fetch_completion(result: MarketDataFetchResult, *, provider: str, started: float) -> None:
    logger.info(
        "market_data.fetch.completed provider=%s status=%s requested_etf_count=%s "
        "rows_fetched=%s duration_ms=%.3f",
        provider,
        result.status,
        result.requested_symbol_count,
        result.rows_fetched,
        (time.perf_counter() - started) * 1000,
    )


def _collect_full_prices(
    active_etfs: list[ETFInfo],
    provider: MarketDataProvider,
    range_start: date | None,
    range_end: date | None,
) -> tuple[list[MarketPrice], list[str], list[str]]:
    """Fetch full history for every active ETF (full fetch mode)."""
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

    return market_prices, errors, failed_symbols


def _collect_incremental_prices(
    session: Session,
    active_etfs: list[ETFInfo],
    provider: MarketDataProvider,
    range_end: date | None,
) -> tuple[list[MarketPrice], list[str], list[str], list[CorporateActionFactorMismatchWarning]]:
    """Fetch incremental prices with per-ETF corporate-action factor checks.

    For each ETF, fetch starting at its own last stored trade date so the
    stored last-row factor can be compared against the upstream same-date
    factor. On a factor mismatch (corporate action detected) the ETF is
    fully refetched. A successful refetch rewrites factors for provider-returned
    existing rows; it does not delete or repair historical dates the provider
    did not return. Otherwise only rows newer than the last stored date append.
    """
    market_prices: list[MarketPrice] = []
    errors: list[str] = []
    failed_symbols: list[str] = []
    corporate_action_warnings: list[CorporateActionFactorMismatchWarning] = []

    for etf in active_etfs:
        last_stored = _stored_last_row(session, etf.id)
        fetch_start = last_stored[0] if last_stored is not None else None
        try:
            daily_prices = provider.get_etf_daily_prices(
                etf.symbol,
                start_date=fetch_start,
                end_date=range_end,
            )
        except Exception as exc:
            failed_symbols.append(etf.symbol)
            errors.append(f"{etf.symbol}: {exc}")
            continue

        if last_stored is None:
            market_prices.extend(to_market_price(price, etf_id=etf.id) for price in daily_prices)
            continue

        last_date, last_factor = last_stored
        upstream_last = next(
            (price for price in daily_prices if price.trade_date == last_date),
            None,
        )
        if upstream_last is not None:
            warning = detect_corporate_action_factor_mismatch(
                etf_id=etf.id,
                trade_date=last_date,
                stored_factor=last_factor,
                upstream_factor=upstream_last.factor,
            )
            if warning is not None:
                corporate_action_warnings.append(warning)
                market_prices.extend(
                    _refetch_full_history(etf, provider, range_end, errors, failed_symbols)
                )
                continue

        for price in daily_prices:
            if price.trade_date > last_date:
                market_prices.append(to_market_price(price, etf_id=etf.id))

    return market_prices, errors, failed_symbols, corporate_action_warnings


def _refetch_full_history(
    etf: ETFInfo,
    provider: MarketDataProvider,
    range_end: date | None,
    errors: list[str],
    failed_symbols: list[str],
) -> list[MarketPrice]:
    """Full refetch for one ETF after a corporate-action factor mismatch."""
    try:
        daily_prices = provider.get_etf_daily_prices(
            etf.symbol,
            start_date=None,
            end_date=range_end,
        )
    except Exception as exc:
        failed_symbols.append(etf.symbol)
        errors.append(f"{etf.symbol}: corporate-action refetch failed: {exc}")
        return []
    return [to_market_price(price, etf_id=etf.id) for price in daily_prices]


def _stored_last_row(session: Session, etf_id: int) -> tuple[date, Decimal] | None:
    """Return ``(trade_date, factor_hfq)`` of the latest stored row for an ETF."""
    row = session.execute(
        select(MarketPrice.trade_date, MarketPrice.factor_hfq)
        .where(MarketPrice.etf_id == etf_id)
        .order_by(MarketPrice.trade_date.desc())
        .limit(1)
    ).first()
    return (row.trade_date, row.factor_hfq) if row is not None else None


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
