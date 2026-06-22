from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice


@dataclass(frozen=True)
class MarketPriceUpsertResult:
    rows_inserted: int
    rows_updated: int


def upsert_market_prices(
    session: Session,
    market_prices: Sequence[MarketPrice],
) -> MarketPriceUpsertResult:
    deduped_prices = _deduplicate_market_prices(market_prices)
    if not deduped_prices:
        return MarketPriceUpsertResult(rows_inserted=0, rows_updated=0)

    keys = list(deduped_prices)
    existing_keys = _existing_market_price_keys(session, keys)
    rows = [_market_price_values(price) for price in deduped_prices.values()]

    statement = insert(MarketPrice).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=[MarketPrice.etf_id, MarketPrice.trade_date],
        set_={
            "open_price": statement.excluded.open_price,
            "high_price": statement.excluded.high_price,
            "low_price": statement.excluded.low_price,
            "close_price": statement.excluded.close_price,
            "adjusted_close": statement.excluded.adjusted_close,
            "volume": statement.excluded.volume,
            "updated_at": func.now(),
        },
    )
    session.execute(statement)

    return MarketPriceUpsertResult(
        rows_inserted=len(keys) - len(existing_keys),
        rows_updated=len(existing_keys),
    )


def _deduplicate_market_prices(
    market_prices: Sequence[MarketPrice],
) -> dict[tuple[int, date], MarketPrice]:
    deduped_prices: dict[tuple[int, date], MarketPrice] = {}
    for market_price in market_prices:
        deduped_prices[(market_price.etf_id, market_price.trade_date)] = market_price
    return deduped_prices


def _existing_market_price_keys(
    session: Session,
    keys: Sequence[tuple[int, date]],
) -> set[tuple[int, date]]:
    rows = session.execute(
        select(MarketPrice.etf_id, MarketPrice.trade_date).where(
            tuple_(MarketPrice.etf_id, MarketPrice.trade_date).in_(keys)
        )
    )
    return {(etf_id, trade_date) for etf_id, trade_date in rows}


def _market_price_values(market_price: MarketPrice) -> dict[str, object]:
    return {
        "etf_id": market_price.etf_id,
        "trade_date": market_price.trade_date,
        "open_price": market_price.open_price,
        "high_price": market_price.high_price,
        "low_price": market_price.low_price,
        "close_price": market_price.close_price,
        "adjusted_close": market_price.adjusted_close,
        "volume": market_price.volume,
    }
