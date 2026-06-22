import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.market_data_provider import MarketDataProvider
from vela_core.market_price_mapping import to_market_price
from vela_core.market_price_upsert import upsert_market_prices
from vela_core.models import DataFetchLog, ETFInfo, MarketPrice


@dataclass(frozen=True)
class MarketDataFetchResult:
    fetch_log_id: int
    status: str
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    error_message: str | None = None


def fetch_market_prices(
    session: Session,
    *,
    provider: MarketDataProvider,
    fetch_mode: str,
    symbols: Sequence[str],
    start_date: date | None = None,
    end_date: date | None = None,
) -> MarketDataFetchResult:
    if fetch_mode not in DataFetchLog.FETCH_MODES:
        raise ValueError(f"Unsupported fetch mode: {fetch_mode}")

    requested_symbols = list(symbols)
    fetch_log = DataFetchLog(
        source=provider.name,
        target_type="market_price",
        fetch_mode=fetch_mode,
        range_start=start_date,
        range_end=end_date,
        requested_symbols=json.dumps(requested_symbols),
        started_at=_now(),
        status="running",
    )
    session.add(fetch_log)
    session.flush()

    market_prices: list[MarketPrice] = []
    errors: list[str] = []
    etfs_by_symbol = _etfs_by_symbol(session, requested_symbols)

    for symbol in requested_symbols:
        etf = etfs_by_symbol.get(symbol)
        if etf is None:
            errors.append(f"{symbol}: ETF metadata not found")
            continue

        try:
            daily_prices = provider.get_etf_daily_prices(
                symbol,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            errors.append(f"{symbol}: {exc}")
            continue

        market_prices.extend(to_market_price(price, etf_id=etf.id) for price in daily_prices)

    rows_fetched = len(market_prices)
    rows_inserted = 0
    rows_updated = 0
    if market_prices:
        upsert_result = upsert_market_prices(session, market_prices)
        rows_inserted = upsert_result.rows_inserted
        rows_updated = upsert_result.rows_updated

    status = _final_status(rows_fetched=rows_fetched, has_errors=bool(errors))
    error_message = "; ".join(errors) if errors else None
    fetch_log.status = status
    fetch_log.finished_at = _now()
    fetch_log.rows_fetched = rows_fetched
    fetch_log.rows_inserted = rows_inserted
    fetch_log.rows_updated = rows_updated
    fetch_log.error_message = error_message
    session.flush()

    return MarketDataFetchResult(
        fetch_log_id=fetch_log.id,
        status=status,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        error_message=error_message,
    )


def _etfs_by_symbol(session: Session, symbols: Sequence[str]) -> dict[str, ETFInfo]:
    if not symbols:
        return {}

    rows = session.scalars(select(ETFInfo).where(ETFInfo.symbol.in_(symbols)))
    return {etf.symbol: etf for etf in rows}


def _final_status(*, rows_fetched: int, has_errors: bool) -> str:
    if has_errors and rows_fetched > 0:
        return "partial"
    if has_errors:
        return "failed"
    return "success"


def _now() -> datetime:
    return datetime.now(UTC)
