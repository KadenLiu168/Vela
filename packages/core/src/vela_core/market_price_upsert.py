from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice

# Sized for the 2-column `(etf_id, trade_date)` key expanded into the
# `tuple_(...).in_(...)` SELECT: 16_000 * 2 = 32_000 binds, below the SQLite
# default `SQLITE_MAX_VARIABLE_NUMBER = 32_766`. Re-evaluate if the key
# columns change.
BATCH_SIZE: int = 16_000


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

    # `execute(stmt, rows)` (rather than `stmt.values(rows); execute(stmt)`)
    # is required so SQLAlchemy 2.0 routes the INSERT through SQLite's
    # `insertmanyvalues` optimization, which auto-chunks the bind parameters
    # and avoids `too many SQL variables` on large batches.
    #
    # ``factor_hfq`` is intentionally absent from the conflict update set: the
    # backward-adjustment factor is an append-only snapshot, so an existing
    # row's factor is never overwritten by a refetch (immune to upstream
    # retroactive factor revisions). New rows still receive their factor via
    # the INSERT values below.
    statement = insert(MarketPrice).on_conflict_do_update(
        index_elements=[MarketPrice.etf_id, MarketPrice.trade_date],
        set_={
            "open_price": insert(MarketPrice).excluded.open_price,
            "high_price": insert(MarketPrice).excluded.high_price,
            "low_price": insert(MarketPrice).excluded.low_price,
            "close_price": insert(MarketPrice).excluded.close_price,
            "volume": insert(MarketPrice).excluded.volume,
            "updated_at": func.now(),
        },
    )
    session.execute(statement, rows)

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
    existing_keys: set[tuple[int, date]] = set()
    for batch in _chunked(list(keys), BATCH_SIZE):
        rows = session.execute(
            select(MarketPrice.etf_id, MarketPrice.trade_date).where(
                tuple_(MarketPrice.etf_id, MarketPrice.trade_date).in_(batch)
            )
        )
        existing_keys.update((etf_id, trade_date) for etf_id, trade_date in rows)
    return existing_keys


def _market_price_values(market_price: MarketPrice) -> dict[str, object]:
    return {
        "etf_id": market_price.etf_id,
        "trade_date": market_price.trade_date,
        "open_price": market_price.open_price,
        "high_price": market_price.high_price,
        "low_price": market_price.low_price,
        "close_price": market_price.close_price,
        "factor_hfq": market_price.factor_hfq,
        "volume": market_price.volume,
    }


def _chunked(items: Sequence[tuple[int, date]], size: int) -> list[list[tuple[int, date]]]:
    return [list(items[i : i + size]) for i in range(0, len(items), size)]
