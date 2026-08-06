# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, localcontext
from typing import Literal

from vela_core.errors import PersistedDataContractError

_SIX_PLACES = Decimal("0.000001")
ROLLING_WINDOW_SESSIONS = 63
_ANNUALIZATION_SESSIONS = 252
_ARITHMETIC_PRECISION = 40

RollingStatus = Literal["available", "insufficient_observations"]
SharpeStatus = Literal[
    "available",
    "insufficient_observations",
    "unavailable_missing_risk_free_rate",
]
CalendarGranularity = Literal["month", "year"]


@dataclass(frozen=True)
class ReturnStabilitySourcePoint:
    trade_date: date
    net_value: Decimal


@dataclass(frozen=True)
class RollingStabilityPoint:
    window_start_date: date
    trade_date: date
    total_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal | None


@dataclass(frozen=True)
class CalendarReturnBucket:
    period: str
    first_date: date
    last_date: date
    observation_count: int
    total_return: Decimal
    is_partial: bool


@dataclass(frozen=True)
class ReturnStabilityResult:
    window_sessions: int
    rolling_status: RollingStatus
    sharpe_status: SharpeStatus
    source_point_count: int
    effective_return_count: int
    rolling: tuple[RollingStabilityPoint, ...]
    monthly: tuple[CalendarReturnBucket, ...]
    yearly: tuple[CalendarReturnBucket, ...]


@dataclass(frozen=True)
class BacktestReturnStabilityBenchmark:
    key: str
    name: str
    result: ReturnStabilityResult


@dataclass(frozen=True)
class BacktestReturnStability:
    strategy: ReturnStabilityResult
    benchmarks: tuple[BacktestReturnStabilityBenchmark, ...]


def derive_return_stability(
    *,
    points: Sequence[ReturnStabilitySourcePoint],
    requested_start_date: date,
    requested_end_date: date,
    risk_free_rate: Decimal | None,
) -> ReturnStabilityResult:
    """Derive rolling and calendar-period stability from one persisted curve.

    The persisted six-decimal net-value curve is the read-time authority: effective
    returns are reconstructed from adjacent persisted values rather than recovered
    transient precision. Malformed evidence fails closed with
    ``PersistedDataContractError``; no sorting, deduplication, filling, or partial
    output is performed.
    """
    _validate_curve(points)
    count = len(points)
    if count < 2:
        effective_returns: dict[int, Decimal] = {}
        effective_count = 0
    else:
        effective_returns = {
            index: points[index].net_value / points[index - 1].net_value - Decimal("1")
            for index in range(1, count)
        }
        effective_count = count - 1

    rolling, rolling_status, sharpe_status = _derive_rolling(
        points,
        effective_returns,
        risk_free_rate=risk_free_rate,
    )

    monthly = _derive_calendar_buckets(
        points,
        effective_returns,
        requested_start_date=requested_start_date,
        requested_end_date=requested_end_date,
        granularity="month",
    )
    yearly = _derive_calendar_buckets(
        points,
        effective_returns,
        requested_start_date=requested_start_date,
        requested_end_date=requested_end_date,
        granularity="year",
    )

    return ReturnStabilityResult(
        window_sessions=ROLLING_WINDOW_SESSIONS,
        rolling_status=rolling_status,
        sharpe_status=sharpe_status,
        source_point_count=count,
        effective_return_count=effective_count,
        rolling=rolling,
        monthly=monthly,
        yearly=yearly,
    )


def _validate_curve(points: Sequence[ReturnStabilitySourcePoint]) -> None:
    previous_date: date | None = None
    for point in points:
        if point.net_value <= 0:
            raise PersistedDataContractError("return stability source net values must be positive")
        if previous_date is not None and point.trade_date <= previous_date:
            raise PersistedDataContractError(
                "return stability source dates must be unique and strictly increasing"
            )
        previous_date = point.trade_date


def _derive_rolling(
    points: Sequence[ReturnStabilitySourcePoint],
    effective_returns: dict[int, Decimal],
    *,
    risk_free_rate: Decimal | None,
) -> tuple[
    tuple[RollingStabilityPoint, ...],
    RollingStatus,
    SharpeStatus,
]:
    count = len(points)
    if count < ROLLING_WINDOW_SESSIONS + 1:
        return (
            (),
            "insufficient_observations",
            "insufficient_observations",
        )
    if risk_free_rate is None:
        sharpe_status: SharpeStatus = "unavailable_missing_risk_free_rate"
    else:
        sharpe_status = "available"

    daily_risk_free_rate = (
        None if risk_free_rate is None else risk_free_rate / Decimal(_ANNUALIZATION_SESSIONS)
    )

    with localcontext() as context:
        context.prec = _ARITHMETIC_PRECISION
        points_list = list(points)
        result: list[RollingStabilityPoint] = []
        for end_index in range(ROLLING_WINDOW_SESSIONS, count):
            start_index = end_index - ROLLING_WINDOW_SESSIONS
            window = [effective_returns[index] for index in range(start_index + 1, end_index + 1)]
            total_return = (
                points_list[end_index].net_value / points_list[start_index].net_value - Decimal("1")
            ).quantize(_SIX_PLACES)
            mean_return = sum(window, Decimal("0")) / Decimal(len(window))
            variance = sum(
                (daily_return - mean_return) * (daily_return - mean_return)
                for daily_return in window
            ) / Decimal(len(window))
            volatility = Decimal(
                str((float(variance) ** 0.5) * (_ANNUALIZATION_SESSIONS**0.5))
            ).quantize(_SIX_PLACES)

            sharpe_ratio = _rolling_sharpe(
                window,
                daily_risk_free_rate=daily_risk_free_rate,
            )
            result.append(
                RollingStabilityPoint(
                    window_start_date=points_list[start_index].trade_date,
                    trade_date=points_list[end_index].trade_date,
                    total_return=total_return,
                    volatility=volatility,
                    sharpe_ratio=sharpe_ratio,
                )
            )
        return tuple(result), "available", sharpe_status


def _rolling_sharpe(
    window: list[Decimal],
    *,
    daily_risk_free_rate: Decimal | None,
) -> Decimal | None:
    if daily_risk_free_rate is None:
        return None
    excess_returns = [daily_return - daily_risk_free_rate for daily_return in window]
    # Population standard deviation is zero iff all excess returns are equal;
    # comparing values directly keeps the boundary exact (matches the existing
    # summary Sharpe convention).
    if all(excess == excess_returns[0] for excess in excess_returns):
        return None
    mean_excess = sum(excess_returns, Decimal("0")) / Decimal(len(excess_returns))
    variance = sum(
        (excess - mean_excess) * (excess - mean_excess) for excess in excess_returns
    ) / Decimal(len(excess_returns))
    return Decimal(
        str(float(mean_excess) / (float(variance) ** 0.5) * (_ANNUALIZATION_SESSIONS**0.5))
    ).quantize(_SIX_PLACES)


def _derive_calendar_buckets(
    points: Sequence[ReturnStabilitySourcePoint],
    effective_returns: dict[int, Decimal],
    *,
    requested_start_date: date,
    requested_end_date: date,
    granularity: CalendarGranularity,
) -> tuple[CalendarReturnBucket, ...]:
    indexed_by_period: dict[str, list[int]] = {}
    for index, point in enumerate(points[1:], start=1):
        period = _period_key(point.trade_date, granularity)
        indexed_by_period.setdefault(period, []).append(index)

    buckets: list[CalendarReturnBucket] = []
    with localcontext() as context:
        context.prec = _ARITHMETIC_PRECISION
        for period, indexes in indexed_by_period.items():
            compound = Decimal("1")
            for index in indexes:
                compound *= Decimal("1") + effective_returns[index]
            first_index = indexes[0]
            last_index = indexes[-1]
            buckets.append(
                CalendarReturnBucket(
                    period=period,
                    first_date=points[first_index].trade_date,
                    last_date=points[last_index].trade_date,
                    observation_count=len(indexes),
                    total_return=(compound - Decimal("1")).quantize(_SIX_PLACES),
                    is_partial=_period_is_partial(
                        period,
                        granularity,
                        requested_start_date=requested_start_date,
                        requested_end_date=requested_end_date,
                    ),
                )
            )
    return tuple(buckets)


def _period_key(trade_date: date, granularity: CalendarGranularity) -> str:
    if granularity == "year":
        return str(trade_date.year)
    return f"{trade_date.year:04d}-{trade_date.month:02d}"


def _period_is_partial(
    period: str,
    granularity: CalendarGranularity,
    *,
    requested_start_date: date,
    requested_end_date: date,
) -> bool:
    first_calendar_date, last_calendar_date = _natural_period_bounds(period, granularity)
    return not (
        requested_start_date <= first_calendar_date and requested_end_date >= last_calendar_date
    )


def _natural_period_bounds(period: str, granularity: CalendarGranularity) -> tuple[date, date]:
    if granularity == "year":
        year = int(period)
        return date(year, 1, 1), date(year, 12, 31)
    year_text, month_text = period.split("-")
    year = int(year_text)
    month = int(month_text)
    first_calendar_date = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return first_calendar_date, next_month - timedelta(days=1)
