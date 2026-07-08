"""Multi-ETF market price panel loader.

This module provides the recommended one-shot primitive for loading market
prices for multiple ETFs over a date range in a single SELECT. Callers that
need historical prices across more than one ETF should use ``load_price_panel``
rather than iterating per-ETF ``select`` calls.

The returned mapping groups ``MarketPrice`` rows by ``etf_id`` in ascending
``trade_date`` order. The caller owns the lifecycle of the returned mapping:
the loader does not cache or mutate it.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice


def load_price_panel(
    session: Session,
    *,
    etf_ids: Iterable[int],
    start_date: date | None,
    end_date: date,
) -> dict[int, list[MarketPrice]]:
    """Load daily market prices for the given ETF ids over a date range.

    Issues a single ``SELECT`` against ``market_price`` filtered on
    ``etf_id IN (...)`` AND ``trade_date BETWEEN start_date AND end_date``,
    reusing the existing ``ix_market_price_etf_trade_date`` composite index.

    Returns a mapping from each requested ETF id to the list of rows in
    ascending ``trade_date`` order. ETFs with no rows in the range are
    omitted from the mapping.

    The caller owns the returned mapping; this function does not cache it
    and does not mutate it after return.
    """
    ids = list(etf_ids)
    if not ids:
        return {}

    stmt = select(MarketPrice).where(MarketPrice.etf_id.in_(ids))
    if start_date is not None:
        stmt = stmt.where(MarketPrice.trade_date >= start_date)
    stmt = stmt.where(MarketPrice.trade_date <= end_date).order_by(
        MarketPrice.etf_id, MarketPrice.trade_date
    )

    panel: dict[int, list[MarketPrice]] = defaultdict(list)
    for price in session.scalars(stmt).all():
        panel[price.etf_id].append(price)

    return dict(panel)