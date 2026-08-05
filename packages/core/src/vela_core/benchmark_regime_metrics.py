from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Context, Decimal

from vela_core.strategy_equity_curve import StrategyEquityCurvePoint

_SIX_PLACES = Decimal("0.000001")
_ANNUAL_SESSIONS = Decimal("252")
_CSI_300_KEY = "csi_300_buy_hold"
# Wide quantization context so extreme (exponential-notation) final values,
# e.g. huge annualized Alpha or a capture ratio near a tiny denominator,
# still quantize to six decimal places without raising InvalidOperation.
_QUANTIZE_CONTEXT = Context(prec=60)


def _quantize_six_places(value: Decimal) -> Decimal:
    return value.quantize(_SIX_PLACES, context=_QUANTIZE_CONTEXT)


@dataclass(frozen=True)
class BenchmarkRegimeMetrics:
    """Immutable CAPM proxy-regression and monthly capture comparison result."""

    benchmark_key: str
    capm_alpha: Decimal | None = None
    capm_beta: Decimal | None = None
    capm_r_squared: Decimal | None = None
    capm_observation_count: int | None = None
    up_capture_ratio: Decimal | None = None
    up_capture_observation_count: int | None = None
    down_capture_ratio: Decimal | None = None
    down_capture_observation_count: int | None = None


def calculate_benchmark_regime_metrics(
    strategy_points: Sequence[StrategyEquityCurvePoint],
    benchmark_points: Sequence[StrategyEquityCurvePoint],
    *,
    risk_free_rate: Decimal,
    benchmark_key: str,
) -> BenchmarkRegimeMetrics:
    """Calculate CAPM proxy-regression and monthly capture metrics.

    Excludes each curve's initial placeholder and requires the remaining
    ordered effective dates to match exactly. Never intersects, sorts,
    truncates, or fills either series. CAPM fields are populated only for
    the fixed ``csi_300_buy_hold`` benchmark; capture metrics are computed
    for every fixed benchmark.
    """
    strategy_effective = list(strategy_points[1:])
    benchmark_effective = list(benchmark_points[1:])
    strategy_dates = [point.trade_date for point in strategy_effective]
    benchmark_dates = [point.trade_date for point in benchmark_effective]
    if strategy_dates != benchmark_dates:
        raise ValueError("Strategy and benchmark effective dates must match exactly")

    capm_alpha, capm_beta, capm_r_squared, capm_count = _capm_metrics(
        strategy_effective,
        benchmark_effective,
        risk_free_rate=risk_free_rate,
        benchmark_key=benchmark_key,
    )
    up_ratio, up_count, down_ratio, down_count = _capture_metrics(
        strategy_effective,
        benchmark_effective,
    )
    return BenchmarkRegimeMetrics(
        benchmark_key=benchmark_key,
        capm_alpha=capm_alpha,
        capm_beta=capm_beta,
        capm_r_squared=capm_r_squared,
        capm_observation_count=capm_count,
        up_capture_ratio=up_ratio,
        up_capture_observation_count=up_count,
        down_capture_ratio=down_ratio,
        down_capture_observation_count=down_count,
    )


def _capm_metrics(
    strategy: Sequence[StrategyEquityCurvePoint],
    benchmark: Sequence[StrategyEquityCurvePoint],
    *,
    risk_free_rate: Decimal,
    benchmark_key: str,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, int | None]:
    if benchmark_key != _CSI_300_KEY:
        return None, None, None, None
    observation_count = len(strategy)
    if observation_count < 2:
        return None, None, None, observation_count

    daily_risk_free_rate = risk_free_rate / _ANNUAL_SESSIONS
    strategy_excess = [point.daily_return - daily_risk_free_rate for point in strategy]
    benchmark_excess = [point.daily_return - daily_risk_free_rate for point in benchmark]
    mean_strategy = sum(strategy_excess, Decimal("0")) / Decimal(observation_count)
    mean_benchmark = sum(benchmark_excess, Decimal("0")) / Decimal(observation_count)
    variance_strategy = sum((value - mean_strategy) ** 2 for value in strategy_excess) / Decimal(
        observation_count
    )
    variance_benchmark = sum((value - mean_benchmark) ** 2 for value in benchmark_excess) / Decimal(
        observation_count
    )
    covariance = sum(
        (strategy_value - mean_strategy) * (benchmark_value - mean_benchmark)
        for strategy_value, benchmark_value in zip(strategy_excess, benchmark_excess, strict=True)
    ) / Decimal(observation_count)
    if variance_benchmark == 0:
        return None, None, None, observation_count

    beta = covariance / variance_benchmark
    daily_alpha = mean_strategy - beta * mean_benchmark
    if daily_alpha <= Decimal("-1"):
        annualized_alpha: Decimal | None = None
    else:
        annualized_alpha = _quantize_six_places((Decimal("1") + daily_alpha) ** 252 - Decimal("1"))
    r_squared = (
        None
        if variance_strategy == 0
        else _quantize_six_places(covariance**2 / (variance_strategy * variance_benchmark))
    )
    return (
        annualized_alpha,
        _quantize_six_places(beta),
        r_squared,
        observation_count,
    )


def _capture_metrics(
    strategy: Sequence[StrategyEquityCurvePoint],
    benchmark: Sequence[StrategyEquityCurvePoint],
) -> tuple[Decimal | None, int, Decimal | None, int]:
    buckets: dict[tuple[int, int], tuple[list[Decimal], list[Decimal]]] = {}
    for strategy_point, benchmark_point in zip(strategy, benchmark, strict=True):
        key = (strategy_point.trade_date.year, strategy_point.trade_date.month)
        strategy_daily, benchmark_daily = buckets.setdefault(key, ([], []))
        strategy_daily.append(strategy_point.daily_return)
        benchmark_daily.append(benchmark_point.daily_return)

    up_strategy: list[Decimal] = []
    up_benchmark: list[Decimal] = []
    up_invalid_count = 0
    down_strategy: list[Decimal] = []
    down_benchmark: list[Decimal] = []
    down_invalid_count = 0
    for strategy_daily, benchmark_daily in buckets.values():
        strategy_monthly = _compound_monthly(strategy_daily)
        benchmark_monthly = _compound_monthly(benchmark_daily)
        valid = _bucket_is_valid(
            strategy_daily,
            benchmark_daily,
            strategy_monthly,
            benchmark_monthly,
        )
        if benchmark_monthly > 0:
            if valid:
                up_strategy.append(Decimal("1") + strategy_monthly)
                up_benchmark.append(Decimal("1") + benchmark_monthly)
            else:
                up_invalid_count += 1
        elif benchmark_monthly < 0:
            if valid:
                down_strategy.append(Decimal("1") + strategy_monthly)
                down_benchmark.append(Decimal("1") + benchmark_monthly)
            else:
                down_invalid_count += 1

    up_ratio = _regime_ratio(up_strategy, up_benchmark, invalid=up_invalid_count > 0)
    down_ratio = _regime_ratio(down_strategy, down_benchmark, invalid=down_invalid_count > 0)
    return (
        up_ratio,
        len(up_strategy) + up_invalid_count,
        down_ratio,
        len(down_strategy) + down_invalid_count,
    )


def _bucket_is_valid(
    strategy_daily: list[Decimal],
    benchmark_daily: list[Decimal],
    strategy_monthly: Decimal,
    benchmark_monthly: Decimal,
) -> bool:
    return (
        all(value > Decimal("-1") for value in strategy_daily)
        and all(value > Decimal("-1") for value in benchmark_daily)
        and strategy_monthly > Decimal("-1")
        and benchmark_monthly > Decimal("-1")
    )


def _compound_monthly(daily_returns: list[Decimal]) -> Decimal:
    product = Decimal("1")
    for daily_return in daily_returns:
        product *= Decimal("1") + daily_return
    return product - Decimal("1")


def _regime_ratio(
    strategy_compounded: list[Decimal],
    benchmark_compounded: list[Decimal],
    *,
    invalid: bool,
) -> Decimal | None:
    if invalid or not strategy_compounded:
        return None
    count = len(strategy_compounded)
    strategy_product = Decimal("1")
    benchmark_product = Decimal("1")
    for strategy_value, benchmark_value in zip(
        strategy_compounded, benchmark_compounded, strict=True
    ):
        strategy_product *= strategy_value
        benchmark_product *= benchmark_value
    root = Decimal("1") / Decimal(count)
    strategy_geometric_mean = strategy_product**root - Decimal("1")
    benchmark_geometric_mean = benchmark_product**root - Decimal("1")
    return _quantize_six_places(strategy_geometric_mean / benchmark_geometric_mean)
