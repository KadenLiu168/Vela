"""Forward-adjusted (qfq) price projection from stored factors.

Forward-adjusted prices are derived at query time from stored unadjusted
close prices and backward-adjustment factors; they are never persisted or
cached. Anchoring at rebalance date ``T`` gives
``qfq(D) = close_price(D) * factor_hfq(D) / factor_hfq(T)``, so
``qfq(T) == close_price(T)`` (the unadjusted execution price) and any
ratio-based signal is identical whether computed from the forward- or
backward-adjusted series, because the two differ only by the constant
``factor_hfq(T)`` which cancels in any ratio.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from vela_core.models import MarketPrice


@dataclass(frozen=True)
class ForwardAdjustedPrice:
    """A single forward-adjusted (qfq) price point in a rebalance-anchored series."""

    trade_date: date
    price: Decimal


def forward_adjusted_prices(
    prices: Sequence[MarketPrice],
    *,
    rebalance_date: date,
) -> list[ForwardAdjustedPrice]:
    """Compute the forward-adjusted (qfq) price series anchored at ``rebalance_date``.

    For each row ``D`` in ``prices``: ``qfq(D) = close_price(D) *
    factor_hfq(D) / factor_hfq(T)`` where ``T`` is ``rebalance_date``. The
    rebalance date must be present in ``prices``; by construction
    ``qfq(T) == close_price(T)`` (the unadjusted execution price).

    Pure function: performs no database access, persists nothing, and caches
    nothing -- the series is recomputed on every call so it always reflects
    the current stored factor series and the caller's chosen anchor.
    """
    if not prices:
        return []

    anchor = next((price for price in prices if price.trade_date == rebalance_date), None)
    if anchor is None:
        raise ValueError(f"rebalance date {rebalance_date} not found in price series")

    anchor_factor = anchor.factor_hfq
    return [
        ForwardAdjustedPrice(
            trade_date=price.trade_date,
            price=(price.close_price * price.factor_hfq) / anchor_factor,
        )
        for price in prices
    ]
