from datetime import date
from decimal import Decimal

import pytest
from vela_core import (
    BenchmarkRegimeMetrics,
    StrategyEquityCurvePoint,
    calculate_benchmark_regime_metrics,
)

CSI_300 = "csi_300_buy_hold"
EQUAL_WEIGHT = "equal_weight_monthly"


def test_capm_proxy_regression_matches_independent_oracle() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05", "0.01", "0.03"], _dates(3)),
        _curve(["0.02", "0.00", "0.01"], _dates(3)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha == Decimal("11.274002")
    assert result.capm_beta == Decimal("2.000000")
    assert result.capm_r_squared == Decimal("1.000000")
    assert result.capm_observation_count == 3


def test_capm_alpha_is_252_session_compounded_with_daily_risk_free_rate() -> None:
    # risk_free_rate = 0.0252 -> daily risk-free 0.0001 shifts both excess series.
    # The unannualized daily alpha is 0.0101, and the 252D compounded value is
    # independently derived as 1.0101^252 - 1 (not alpha_daily * 252).
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05", "0.01", "0.03"], _dates(3)),
        _curve(["0.02", "0.00", "0.01"], _dates(3)),
        risk_free_rate=Decimal("0.0252"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha == Decimal("11.584081")
    assert result.capm_beta == Decimal("2.000000")
    assert result.capm_r_squared == Decimal("1.000000")
    assert result.capm_alpha != Decimal("0.0101") * Decimal("252")


def test_capm_r_squared_matches_independent_nonlinear_oracle() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05", "0.01", "0.01"], _dates(3)),
        _curve(["0.02", "0.00", "0.01"], _dates(3)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha == Decimal("1.313134")
    assert result.capm_beta == Decimal("2.000000")
    assert result.capm_r_squared == Decimal("0.750000")
    assert result.capm_observation_count == 3


def test_capm_public_values_are_quantized_to_six_places() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05", "0.01", "0.03"], _dates(3)),
        _curve(["0.02", "0.00", "0.01"], _dates(3)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha == result.capm_alpha.quantize(Decimal("0.000001"))
    assert result.capm_beta == result.capm_beta.quantize(Decimal("0.000001"))
    assert result.capm_r_squared == result.capm_r_squared.quantize(Decimal("0.000001"))


def test_capm_observation_count_matches_aligned_effective_dates() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05", "0.01", "0.03", "-0.02"], _dates(4)),
        _curve(["0.02", "0.00", "0.01", "0.00"], _dates(4)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_observation_count == 4


def test_up_and_down_capture_use_benchmark_defined_regimes() -> None:
    # Single-session calendar months: Jan up, Feb down, Mar zero, Apr up.
    # Zero-benchmark March contributes to neither regime.
    result = calculate_benchmark_regime_metrics(
        _curve(["0.02", "-0.01", "0.01", "0.06"], _monthly_dates()),
        _curve(["0.01", "-0.02", "0.00", "0.03"], _monthly_dates()),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result == BenchmarkRegimeMetrics(
        benchmark_key=CSI_300,
        capm_alpha=Decimal("25.417427"),
        capm_beta=Decimal("1.384615"),
        capm_r_squared=Decimal("0.958580"),
        capm_observation_count=4,
        up_capture_ratio=Decimal("1.995274"),
        up_capture_observation_count=2,
        down_capture_ratio=Decimal("0.500000"),
        down_capture_observation_count=1,
    )


def test_capture_compounds_daily_returns_into_calendar_month_buckets() -> None:
    # February has three sessions (compounds inside the month), March is a
    # partial edge month with two sessions, April has three down sessions.
    result = calculate_benchmark_regime_metrics(
        _curve(
            ["0.02", "0.02", "0.02", "0.01", "0.01", "0.00", "0.00", "0.00"],
            _compounding_dates(),
        ),
        _curve(
            ["0.01", "0.01", "0.01", "0.005", "0.005", "-0.02", "-0.02", "-0.02"],
            _compounding_dates(),
        ),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.up_capture_ratio == Decimal("2.011224")
    assert result.up_capture_observation_count == 2
    # Strategy returns nothing in the single down month, so the ratio is a
    # valid zero rather than a fabricated null.
    assert result.down_capture_ratio == Decimal("0.000000")
    assert result.down_capture_observation_count == 1


def test_capture_handles_both_fixed_benchmark_keys() -> None:
    equal_weight = calculate_benchmark_regime_metrics(
        _curve(["0.02", "-0.01", "0.01", "0.06"], _monthly_dates()),
        _curve(["0.01", "-0.02", "0.00", "0.03"], _monthly_dates()),
        risk_free_rate=Decimal("0"),
        benchmark_key=EQUAL_WEIGHT,
    )

    assert equal_weight.capm_alpha is None
    assert equal_weight.capm_beta is None
    assert equal_weight.capm_r_squared is None
    assert equal_weight.capm_observation_count is None
    assert equal_weight.up_capture_ratio == Decimal("1.995274")
    assert equal_weight.up_capture_observation_count == 2
    assert equal_weight.down_capture_ratio == Decimal("0.500000")
    assert equal_weight.down_capture_observation_count == 1


def test_capture_keeps_ratio_for_near_zero_non_zero_denominator() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["-0.0001", "0.01"], _two_month_dates()),
        _curve(["-0.0001", "0.02"], _two_month_dates()),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.down_capture_ratio == Decimal("1.000000")
    assert result.down_capture_observation_count == 1
    assert result.up_capture_ratio == Decimal("0.500000")
    assert result.up_capture_observation_count == 1


def test_capture_retains_decimal_precision_for_tiny_non_zero_denominator() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.00000000000000000002"], _dates(1)),
        _curve(["0.00000000000000000001"], _dates(1)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.up_capture_ratio == Decimal("2.000000")
    assert result.up_capture_observation_count == 1


def test_empty_regime_returns_null_ratio_with_explicit_count() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.02", "0.01"], _two_month_dates()),
        _curve(["0.01", "0.02"], _two_month_dates()),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.down_capture_ratio is None
    assert result.down_capture_observation_count == 0
    assert result.up_capture_observation_count == 2


@pytest.mark.parametrize(
    "benchmark_dates",
    [
        [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 4)],
        [date(2026, 1, 1), date(2026, 1, 4), date(2026, 1, 3)],
    ],
)
def test_regime_calculation_rejects_different_effective_date_identity(
    benchmark_dates: list[date],
) -> None:
    with pytest.raises(ValueError, match="effective dates"):
        calculate_benchmark_regime_metrics(
            _curve(["0.05", "0.01"], _dates(2)),
            _curve(["0.02", "0.00"], benchmark_dates),
            risk_free_rate=Decimal("0"),
            benchmark_key=CSI_300,
        )


def test_capm_requires_at_least_two_observations() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05"], _dates(1)),
        _curve(["0.02"], _dates(1)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha is None
    assert result.capm_beta is None
    assert result.capm_r_squared is None
    assert result.capm_observation_count == 1


def test_capm_zero_proxy_variance_returns_null_fit() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.05", "0.01"], _dates(2)),
        _curve(["0.02", "0.02"], _dates(2)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha is None
    assert result.capm_beta is None
    assert result.capm_r_squared is None
    assert result.capm_observation_count == 2


def test_capm_constant_strategy_keeps_beta_but_nulls_r_squared() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["0.01", "0.01"], _dates(2)),
        _curve(["0.02", "0.00"], _dates(2)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_beta == Decimal("0.000000")
    assert result.capm_r_squared is None
    assert result.capm_observation_count == 2


def test_capm_daily_alpha_at_or_below_minus_one_nulls_annualized_alpha() -> None:
    result = calculate_benchmark_regime_metrics(
        _curve(["-1.2", "-1.2"], _dates(2)),
        _curve(["0.00", "0.10"], _dates(2)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.capm_alpha is None
    assert result.capm_beta == Decimal("0.000000")
    assert result.capm_r_squared is None
    assert result.capm_observation_count == 2


def test_capture_invalid_selected_bucket_nulls_regime_ratio_with_count() -> None:
    # One valid up month and one up month whose strategy daily return is -1:
    # the whole up regime ratio is null while the selected-month count remains.
    result = calculate_benchmark_regime_metrics(
        _curve(["0.02", "-1.0"], _two_month_dates()),
        _curve(["0.01", "0.03"], _two_month_dates()),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.up_capture_ratio is None
    assert result.up_capture_observation_count == 2
    assert result.down_capture_observation_count == 0


def test_capture_invalid_monthly_return_nulls_down_regime() -> None:
    # Benchmark monthly return of -1.5 (from a single -1.5 daily return)
    # selects the down regime and then fails the validity boundary.
    result = calculate_benchmark_regime_metrics(
        _curve(["0.01", "0.01"], _dates(2)),
        _curve(["-1.5", "0.02"], _dates(2)),
        risk_free_rate=Decimal("0"),
        benchmark_key=CSI_300,
    )

    assert result.down_capture_ratio is None
    assert result.down_capture_observation_count == 1


def test_regime_calculation_public_export_shared_implementation() -> None:
    import vela_core.benchmark_regime_metrics as regime_module

    assert calculate_benchmark_regime_metrics is regime_module.calculate_benchmark_regime_metrics
    assert BenchmarkRegimeMetrics is regime_module.BenchmarkRegimeMetrics


def _curve(returns: list[str], dates: list[date]) -> list[StrategyEquityCurvePoint]:
    return [
        StrategyEquityCurvePoint(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000") if index == 0 else Decimal(value),
        )
        for index, (trade_date, value) in enumerate(zip(dates, ["0", *returns], strict=True))
    ]


def _dates(count: int) -> list[date]:
    return [date(2026, 1, index + 1) for index in range(count + 1)]


def _monthly_dates() -> list[date]:
    return [
        date(2026, 1, 2),
        date(2026, 1, 5),
        date(2026, 2, 5),
        date(2026, 3, 5),
        date(2026, 4, 5),
    ]


def _two_month_dates() -> list[date]:
    return [
        date(2026, 1, 2),
        date(2026, 1, 5),
        date(2026, 2, 5),
    ]


def _compounding_dates() -> list[date]:
    return [
        date(2026, 1, 30),
        date(2026, 2, 2),
        date(2026, 2, 3),
        date(2026, 2, 4),
        date(2026, 3, 2),
        date(2026, 3, 3),
        date(2026, 4, 6),
        date(2026, 4, 7),
        date(2026, 4, 8),
    ]
