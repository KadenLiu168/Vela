from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.market_price_query import load_price_panel
from vela_core.models import MarketPrice
from vela_core.resolved_session_price import ResolvedSessionPrice
from vela_core.strategy_config import DualMomentumParams


@dataclass(frozen=True)
class TrendFilterResult:
    etf_id: int
    as_of_date: date
    current_price: Decimal | None
    moving_average: Decimal | None
    passes_filter: bool


def _trend_filter_from_prices(
    prices: Sequence[MarketPrice | ResolvedSessionPrice],
    *,
    etf_id: int,
    as_of_date: date,
    parameters: DualMomentumParams,
) -> TrendFilterResult:
    """Pure-function trend filter over an in-memory ascending price series.

    ``prices`` MUST be sorted by ``trade_date`` ascending. The series is
    expected to contain at least the longest window (trend
    ``moving_average_days``) of rows through ``as_of_date``.
    """
    window = parameters.trend_filter.moving_average_days
    relation = parameters.trend_filter.price_relation

    if not prices or prices[-1].trade_date != as_of_date:
        return TrendFilterResult(
            etf_id=etf_id,
            as_of_date=as_of_date,
            current_price=None,
            moving_average=None,
            passes_filter=False,
        )

    adjusted_prices = forward_adjusted_prices(prices, rebalance_date=as_of_date)
    current_price = adjusted_prices[-1].price

    if len(prices) < window:
        return TrendFilterResult(
            etf_id=etf_id,
            as_of_date=as_of_date,
            current_price=current_price,
            moving_average=None,
            passes_filter=False,
        )

    ma_value = sum(
        (price.price for price in adjusted_prices[-window:]),
        Decimal("0"),
    ) / Decimal(window)

    passes_filter = (relation == "above" and current_price > ma_value) or (
        relation == "below" and current_price < ma_value
    )

    return TrendFilterResult(
        etf_id=etf_id,
        as_of_date=as_of_date,
        current_price=current_price,
        moving_average=ma_value,
        passes_filter=passes_filter,
    )


def apply_trend_filter(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
    parameters: DualMomentumParams,
) -> TrendFilterResult:
    """Compatibility wrapper that loads a single-ETF panel then delegates.

    Prefer the panel-driven flow in ``generate_strategy_signal`` for new
    code; this entry point remains for callers that already hold a
    session and want a single trend verdict.
    """
    window = parameters.trend_filter.moving_average_days
    panel = load_price_panel(
        session,
        etf_ids=[etf_id],
        start_date=None,
        end_date=as_of_date,
    )
    # Trim to the most-recent ``window`` rows so the trend verdict uses
    # the same rows the historical ``LIMIT window`` query did.
    prices = panel.get(etf_id, [])[-window:]

    return _trend_filter_from_prices(
        prices,
        etf_id=etf_id,
        as_of_date=as_of_date,
        parameters=parameters,
    )
