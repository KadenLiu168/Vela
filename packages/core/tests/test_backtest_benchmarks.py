from datetime import date
from decimal import Decimal

import pytest
from vela_core.backtest_benchmarks import calculate_backtest_benchmarks
from vela_core.errors import BacktestDataError
from vela_core.models import ETFInfo, MarketPrice


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


def _etf(identifier: int, exchange: str, symbol: str) -> ETFInfo:
    return ETFInfo(id=identifier, exchange=exchange, symbol=symbol, name=symbol, is_active=True)


def _price(etf_id: int, trade_date: date, close: int, factor: int) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        close_price=Decimal(close),
        factor_hfq=Decimal(factor),
    )
