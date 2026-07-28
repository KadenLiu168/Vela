from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import TypeAlias

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.models import MarketPrice
from vela_core.portfolio_holdings import PortfolioHoldingSnapshot, calculate_portfolio_holdings
from vela_core.strategy_config import StrategyConfig

_SIX_PLACES = Decimal("0.000001")
_BASIS_POINTS = Decimal("10000")
_PriceKey: TypeAlias = tuple[int, date]


@dataclass(frozen=True)
class StrategyEquityCurvePoint:
    trade_date: date
    net_value: Decimal
    daily_return: Decimal
    portfolio_state: "StrategyPortfolioState | None" = field(default=None, compare=False)


@dataclass(frozen=True)
class StrategyPortfolioPosition:
    etf_id: int
    target_weight: Decimal
    actual_weight: Decimal


@dataclass(frozen=True)
class StrategyPortfolioState:
    cash: Decimal
    market_value: Decimal
    total_assets: Decimal
    positions: tuple[StrategyPortfolioPosition, ...]


@dataclass(frozen=True)
class StrategyAnnualizedReturn:
    total_return: Decimal | None
    annualized_return: Decimal | None


@dataclass(frozen=True)
class StrategyMaximumDrawdown:
    max_drawdown: Decimal
    peak_date: date | None
    trough_date: date | None


@dataclass(frozen=True)
class StrategyVolatility:
    volatility: Decimal | None


@dataclass(frozen=True)
class StrategySharpeRatio:
    sharpe_ratio: Decimal | None


def calculate_strategy_equity_curve(
    session: Session,
    *,
    trading_dates: list[date],
    strategy_config: StrategyConfig,
    signal_ids: Sequence[int] | None = None,
    price_panel: dict[int, list[MarketPrice]] | None = None,
) -> list[StrategyEquityCurvePoint]:
    if not trading_dates:
        return []

    holding_snapshots = calculate_portfolio_holdings(
        session,
        trading_dates=trading_dates,
        strategy_id=strategy_config.strategy_id,
        config_version=strategy_config.version,
        signal_ids=signal_ids,
    )
    prices_by_key = _load_prices_by_key(
        session,
        holding_snapshots,
        price_panel=price_panel,
    )
    transaction_cost_rate = Decimal(str(strategy_config.costs.transaction_cost_bps)) / _BASIS_POINTS

    active_signal_id = holding_snapshots[0].strategy_signal_id
    cash, position_values = _allocate_target(Decimal("1"), holding_snapshots[0])
    points = [_to_point(holding_snapshots[0], cash, position_values, Decimal("0"))]

    for index, snapshot in enumerate(holding_snapshots[1:], start=1):
        previous_total = cash + sum(position_values.values(), Decimal("0"))
        position_values = _mark_to_market(
            position_values=position_values,
            previous_date=trading_dates[index - 1],
            current_date=snapshot.trade_date,
            prices_by_key=prices_by_key,
        )
        marked_total = cash + sum(position_values.values(), Decimal("0"))

        if snapshot.strategy_signal_id != active_signal_id:
            cash, position_values = _rebalance(
                total_assets=marked_total,
                position_values=position_values,
                snapshot=snapshot,
                transaction_cost_rate=transaction_cost_rate,
            )
            active_signal_id = snapshot.strategy_signal_id

        total_assets = cash + sum(position_values.values(), Decimal("0"))
        if previous_total <= 0 or total_assets <= 0:
            raise ValueError("Portfolio assets must remain positive")
        points.append(_to_point(snapshot, cash, position_values, total_assets / previous_total - 1))

    return points


def calculate_strategy_annualized_return(
    points: list[StrategyEquityCurvePoint],
) -> StrategyAnnualizedReturn:
    if len(points) < 2:
        return StrategyAnnualizedReturn(total_return=None, annualized_return=None)

    start = points[0]
    end = points[-1]
    elapsed_days = (end.trade_date - start.trade_date).days
    if elapsed_days <= 0 or start.net_value <= 0:
        return StrategyAnnualizedReturn(total_return=None, annualized_return=None)

    total_return = (end.net_value / start.net_value - Decimal("1")).quantize(_SIX_PLACES)
    annualization_power = Decimal("365") / Decimal(elapsed_days)
    annualized_return = (
        Decimal(str(float(end.net_value / start.net_value) ** float(annualization_power)))
        - Decimal("1")
    ).quantize(_SIX_PLACES)

    return StrategyAnnualizedReturn(
        total_return=total_return,
        annualized_return=annualized_return,
    )


def calculate_strategy_maximum_drawdown(
    points: list[StrategyEquityCurvePoint],
) -> StrategyMaximumDrawdown:
    if not points:
        return _zero_maximum_drawdown()

    peak = points[0]
    max_drawdown = Decimal("0.000000")
    peak_date: date | None = None
    trough_date: date | None = None

    for point in points:
        if point.net_value > peak.net_value:
            peak = point

        if peak.net_value <= 0:
            continue

        drawdown = (point.net_value / peak.net_value - Decimal("1")).quantize(_SIX_PLACES)
        if drawdown < max_drawdown:
            max_drawdown = drawdown
            peak_date = peak.trade_date
            trough_date = point.trade_date

    return StrategyMaximumDrawdown(
        max_drawdown=max_drawdown,
        peak_date=peak_date,
        trough_date=trough_date,
    )


def calculate_strategy_volatility(points: list[StrategyEquityCurvePoint]) -> StrategyVolatility:
    effective_returns = [point.daily_return for point in points[1:]]
    if len(effective_returns) < 2:
        return StrategyVolatility(volatility=None)

    mean_return = sum(effective_returns, Decimal("0")) / Decimal(len(effective_returns))
    variance = sum(
        ((daily_return - mean_return) * (daily_return - mean_return))
        for daily_return in effective_returns
    ) / Decimal(len(effective_returns))
    annualized_volatility = Decimal(str((float(variance) ** 0.5) * (252**0.5))).quantize(
        _SIX_PLACES
    )

    return StrategyVolatility(volatility=annualized_volatility)


def calculate_strategy_sharpe_ratio(
    points: list[StrategyEquityCurvePoint],
    *,
    risk_free_rate: Decimal,
) -> StrategySharpeRatio:
    # Effective observations exclude the initial placeholder return
    # (points[0].daily_return == 0.000000 is an initialization artifact).
    effective_returns = [point.daily_return for point in points[1:]]
    if len(effective_returns) < 2:
        return StrategySharpeRatio(sharpe_ratio=None)

    # Arithmetic daily risk-free rate, consistent with the 252 trading-day
    # convention used for volatility annualization.
    daily_risk_free_rate = risk_free_rate / Decimal("252")
    excess_returns = [daily_return - daily_risk_free_rate for daily_return in effective_returns]
    # Population standard deviation is zero iff all excess returns are equal.
    # Comparing the excess values directly (rather than the Decimal variance,
    # which can carry division rounding error from the mean) keeps this
    # boundary exact even when every effective daily return is identical.
    if all(excess == excess_returns[0] for excess in excess_returns):
        return StrategySharpeRatio(sharpe_ratio=None)

    mean_excess = sum(excess_returns, Decimal("0")) / Decimal(len(excess_returns))
    # Population variance: the backtest return sequence is the full realized
    # population being summarized, not a sample (matches volatility).
    variance = sum(
        (excess - mean_excess) * (excess - mean_excess) for excess in excess_returns
    ) / Decimal(len(excess_returns))

    sharpe_ratio = Decimal(
        str(float(mean_excess) / (float(variance) ** 0.5) * (252**0.5))
    ).quantize(_SIX_PLACES)
    return StrategySharpeRatio(sharpe_ratio=sharpe_ratio)


def _load_prices_by_key(
    session: Session,
    holding_snapshots: list[PortfolioHoldingSnapshot],
    *,
    price_panel: dict[int, list[MarketPrice]] | None = None,
) -> dict[_PriceKey, MarketPrice]:
    etf_ids = {holding.etf_id for snapshot in holding_snapshots for holding in snapshot.holdings}
    trade_dates = {snapshot.trade_date for snapshot in holding_snapshots}

    if not etf_ids or not trade_dates:
        return {}

    if price_panel is not None:
        return {
            (price.etf_id, price.trade_date): price
            for prices in price_panel.values()
            for price in prices
            if price.etf_id in etf_ids and price.trade_date in trade_dates
        }

    prices = session.scalars(
        select(MarketPrice)
        .where(MarketPrice.etf_id.in_(etf_ids))
        .where(MarketPrice.trade_date.in_(trade_dates))
    ).all()

    return {(price.etf_id, price.trade_date): price for price in prices}


def _allocate_target(
    total_assets: Decimal,
    snapshot: PortfolioHoldingSnapshot,
) -> tuple[Decimal, dict[int, Decimal]]:
    target_weights = _normalized_target_weights(snapshot)
    if not target_weights:
        return total_assets, {}
    return Decimal("0"), {
        etf_id: total_assets * weight for etf_id, weight in target_weights.items()
    }


def _normalized_target_weights(snapshot: PortfolioHoldingSnapshot) -> dict[int, Decimal]:
    weights = {holding.etf_id: holding.target_weight for holding in snapshot.holdings}
    total_weight = sum(weights.values(), Decimal("0"))
    if not weights:
        return {}
    if total_weight <= 0 or any(weight <= 0 for weight in weights.values()):
        raise ValueError("Portfolio target weights must be positive")
    return {etf_id: weight / total_weight for etf_id, weight in weights.items()}


def _mark_to_market(
    *,
    position_values: dict[int, Decimal],
    previous_date: date,
    current_date: date,
    prices_by_key: dict[_PriceKey, MarketPrice],
) -> dict[int, Decimal]:
    marked_values = dict(position_values)
    for etf_id, value in position_values.items():
        previous_row = prices_by_key.get((etf_id, previous_date))
        current_row = prices_by_key.get((etf_id, current_date))
        if previous_row is None or current_row is None:
            missing_dates = [
                trade_date.isoformat()
                for row, trade_date in ((previous_row, previous_date), (current_row, current_date))
                if row is None
            ]
            raise ValueError(
                f"Missing strategy price for held ETF {etf_id} on {', '.join(missing_dates)}"
            )
        previous_price, current_price = (
            price.price
            for price in forward_adjusted_prices(
                [previous_row, current_row],
                rebalance_date=current_date,
            )
        )
        marked_values[etf_id] = value * current_price / previous_price
    return marked_values


def _rebalance(
    *,
    total_assets: Decimal,
    position_values: dict[int, Decimal],
    snapshot: PortfolioHoldingSnapshot,
    transaction_cost_rate: Decimal,
) -> tuple[Decimal, dict[int, Decimal]]:
    if total_assets <= 0:
        raise ValueError("Portfolio assets must remain positive before rebalancing")
    target_weights = _normalized_target_weights(snapshot)
    actual_weights = {etf_id: value / total_assets for etf_id, value in position_values.items()}
    turnover = sum(
        (
            abs(target_weights.get(etf_id, Decimal("0")) - actual_weights.get(etf_id, Decimal("0")))
            for etf_id in target_weights.keys() | actual_weights.keys()
        ),
        Decimal("0"),
    )
    post_cost_assets = total_assets * (Decimal("1") - turnover * transaction_cost_rate)
    if post_cost_assets <= 0:
        raise ValueError("Transaction costs exhausted portfolio assets")
    return _allocate_target(post_cost_assets, snapshot)


def _to_point(
    snapshot: PortfolioHoldingSnapshot,
    cash: Decimal,
    position_values: dict[int, Decimal],
    daily_return: Decimal,
) -> StrategyEquityCurvePoint:
    total_assets = cash + sum(position_values.values(), Decimal("0"))
    if total_assets <= 0:
        raise ValueError("Portfolio assets must remain positive")
    target_weights = {holding.etf_id: holding.target_weight for holding in snapshot.holdings}
    total_output = total_assets.quantize(_SIX_PLACES)
    cash_output = cash.quantize(_SIX_PLACES)
    market_output = total_output - cash_output
    positions = tuple(
        StrategyPortfolioPosition(
            etf_id=etf_id,
            target_weight=target_weights[etf_id].quantize(_SIX_PLACES),
            actual_weight=(value / total_assets).quantize(_SIX_PLACES),
        )
        for etf_id, value in sorted(position_values.items())
    )
    return StrategyEquityCurvePoint(
        trade_date=snapshot.trade_date,
        net_value=total_output,
        daily_return=daily_return.quantize(_SIX_PLACES),
        portfolio_state=StrategyPortfolioState(
            cash=cash_output,
            market_value=market_output,
            total_assets=total_output,
            positions=positions,
        ),
    )


def _zero_maximum_drawdown() -> StrategyMaximumDrawdown:
    return StrategyMaximumDrawdown(
        max_drawdown=Decimal("0.000000"),
        peak_date=None,
        trough_date=None,
    )
