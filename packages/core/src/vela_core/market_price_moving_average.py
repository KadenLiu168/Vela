from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.market_price_query import load_price_panel
from vela_core.models import MarketPrice


@dataclass(frozen=True)
class MarketPriceMovingAverage:
    etf_id: int
    as_of_date: date
    window: int
    ma: Decimal | None


def _moving_average_from_prices(
    prices: list[MarketPrice],
    *,
    etf_id: int,
    as_of_date: date,
    window: int,
) -> MarketPriceMovingAverage:
    """Pure-function MA over an in-memory ascending price series.

    ``prices`` MUST be sorted by ``trade_date`` ascending. The function
    consumes the first ``window`` entries; if fewer rows are available
    or the most recent row is older than ``as_of_date``, ``ma`` is null.
    """
    if len(prices) < window or prices[-1].trade_date != as_of_date:
        return MarketPriceMovingAverage(
            etf_id=etf_id,
            as_of_date=as_of_date,
            window=window,
            ma=None,
        )

    return MarketPriceMovingAverage(
        etf_id=etf_id,
        as_of_date=as_of_date,
        window=window,
        ma=sum(
            (price.price for price in forward_adjusted_prices(prices, rebalance_date=as_of_date)),
            Decimal("0"),
        )
        / Decimal(window),
    )


def calculate_market_price_moving_average(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
    window: int,
) -> MarketPriceMovingAverage:
    """Compatibility wrapper that loads a single-ETF panel then delegates.

    Prefer the panel-driven flow in ``generate_strategy_signal`` and
    ``apply_trend_filter`` for new code; this entry point remains for
    callers that already hold a session and want a single MA value.
    """
    panel = load_price_panel(
        session,
        etf_ids=[etf_id],
        start_date=None,
        end_date=as_of_date,
    )
    # Trim to the most-recent ``window`` rows so callers that historically
    # used ``ORDER BY trade_date DESC LIMIT window`` see the same window.
    prices = panel.get(etf_id, [])[-window:]

    return _moving_average_from_prices(
        prices,
        etf_id=etf_id,
        as_of_date=as_of_date,
        window=window,
    )
