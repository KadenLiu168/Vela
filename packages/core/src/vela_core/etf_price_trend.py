"""Single-ETF forward-adjusted daily price trend.

Derives a forward-adjusted (qfq) daily price series for one ETF over a
selected time window, computed at query time from stored ``market_price``
rows. Each price is normalized through ``forward_adjusted_prices`` using the
latest selected date as anchor, so ex-dividend days do not produce phantom
gaps in the trend. Adjusted prices are never persisted or cached.

``range`` selects a *time window* anchored at the ETF's latest persisted
``trade_date``; it does not resample. Daily precision is preserved -- the
window only narrows the ``start_date`` / ``end_date`` filter, matching the
mainstream financial-UI range-button semantics.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, MarketPrice

PriceTrendRange = Literal["1m", "3m", "1y", "3y", "max"]

#: Maps each range to the number of calendar months to shift back from the
#: ETF's latest persisted trade date. ``max`` has no lower bound (``None``).
_RANGE_MONTHS: Mapping[PriceTrendRange, int | None] = {
    "1m": 1,
    "3m": 3,
    "1y": 12,
    "3y": 36,
    "max": None,
}


@dataclass(frozen=True)
class EtfPriceTrendPoint:
    """A single forward-adjusted daily price point in a trend series."""

    trade_date: date
    price: Decimal


@dataclass(frozen=True)
class EtfPriceTrendResult:
    """Forward-adjusted daily price trend for one ETF over a time window.

    ``points`` is empty when the ETF exists but has no persisted
    ``market_price`` rows in the window. A missing ``ETFInfo`` row is
    signaled by ``get_etf_price_trend`` returning ``None`` instead.
    """

    etf_id: int
    exchange: str
    symbol: str
    name: str
    points: tuple[EtfPriceTrendPoint, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "etf": {
                "id": self.etf_id,
                "exchange": self.exchange,
                "symbol": self.symbol,
                "name": self.name,
            },
            "points": [
                {
                    "trade_date": point.trade_date.isoformat(),
                    "price": str(point.price),
                }
                for point in self.points
            ],
        }


def get_etf_price_trend(
    session: Session,
    *,
    etf_id: int,
    range_: PriceTrendRange = "1y",
) -> EtfPriceTrendResult | None:
    """Return the forward-adjusted daily price trend for one ETF.

    Resolves ``range_`` to a date window anchored at the ETF's latest
    persisted ``trade_date`` per design D6, loads the matching
    ``market_price`` rows via ``load_price_panel`` (single SELECT on
    ``ix_market_price_etf_trade_date``), and projects each row to
    forward-adjusted values at query time without persisting.

    Returns ``None`` when no ``ETFInfo`` row exists for ``etf_id`` (a
    distinct not-found signal). Returns a result with empty ``points`` when
    the ETF exists but has no persisted prices.

    Pure query function: performs no mutation, persists nothing, caches
    nothing -- the series is recomputed on every call so it always reflects
    the current stored price/factor series.
    """
    etf = session.get(ETFInfo, etf_id)
    if etf is None:
        return None

    end_date = session.scalar(
        select(func.max(MarketPrice.trade_date)).where(MarketPrice.etf_id == etf_id)
    )
    if end_date is None:
        return EtfPriceTrendResult(
            etf_id=etf.id,
            exchange=etf.exchange,
            symbol=etf.symbol,
            name=etf.name,
            points=(),
        )

    start_date = _range_start_date(range_, end_date)
    panel = load_price_panel(
        session,
        etf_ids=[etf_id],
        start_date=start_date,
        end_date=end_date,
    )
    projected_prices = forward_adjusted_prices(panel.get(etf_id, []), rebalance_date=end_date)
    points = tuple(
        EtfPriceTrendPoint(trade_date=row.trade_date, price=row.price) for row in projected_prices
    )
    return EtfPriceTrendResult(
        etf_id=etf.id,
        exchange=etf.exchange,
        symbol=etf.symbol,
        name=etf.name,
        points=points,
    )


def _range_start_date(range_: PriceTrendRange, end_date: date) -> date | None:
    """Resolve the inclusive lower bound for a range anchored at ``end_date``.

    ``max`` returns ``None`` (no lower bound). The window end is always the
    ETF's latest persisted ``trade_date`` rather than ``today``, so
    weekend/holiday tails do not produce an empty trailing segment. A
    ``start_date`` that lands on a non-trading day is harmless: the DB
    filter ``trade_date >= start_date`` naturally yields the next trading
    day.
    """
    months = _RANGE_MONTHS[range_]
    if months is None:
        return None
    return _shift_months(end_date, months)


def _shift_months(value: date, months: int) -> date:
    """Shift ``value`` back by ``months`` calendar months, day-clamped.

    Uses calendar-month arithmetic with day-clamping to the target month's
    last day (e.g. 2026-05-31 shifted back one month is 2026-04-30), so no
    external date library is required.
    """
    import calendar

    total = value.year * 12 + (value.month - 1) - months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(value.day, last_day))
