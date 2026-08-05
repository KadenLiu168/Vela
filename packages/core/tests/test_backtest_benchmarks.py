from datetime import date
from decimal import Decimal

import pytest
from vela_core.backtest_benchmarks import (
    calculate_backtest_benchmark_active_risk_metrics,
    calculate_backtest_benchmark_regime_metrics,
    calculate_backtest_benchmarks,
)
from vela_core.errors import BacktestDataError
from vela_core.models import ETFInfo, MarketPrice
from vela_core.strategy_equity_curve import StrategyEquityCurvePoint


def test_calculate_backtest_benchmarks_uses_adjusted_prices_and_monthly_rebalance_costs() -> None:
    dates = [date(2026, 1, 30), date(2026, 1, 31), date(2026, 2, 2)]
    universe = [_etf(1, "SSE", "510300"), _etf(2, "SSE", "510500")]
    results = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=universe,
        price_panel={
            1: [
                _price(1, dates[0], 100, 1),
                _price(1, dates[1], 110, 1),
                _price(1, dates[2], 121, 1),
            ],
            2: [
                _price(2, dates[0], 100, 1),
                _price(2, dates[1], 100, 1),
                _price(2, dates[2], 100, 1),
            ],
        },
        transaction_cost_bps=100,
        risk_free_rate=Decimal("0"),
    )

    equal, csi_300 = results

    assert equal.key == "equal_weight_monthly"
    assert [point.net_value for point in equal.points] == [
        Decimal("1.000000"),
        Decimal("1.049500"),
        Decimal("1.101975"),
    ]
    assert csi_300.key == "csi_300_buy_hold"
    assert [point.net_value for point in csi_300.points] == [
        Decimal("1.000000"),
        Decimal("1.100000"),
        Decimal("1.210000"),
    ]


def test_equal_weight_benchmark_uses_the_dated_universe_at_month_end() -> None:
    dates = [date(2026, 1, 30), date(2026, 2, 2), date(2026, 2, 27), date(2026, 3, 2)]
    csi = _etf(1, "SSE", "510300")
    later = _etf(2, "SSE", "510500")
    later.inception_date = date(2026, 2, 2)

    equal, _ = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=[csi, later],
        price_panel={
            1: [_price(1, trade_date, 100, 1) for trade_date in dates],
            2: [
                _price(2, dates[1], 100, 1),
                _price(2, dates[2], 100, 1),
                _price(2, dates[3], 110, 1),
            ],
        },
        transaction_cost_bps=0,
        risk_free_rate=Decimal("0"),
    )

    assert [point.net_value for point in equal.points] == [
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("1.000000"),
        Decimal("1.050000"),
    ]


def test_equal_weight_benchmark_does_not_rebalance_on_a_truncated_month() -> None:
    dates = [date(2026, 2, 2), date(2026, 2, 3)]
    universe = [_etf(1, "SSE", "510300"), _etf(2, "SSE", "510500")]

    equal, _ = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=universe,
        price_panel={
            1: [_price(1, dates[0], 100, 1), _price(1, dates[1], 110, 1)],
            2: [_price(2, dates[0], 100, 1), _price(2, dates[1], 100, 1)],
        },
        transaction_cost_bps=100,
        risk_free_rate=Decimal("0"),
        following_trading_date=date(2026, 2, 4),
    )

    assert equal.points[-1].net_value == Decimal("1.050000")


def test_benchmarks_use_forward_adjusted_price_ratios() -> None:
    dates = [date(2026, 2, 2), date(2026, 2, 3)]
    csi = _etf(1, "SSE", "510300")

    equal, csi_300 = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=[csi],
        price_panel={
            1: [
                _price(1, dates[0], 100, 1),
                _price(1, dates[1], 50, 2),
            ]
        },
        transaction_cost_bps=0,
        risk_free_rate=Decimal("0"),
        following_trading_date=date(2026, 2, 4),
    )

    assert equal.points[-1].net_value == Decimal("1.000000")
    assert csi_300.points[-1].net_value == Decimal("1.000000")


def test_benchmarks_reject_missing_csi_identity_and_required_price() -> None:
    trade_date = date(2026, 1, 2)

    with pytest.raises(BacktestDataError, match="exactly one active SSE:510300"):
        calculate_backtest_benchmarks(
            trading_dates=[trade_date],
            active_etfs=[_etf(2, "SSE", "510500")],
            price_panel={2: [_price(2, trade_date, 100, 1)]},
            transaction_cost_bps=0,
            risk_free_rate=Decimal("0"),
        )

    with pytest.raises(BacktestDataError, match=r"SSE:510300 on 2026-01-02"):
        calculate_backtest_benchmarks(
            trading_dates=[trade_date],
            active_etfs=[_etf(1, "SSE", "510300")],
            price_panel={},
            transaction_cost_bps=0,
            risk_free_rate=Decimal("0"),
        )


def test_equal_weight_benchmark_rejects_costs_that_exhaust_assets() -> None:
    dates = [date(2026, 1, 30), date(2026, 2, 2)]
    csi = _etf(1, "SSE", "510300")
    later = _etf(2, "SSE", "510500")
    later.inception_date = dates[1]

    with pytest.raises(ValueError, match="Transaction costs exhausted benchmark assets"):
        calculate_backtest_benchmarks(
            trading_dates=dates,
            active_etfs=[csi, later],
            price_panel={
                1: [_price(1, trade_date, 100, 1) for trade_date in dates],
                2: [_price(2, dates[1], 100, 1)],
            },
            transaction_cost_bps=20000,
            risk_free_rate=Decimal("0"),
            following_trading_date=date(2026, 3, 2),
        )


def test_benchmark_calculation_adds_shared_downside_and_duration_metrics() -> None:
    dates = [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)]
    results = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=[_etf(1, "SSE", "510300")],
        price_panel={1: [_price(1, trade_date, 100, 1) for trade_date in dates]},
        transaction_cost_bps=0,
        risk_free_rate=Decimal("0"),
    )

    assert all(result.sortino_ratio.sortino_ratio is None for result in results)
    assert all(result.calmar_ratio.calmar_ratio is None for result in results)
    assert all(
        result.longest_drawdown_duration.longest_drawdown_duration_sessions == 0
        for result in results
    )


def test_benchmark_calculation_uses_non_default_shared_metric_results() -> None:
    dates = [date(2026, 1, day) for day in range(2, 6)]
    prices = [100, 110, 99, 105]

    results = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=[_etf(1, "SSE", "510300")],
        price_panel={
            1: [
                _price(1, trade_date, close, 1)
                for trade_date, close in zip(dates, prices, strict=True)
            ]
        },
        transaction_cost_bps=0,
        risk_free_rate=Decimal("0"),
    )

    assert all(result.sortino_ratio.sortino_ratio is not None for result in results)
    assert all(result.calmar_ratio.calmar_ratio is not None for result in results)
    assert all(
        result.longest_drawdown_duration.longest_drawdown_duration_sessions == 2
        and result.longest_drawdown_duration.peak_date == dates[1]
        and result.longest_drawdown_duration.trough_date == dates[2]
        and result.longest_drawdown_duration.recovery_date is None
        for result in results
    )


def test_benchmark_active_metrics_are_added_after_strategy_curve_exists() -> None:
    dates = [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 5)]
    results = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=[_etf(1, "SSE", "510300")],
        price_panel={1: [_price(1, trade_date, 100, 1) for trade_date in dates]},
        transaction_cost_bps=0,
        risk_free_rate=Decimal("0"),
    )
    strategy_points = [
        StrategyEquityCurvePoint(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            daily_return=Decimal(daily_return),
        )
        for trade_date, daily_return in zip(
            dates,
            ["0.000000", "0.002000", "-0.001000", "0.005000"],
            strict=True,
        )
    ]

    updated = [
        calculate_backtest_benchmark_active_risk_metrics(strategy_points, result)
        for result in results
    ]

    assert all(result.tracking_error == Decimal("0.038884") for result in updated)
    assert all(result.information_ratio == Decimal("12.961481") for result in updated)
    assert [result.points for result in updated] == [result.points for result in results]


def test_benchmark_regime_metrics_keep_ownership_and_preserve_existing_fields() -> None:
    dates = [
        date(2026, 1, 5),
        date(2026, 2, 5),
        date(2026, 3, 5),
        date(2026, 4, 5),
    ]
    results = calculate_backtest_benchmarks(
        trading_dates=dates,
        active_etfs=[_etf(1, "SSE", "510300")],
        price_panel={
            1: [
                _price(1, dates[0], 100, 1),
                _price(1, dates[1], 102, 1),
                _price(1, dates[2], 101, 1),
                _price(1, dates[3], 105, 1),
            ]
        },
        transaction_cost_bps=0,
        risk_free_rate=Decimal("0"),
    )
    strategy_points = [
        StrategyEquityCurvePoint(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            daily_return=Decimal(daily_return),
        )
        for trade_date, daily_return in zip(
            dates,
            ["0.000000", "0.020000", "-0.010000", "0.010000"],
            strict=True,
        )
    ]
    active_updated = [
        calculate_backtest_benchmark_active_risk_metrics(strategy_points, result)
        for result in results
    ]
    updated = [
        calculate_backtest_benchmark_regime_metrics(
            strategy_points,
            result,
            risk_free_rate=Decimal("0"),
        )
        for result in active_updated
    ]

    equal_weight, csi_300 = updated
    assert equal_weight.key == "equal_weight_monthly"
    assert equal_weight.capm_alpha is None
    assert equal_weight.capm_beta is None
    assert equal_weight.capm_r_squared is None
    assert equal_weight.capm_observation_count is None
    assert equal_weight.up_capture_ratio is not None
    assert equal_weight.down_capture_ratio is not None
    assert csi_300.key == "csi_300_buy_hold"
    assert csi_300.capm_alpha is not None
    assert csi_300.capm_beta is not None
    assert csi_300.capm_r_squared is not None
    assert csi_300.capm_observation_count == 3
    assert csi_300.up_capture_ratio is not None
    assert csi_300.down_capture_ratio is not None
    # Existing active-risk and shared metrics remain unchanged.
    assert all(result.tracking_error is not None for result in updated)
    assert all(result.information_ratio is not None for result in updated)
    assert [result.points for result in updated] == [result.points for result in results]
    assert [result.annualized_return for result in updated] == [
        result.annualized_return for result in results
    ]


def _etf(identifier: int, exchange: str, symbol: str) -> ETFInfo:
    return ETFInfo(id=identifier, exchange=exchange, symbol=symbol, name=symbol, is_active=True)


def _price(etf_id: int, trade_date: date, close: int, factor: int) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        close_price=Decimal(close),
        factor_hfq=Decimal(factor),
    )
