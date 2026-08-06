# ruff: noqa: E501

import math
from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from decimal import Decimal

import pytest
from vela_core.strategy_equity_curve import StrategyEquityCurvePoint
from vela_core.tail_distribution_risk_metrics import (
    MINIMUM_PUBLICATION_OBSERVATIONS,
    TAIL_DISTRIBUTION_METRIC_VERSION,
    calculate_tail_distribution_risk_metrics,
)

_SIX = Decimal("0.000001")


def _curve(values: list[Decimal]) -> tuple[StrategyEquityCurvePoint, ...]:
    """Build a curve from daily returns; the first point is the zero-return placeholder."""
    start = date(2026, 1, 1)
    placeholder = StrategyEquityCurvePoint(start, Decimal("1.000000"), Decimal("0"))
    return (placeholder,) + tuple(
        StrategyEquityCurvePoint(
            start + timedelta(days=index + 1),
            Decimal("1.000000"),
            value,
        )
        for index, value in enumerate(values)
    )


def _return(value: str) -> Decimal:
    return Decimal(value)


def _returns(count: int, value: str = "0.005") -> list[Decimal]:
    return [_return(value) for _ in range(count)]


def _controlled_100_returns() -> list[Decimal]:
    """Five independently known worst observations plus 95 mild gains."""
    return [_return(value) for value in ("-0.10", "-0.08", "-0.06", "-0.04", "-0.02")] + _returns(
        95
    )


def _var_cvar_oracle(returns: list[Decimal]) -> tuple[Decimal, Decimal]:
    """Independent nearest-rank positive-loss Historical VaR/CVaR oracle.

    Sorts unquantized returns ascending, takes ``ceil(0.05 * n)`` as the fixed
    tail cardinality, and publishes positive loss magnitudes quantized to six
    places. Implemented with its own arithmetic so it never calls the module.
    """
    sorted_returns = sorted(returns)
    tail_count = math.ceil(0.05 * len(sorted_returns))
    cutoff = sorted_returns[tail_count - 1]
    tail = sorted_returns[:tail_count]
    var = max(Decimal("0"), -cutoff)
    cvar = max(Decimal("0"), -sum(tail, Decimal("0")) / Decimal(len(tail)))
    return var.quantize(_SIX), cvar.quantize(_SIX)


def _shape_oracle(returns: list[Decimal]) -> tuple[Decimal, Decimal]:
    """Independent bias-corrected Fisher-Pearson skewness / excess kurtosis oracle."""
    n = len(returns)
    n_dec = Decimal(n)
    mean = sum(returns, Decimal("0")) / n_dec
    m2 = sum((value - mean) ** 2 for value in returns) / n_dec
    if m2 == 0:
        raise AssertionError("shape oracle requires non-zero second central moment")
    m3 = sum((value - mean) ** 3 for value in returns) / n_dec
    m4 = sum((value - mean) ** 4 for value in returns) / n_dec
    g1 = Decimal(str(math.sqrt(n * (n - 1)))) / (n_dec - 2) * m3 / (m2 ** Decimal("1.5"))
    g2 = (n_dec - 1) / ((n_dec - 2) * (n_dec - 3)) * ((n_dec + 1) * (m4 / m2**2 - 3) + 6)
    return g1.quantize(_SIX), g2.quantize(_SIX)


# --- 1.2 observation boundary and tail-cardinality publication contract ---


def test_ninety_nine_observations_are_insufficient() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(99)))
    assert result.observation_count == 99
    assert result.tail_observation_count == 5
    assert result.evidence_status == "insufficient_evidence"
    assert result.historical_var_95 is None
    assert result.historical_cvar_95 is None
    assert result.return_skewness is None
    assert result.return_excess_kurtosis is None


def test_one_hundred_observations_are_sufficient() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_controlled_100_returns()))
    assert result.observation_count == 100
    assert result.tail_observation_count == 5
    assert result.evidence_status == "sufficient"
    assert result.historical_var_95 is not None
    assert result.historical_cvar_95 is not None


@pytest.mark.parametrize(
    ("observation_count", "expected_tail_count"),
    [(0, 0), (1, 1), (20, 1), (21, 2), (99, 5), (100, 5), (101, 6)],
)
def test_tail_count_is_ceiling_of_five_percent(
    observation_count: int, expected_tail_count: int
) -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(observation_count)))
    assert result.observation_count == observation_count
    assert result.tail_observation_count == expected_tail_count


def test_publication_threshold_is_independent_of_walk_forward_threshold() -> None:
    """A few observations remain insufficient even though they meet the
    three-window Walk-forward aggregation sufficiency rule."""
    assert MINIMUM_PUBLICATION_OBSERVATIONS != 3
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(5)))
    assert result.evidence_status == "insufficient_evidence"
    assert result.tail_observation_count == 1
    assert result.historical_var_95 is None


# --- 1.3 Historical VaR/CVaR independent oracle and invariants ---


def test_var_cvar_matches_independent_oracle_on_controlled_tail() -> None:
    returns = _controlled_100_returns()
    expected_var, expected_cvar = _var_cvar_oracle(returns)
    # The five worst returns are -0.10..-0.02; the nearest-rank cutoff is the
    # fifth-worst (-0.02) and CVaR is the mean loss of exactly those five.
    assert expected_var == Decimal("0.020000")
    assert expected_cvar == Decimal("0.060000")
    result = calculate_tail_distribution_risk_metrics(_curve(returns))
    assert result.historical_var_95 == expected_var
    assert result.historical_cvar_95 == expected_cvar


def test_var_cvar_values_are_quantized_to_six_places() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_controlled_100_returns()))
    assert result.historical_var_95 is not None
    assert result.historical_cvar_95 is not None
    for value in (result.historical_var_95, result.historical_cvar_95):
        assert value == value.quantize(_SIX)
        assert value.as_tuple().exponent == -6


@pytest.mark.parametrize("tail_value", ["-0.30", "-0.17", "-0.04", "-0.001"])
def test_cvar_is_at_least_var_and_var_is_non_negative(tail_value: str) -> None:
    returns = [_return(tail_value)] + _returns(99, value="0.003")
    result = calculate_tail_distribution_risk_metrics(_curve(returns))
    assert result.evidence_status == "sufficient"
    assert result.historical_cvar_95 is not None
    assert result.historical_var_95 is not None
    assert result.historical_cvar_95 >= result.historical_var_95 >= Decimal("0")


def test_all_non_negative_returns_publish_zero_loss() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(100, value="0.001")))
    assert result.evidence_status == "sufficient"
    assert result.historical_var_95 == Decimal("0.000000")
    assert result.historical_cvar_95 == Decimal("0.000000")


def test_all_zero_returns_publish_zero_loss() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(100, value="0")))
    assert result.evidence_status == "sufficient"
    assert result.historical_var_95 == Decimal("0.000000")
    assert result.historical_cvar_95 == Decimal("0.000000")


# --- 1.4 bias-corrected Fisher shape statistics and boundaries ---


def test_skewness_and_kurtosis_match_independent_oracle() -> None:
    returns = [
        _return(value)
        for value in (
            "-0.05",
            "-0.04",
            "-0.03",
            "-0.02",
            "-0.01",
            "0.00",
            "0.01",
            "0.02",
            "0.04",
            "0.09",
        )
    ] * 10
    expected_g1, expected_g2 = _shape_oracle(returns)
    result = calculate_tail_distribution_risk_metrics(_curve(returns))
    assert result.return_skewness == expected_g1
    assert result.return_excess_kurtosis == expected_g2


def test_skewness_kurtosis_are_quantized_to_six_places() -> None:
    returns = [
        _return(value)
        for value in (
            "-0.05",
            "-0.04",
            "-0.03",
            "-0.02",
            "-0.01",
            "0.00",
            "0.01",
            "0.02",
            "0.04",
            "0.09",
        )
    ] * 10
    result = calculate_tail_distribution_risk_metrics(_curve(returns))
    assert result.return_skewness is not None
    assert result.return_excess_kurtosis is not None
    for value in (result.return_skewness, result.return_excess_kurtosis):
        assert value == value.quantize(_SIX)


def test_constant_sufficient_distribution_has_null_shape() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(100, value="0.01")))
    assert result.evidence_status == "sufficient"
    assert result.return_skewness is None
    assert result.return_excess_kurtosis is None
    # VaR/CVaR remain governed by their own positive-loss rules.
    assert result.historical_var_95 == Decimal("0.000000")
    assert result.historical_cvar_95 == Decimal("0.000000")


def test_constant_negative_distribution_keeps_loss_metrics() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(100, value="-0.01")))
    assert result.evidence_status == "sufficient"
    assert result.return_skewness is None
    assert result.return_excess_kurtosis is None
    assert result.historical_var_95 == Decimal("0.010000")
    assert result.historical_cvar_95 == Decimal("0.010000")


# --- 1.5 immutable public contract ---


def test_result_is_immutable() -> None:
    result = calculate_tail_distribution_risk_metrics(_curve(_returns(100)))
    with pytest.raises(FrozenInstanceError):
        result.observation_count = 1  # type: ignore[misc]


def test_metric_version_is_locked() -> None:
    assert TAIL_DISTRIBUTION_METRIC_VERSION == "tail_distribution_metrics_v1"


def test_public_function_accepts_execution_curve_points() -> None:
    points = _curve(_controlled_100_returns())
    result = calculate_tail_distribution_risk_metrics(points)
    assert result.observation_count == 100
    assert result.evidence_status == "sufficient"
