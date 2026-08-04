from datetime import date
from decimal import Decimal

import pytest
import vela_core.strategy_equity_curve as equity_curve_module
from vela_core import (
    ActiveRiskMetrics,
    StrategyCalmarRatio,
    StrategyEquityCurvePoint,
    StrategyLongestDrawdownDuration,
    StrategySortinoRatio,
    calculate_active_risk_metrics,
    calculate_strategy_calmar_ratio,
    calculate_strategy_longest_drawdown_duration,
    calculate_strategy_sortino_ratio,
)


def test_sortino_uses_daily_mar_and_all_effective_observations() -> None:
    result = calculate_strategy_sortino_ratio(
        _points(["0.0101", "-0.0049", "0.0201"]),
        risk_free_rate=Decimal("0.0252"),
    )

    assert result == StrategySortinoRatio(sortino_ratio=Decimal("45.825757"))


@pytest.mark.parametrize(
    ("returns", "expected"),
    [
        (["-0.0100", "0.0000"], Decimal("-11.224972")),
        (["0.0100"], None),
        (["0.0001", "0.0002"], None),
    ],
)
def test_sortino_returns_null_for_unsupported_downside_cases(
    returns: list[str], expected: Decimal | None
) -> None:
    result = calculate_strategy_sortino_ratio(
        _points(returns),
        risk_free_rate=Decimal("0"),
    )

    assert result == StrategySortinoRatio(sortino_ratio=expected)


def test_calmar_uses_published_cagr_and_absolute_maximum_drawdown() -> None:
    assert calculate_strategy_calmar_ratio(Decimal("0.12"), Decimal("-0.08")) == (
        StrategyCalmarRatio(calmar_ratio=Decimal("1.500000"))
    )
    assert calculate_strategy_calmar_ratio(Decimal("-0.12"), Decimal("-0.08")) == (
        StrategyCalmarRatio(calmar_ratio=Decimal("-1.500000"))
    )
    assert calculate_strategy_calmar_ratio(None, Decimal("-0.08")) == StrategyCalmarRatio(
        calmar_ratio=None
    )
    assert calculate_strategy_calmar_ratio(Decimal("0.12"), Decimal("0")) == (
        StrategyCalmarRatio(calmar_ratio=None)
    )


def test_longest_drawdown_duration_counts_official_session_intervals() -> None:
    result = calculate_strategy_longest_drawdown_duration(
        _curve(["1.0", "1.2", "0.9", "1.2", "1.2"])
    )

    assert result == StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=2,
        peak_date=date(2026, 1, 2),
        trough_date=date(2026, 1, 3),
        recovery_date=date(2026, 1, 4),
    )


def test_longest_drawdown_duration_keeps_ongoing_recovery_null() -> None:
    result = calculate_strategy_longest_drawdown_duration(_curve(["1.0", "1.1", "0.8", "0.9"]))

    assert result == StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=2,
        peak_date=date(2026, 1, 2),
        trough_date=date(2026, 1, 3),
        recovery_date=None,
    )


def test_longest_drawdown_duration_uses_last_equal_high_and_earliest_ties() -> None:
    result = calculate_strategy_longest_drawdown_duration(_curve(["1.0", "1.0", "0.9", "1.0"]))

    assert result == StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=2,
        peak_date=date(2026, 1, 2),
        trough_date=date(2026, 1, 3),
        recovery_date=date(2026, 1, 4),
    )


def test_longest_drawdown_duration_anchors_following_interval_at_equal_recovery() -> None:
    result = calculate_strategy_longest_drawdown_duration(
        _curve(["1.0", "1.2", "0.9", "1.2", "1.0", "1.2"])
    )

    assert result == StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=2,
        peak_date=date(2026, 1, 2),
        trough_date=date(2026, 1, 3),
        recovery_date=date(2026, 1, 4),
    )


def test_longest_drawdown_duration_keeps_earliest_deepest_trough_on_a_tie() -> None:
    result = calculate_strategy_longest_drawdown_duration(_curve(["1.0", "0.8", "0.8", "1.0"]))

    assert result == StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=3,
        peak_date=date(2026, 1, 1),
        trough_date=date(2026, 1, 2),
        recovery_date=date(2026, 1, 4),
    )


def test_longest_drawdown_duration_keeps_earliest_interval_on_a_duration_tie() -> None:
    result = calculate_strategy_longest_drawdown_duration(
        _curve(["1.0", "0.9", "1.0", "0.8", "1.0"])
    )

    assert result == StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=2,
        peak_date=date(2026, 1, 1),
        trough_date=date(2026, 1, 2),
        recovery_date=date(2026, 1, 3),
    )


def test_longest_drawdown_duration_returns_zero_for_never_underwater_curve() -> None:
    assert calculate_strategy_longest_drawdown_duration(_curve(["1.0", "1.1", "1.2"])) == (
        StrategyLongestDrawdownDuration(
            longest_drawdown_duration_sessions=0,
            peak_date=None,
            trough_date=None,
            recovery_date=None,
        )
    )


def test_active_risk_metrics_use_unquantized_tracking_error_for_information_ratio() -> None:
    result = calculate_active_risk_metrics(
        _points(["0.002", "0.009", "0.005"]),
        _points(["0.000", "0.010", "0.000"]),
    )

    assert result == ActiveRiskMetrics(
        tracking_error=Decimal("0.038884"),
        information_ratio=Decimal("12.961481"),
    )
    assert result.information_ratio != Decimal("12.961629")


@pytest.mark.parametrize(
    "strategy_returns,benchmark_returns,expected",
    [
        (["0.001", "0.001"], ["0.000", "0.000"], ActiveRiskMetrics(Decimal("0.000000"), None)),
        (["0.00000001", "-0.00000001"], ["0", "0"], ActiveRiskMetrics(Decimal("0.000000"), None)),
        (["0.001"], ["0.000"], ActiveRiskMetrics(None, None)),
    ],
)
def test_active_risk_metrics_handles_zero_and_insufficient_dispersion(
    strategy_returns: list[str],
    benchmark_returns: list[str],
    expected: ActiveRiskMetrics,
) -> None:
    assert (
        calculate_active_risk_metrics(_points(strategy_returns), _points(benchmark_returns))
        == expected
    )


@pytest.mark.parametrize(
    "benchmark_dates",
    [[date(2026, 1, 2), date(2026, 1, 3)], [date(2026, 1, 3), date(2026, 1, 2)]],
)
def test_active_risk_metrics_rejects_different_effective_date_identity(
    benchmark_dates: list[date],
) -> None:
    with pytest.raises(ValueError, match="effective dates"):
        calculate_active_risk_metrics(
            _points(["0.002", "0.009"]),
            _points(["0.000", "0.010"], dates=benchmark_dates),
        )


def test_expanded_metric_public_exports_share_the_core_implementations() -> None:
    assert calculate_strategy_sortino_ratio is equity_curve_module.calculate_strategy_sortino_ratio
    assert calculate_strategy_calmar_ratio is equity_curve_module.calculate_strategy_calmar_ratio
    assert (
        calculate_strategy_longest_drawdown_duration
        is equity_curve_module.calculate_strategy_longest_drawdown_duration
    )
    assert calculate_active_risk_metrics is equity_curve_module.calculate_active_risk_metrics


def _points(returns: list[str], dates: list[date] | None = None) -> list[StrategyEquityCurvePoint]:
    dates = dates or [date(2026, 1, index) for index in range(1, len(returns) + 2)]
    return [
        StrategyEquityCurvePoint(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000") if index == 0 else Decimal(value),
        )
        for index, trade_date in enumerate(dates)
        for value in (["0"] if index == 0 else [returns[index - 1]])
    ]


def _curve(net_values: list[str]) -> list[StrategyEquityCurvePoint]:
    points = []
    for index, net_value in enumerate(net_values, start=1):
        points.append(
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, index),
                net_value=Decimal(net_value),
                daily_return=Decimal("0.000000"),
            )
        )
    return points
