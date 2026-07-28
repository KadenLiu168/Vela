from datetime import UTC, date, datetime
from decimal import Decimal
from math import sqrt

import pytest
import vela_core.strategy_equity_curve as equity_curve_module
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    StrategyAnnualizedReturn,
    StrategyEquityCurvePoint,
    StrategyMaximumDrawdown,
    StrategySharpeRatio,
    StrategySignalPositionInput,
    StrategyVolatility,
    calculate_strategy_annualized_return,
    calculate_strategy_equity_curve,
    calculate_strategy_maximum_drawdown,
    calculate_strategy_sharpe_ratio,
    calculate_strategy_volatility,
    persist_strategy_signal,
)
from vela_core.models import Base, ETFInfo, MarketPrice
from vela_core.strategy_config import StrategyConfig, validate_strategy_config


def test_calculate_strategy_equity_curve_returns_empty_for_empty_dates() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[],
            strategy_config=_strategy_config(),
        )

    assert points == []


def test_calculate_strategy_equity_curve_sets_initial_net_value() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23)],
            strategy_config=_strategy_config(),
        )

    assert points == [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 6, 23),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        )
    ]


def test_calculate_strategy_equity_curve_applies_weighted_daily_return() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.600000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.400000")),
            ],
        )
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=200)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=180)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(),
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.020000"),
    ]
    assert points[1].daily_return == Decimal("0.020000")


def test_calculate_strategy_equity_curve_carries_drifted_values_until_next_rebalance() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.5")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.5")),
            ],
        )
        for trade_date, spy_price, qqq_price in [
            (date(2026, 6, 23), 100, 100),
            (date(2026, 6, 24), 200, 100),
            (date(2026, 6, 25), 400, 100),
        ]:
            _add_price(session, etf_id=spy.id, trade_date=trade_date, close_price=spy_price)
            _add_price(session, etf_id=qqq.id, trade_date=trade_date, close_price=qqq_price)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24), date(2026, 6, 25)],
            strategy_config=_strategy_config(),
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.500000"),
        Decimal("2.500000"),
    ]
    assert points[1].portfolio_state is not None
    assert points[1].portfolio_state.positions[0].actual_weight == Decimal("0.666667")


def test_calculate_strategy_equity_curve_single_asset_matches_direct_compounding() -> None:
    session_factory = _create_session_factory()
    trading_dates = [
        date(2026, 6, 23),
        date(2026, 6, 24),
        date(2026, 6, 25),
        date(2026, 6, 26),
    ]

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        for trade_date, close_price in zip(
            trading_dates,
            [Decimal("100"), Decimal("120"), Decimal("90"), Decimal("135")],
            strict=True,
        ):
            _add_price(
                session,
                etf_id=spy.id,
                trade_date=trade_date,
                close_price=close_price,
            )
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=trading_dates,
            strategy_config=_strategy_config(),
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.200000"),
        Decimal("0.900000"),
        Decimal("1.350000"),
    ]
    assert all(
        point.portfolio_state is not None
        and point.portfolio_state.positions[0].actual_weight == Decimal("1.000000")
        for point in points
    )


def test_calculate_strategy_equity_curve_keeps_unquantized_state_between_outputs() -> None:
    session_factory = _create_session_factory()
    trading_dates = [
        date(2026, 7, 1),
        date(2026, 7, 2),
        date(2026, 7, 3),
        date(2026, 7, 6),
        date(2026, 7, 7),
        date(2026, 7, 8),
        date(2026, 7, 9),
        date(2026, 7, 10),
        date(2026, 7, 13),
    ]
    spy_prices = [100, 114, 103, 106, 95, 81, 74, 88, 82]
    qqq_prices = [100, 89, 75, 91, 100, 85, 92, 78, 62]

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(
            session,
            signal_date=date(2026, 6, 30),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.5")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.5")),
            ],
        )
        for trade_date, spy_price, qqq_price in zip(
            trading_dates,
            spy_prices,
            qqq_prices,
            strict=True,
        ):
            _add_price(
                session,
                etf_id=spy.id,
                trade_date=trade_date,
                close_price=spy_price,
            )
            _add_price(
                session,
                etf_id=qqq.id,
                trade_date=trade_date,
                close_price=qqq_price,
            )
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=trading_dates,
            strategy_config=_strategy_config(),
        )

    # Exact value carry telescopes to 0.5 * 82/100 + 0.5 * 62/100 = 0.720000.
    # Reconstructing positions from each six-place point instead yields 0.719999.
    assert points[-1].net_value == Decimal("0.720000")
    assert points[-1].net_value != Decimal("0.719999")


def test_calculate_strategy_equity_curve_recenters_same_targets_for_new_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        positions = [
            StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.5")),
            StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.5")),
        ]
        _add_signal(session, signal_date=date(2026, 6, 22), positions=positions)
        _add_signal(session, signal_date=date(2026, 6, 23), positions=positions)
        for trade_date, spy_price, qqq_price in [
            (date(2026, 6, 23), 100, 100),
            (date(2026, 6, 24), 200, 100),
        ]:
            _add_price(session, etf_id=spy.id, trade_date=trade_date, close_price=spy_price)
            _add_price(session, etf_id=qqq.id, trade_date=trade_date, close_price=qqq_price)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=100),
        )

    assert points[1].net_value == Decimal("1.495000")
    assert points[1].daily_return == Decimal("0.495000")
    assert points[1].portfolio_state is not None
    assert [position.actual_weight for position in points[1].portfolio_state.positions] == [
        Decimal("0.500000"),
        Decimal("0.500000"),
    ]


def test_calculate_strategy_equity_curve_normalizes_repeating_targets_without_cash() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etfs = [_add_etf(session, symbol=symbol) for symbol in ["AAA", "BBB", "CCC"]]
        third = Decimal("1") / Decimal("3")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[
                StrategySignalPositionInput(etf_id=etf.id, target_weight=third) for etf in etfs
            ],
        )
        for etf in etfs:
            _add_price(session, etf_id=etf.id, trade_date=date(2026, 6, 23), close_price=100)
        session.commit()

        point = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23)],
            strategy_config=_strategy_config(),
        )[0]

    assert point.portfolio_state is not None
    assert point.portfolio_state.cash == Decimal("0.000000")
    assert sum(position.actual_weight for position in point.portfolio_state.positions) == Decimal(
        "0.999999"
    )


def test_calculate_strategy_equity_curve_rejects_non_positive_targets_and_exhausted_costs() -> None:
    session_factory = _create_session_factory()

    exhausting_session_factory = _create_session_factory()
    with exhausting_session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0"))],
        )
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        session.commit()

        with pytest.raises(ValueError, match="target weights must be positive"):
            calculate_strategy_equity_curve(
                session,
                trading_dates=[date(2026, 6, 23)],
                strategy_config=_strategy_config(),
            )

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=100)
        session.commit()

        with pytest.raises(ValueError, match="exhausted portfolio assets"):
            calculate_strategy_equity_curve(
                session,
                trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
                strategy_config=_strategy_config(transaction_cost_bps=10000),
            )


def test_calculate_strategy_equity_curve_uses_supplied_price_panel() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=999)
        session.commit()

        price_panel = {
            spy.id: [
                _market_price(
                    etf_id=spy.id,
                    trade_date=date(2026, 6, 23),
                    close_price=Decimal("100"),
                ),
                _market_price(
                    etf_id=spy.id,
                    trade_date=date(2026, 6, 24),
                    close_price=Decimal("110"),
                ),
            ]
        }
        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(),
            price_panel=price_panel,
        )

    assert points[1].daily_return == Decimal("0.100000")
    assert points[1].net_value == Decimal("1.100000")


def test_calculate_strategy_equity_curve_scopes_to_selected_same_date_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        selected = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="backtest",
            positions=[StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1"))],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 31, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="backtest",
            positions=[StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1"))],
        )
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=50)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(),
            signal_ids=[selected.strategy_signal.id],
        )

    assert [point.net_value for point in points] == [Decimal("1.000000"), Decimal("1.100000")]
    assert [point.daily_return for point in points] == [Decimal("0.000000"), Decimal("0.100000")]


def test_calculate_strategy_equity_curve_verifies_daily_values_and_rebalance_effect() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.600000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.400000")),
            ],
        )
        _add_signal(
            session,
            signal_date=date(2026, 6, 24),
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000")),
            ],
        )
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 25), close_price=55)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=200)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=180)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 25), close_price=198)
        _add_price(
            session,
            etf_id=qqq.id,
            trade_date=date(2026, 6, 26),
            close_price=Decimal("217.8"),
        )
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[
                date(2026, 6, 23),
                date(2026, 6, 24),
                date(2026, 6, 25),
                date(2026, 6, 26),
            ],
            strategy_config=_strategy_config(),
        )

    assert points == [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 6, 23),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 6, 24),
            net_value=Decimal("1.020000"),
            daily_return=Decimal("0.020000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 6, 25),
            net_value=Decimal("0.726000"),
            daily_return=Decimal("-0.288235"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 6, 26),
            net_value=Decimal("0.798600"),
            daily_return=Decimal("0.100000"),
        ),
    ]


def test_calculate_strategy_equity_curve_carries_and_rebalances_holdings() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 24), etf_id=qqq.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 25), close_price=55)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=200)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 25), close_price=220)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[
                date(2026, 6, 23),
                date(2026, 6, 24),
                date(2026, 6, 25),
            ],
            strategy_config=_strategy_config(),
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.100000"),
        Decimal("0.550000"),
    ]


def test_calculate_strategy_equity_curve_keeps_net_value_for_empty_holdings() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 22), date(2026, 6, 23)],
            strategy_config=_strategy_config(),
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.000000"),
    ]
    assert points[1].daily_return == Decimal("0.000000")


@pytest.mark.parametrize(
    ("prices", "missing_date"),
    [
        ([(date(2026, 6, 24), 110)], date(2026, 6, 23)),
        ([(date(2026, 6, 23), 100)], date(2026, 6, 24)),
    ],
)
def test_calculate_strategy_equity_curve_rejects_missing_held_price_endpoint(
    prices: list[tuple[date, int]],
    missing_date: date,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        for trade_date, close_price in prices:
            _add_price(session, etf_id=spy.id, trade_date=trade_date, close_price=close_price)
        session.commit()

        with pytest.raises(ValueError, match=missing_date.isoformat()):
            calculate_strategy_equity_curve(
                session,
                trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
                strategy_config=_strategy_config(),
            )


def test_calculate_strategy_equity_curve_deducts_initial_entry_transaction_cost() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=100)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=10),
        )

    assert points[1].daily_return == Decimal("-0.001000")
    assert points[1].net_value == Decimal("0.999000")


def test_calculate_strategy_equity_curve_deducts_rebalance_transaction_cost() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=qqq.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=110)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=10),
        )

    assert points[1].daily_return == Decimal("0.097800")
    assert points[1].net_value == Decimal("1.097800")


def test_calculate_strategy_equity_curve_skips_transaction_cost_when_configured_zero() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=100)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=0),
        )

    assert points[1].daily_return == Decimal("0.000000")
    assert points[1].net_value == Decimal("1.000000")


def test_calculate_strategy_equity_curve_applies_different_turnover_costs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.600000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.400000")),
            ],
        )
        _add_signal(
            session,
            signal_date=date(2026, 6, 23),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.800000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.200000")),
            ],
        )
        _add_signal(
            session,
            signal_date=date(2026, 6, 24),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.500000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.500000")),
            ],
        )
        for trade_date in [date(2026, 6, 23), date(2026, 6, 24), date(2026, 6, 25)]:
            _add_price(session, etf_id=spy.id, trade_date=trade_date, close_price=100)
            _add_price(session, etf_id=qqq.id, trade_date=trade_date, close_price=100)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[
                date(2026, 6, 23),
                date(2026, 6, 24),
                date(2026, 6, 25),
            ],
            strategy_config=_strategy_config(transaction_cost_bps=25),
        )

    assert points[1].daily_return == Decimal("-0.001000")
    assert points[1].net_value == Decimal("0.999000")
    assert points[2].daily_return == Decimal("-0.001500")
    assert points[2].net_value == Decimal("0.997502")


def test_calculate_strategy_equity_curve_applies_different_cost_rates() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=qqq.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=100)
        session.commit()

        low_cost_points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=10),
        )
        high_cost_points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=25),
        )

    assert low_cost_points[1].daily_return == Decimal("0.097800")
    assert low_cost_points[1].net_value == Decimal("1.097800")
    assert high_cost_points[1].daily_return == Decimal("0.094500")
    assert high_cost_points[1].net_value == Decimal("1.094500")
    assert high_cost_points[1].daily_return < low_cost_points[1].daily_return


def test_calculate_strategy_equity_curve_transaction_cost_reduces_net_value() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=qqq.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=110)
        session.commit()

        no_cost_points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=0),
        )
        cost_points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=10),
        )

    assert no_cost_points[1].daily_return == Decimal("0.100000")
    assert no_cost_points[1].net_value == Decimal("1.100000")
    assert cost_points[1].daily_return == Decimal("0.097800")
    assert cost_points[1].net_value == Decimal("1.097800")
    assert cost_points[1].net_value < no_cost_points[1].net_value


def test_calculate_strategy_annualized_return_uses_calendar_day_span() -> None:
    result = calculate_strategy_annualized_return(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2027, 1, 1),
                net_value=Decimal("1.100000"),
                daily_return=Decimal("0.100000"),
            ),
        ]
    )

    assert result == StrategyAnnualizedReturn(
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.100000"),
    )


def test_performance_metrics_keep_calendar_cagr_and_daily_return_sharpe_contracts() -> None:
    # The effective daily returns compound to 1.025049 over a 365-calendar-day
    # curve.  CAGR is therefore 0.025049, while the 252D Sharpe numerator is
    # the annualized arithmetic excess return, not CAGR minus the risk-free rate.
    risk_free_rate = Decimal("0.0126")
    effective_returns = [Decimal("0.010000"), Decimal("-0.005000"), Decimal("0.020000")]
    points = [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 1),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 4, 1),
            net_value=Decimal("1.010000"),
            daily_return=effective_returns[0],
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 8, 1),
            net_value=Decimal("1.004950"),
            daily_return=effective_returns[1],
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2027, 1, 1),
            net_value=Decimal("1.025049"),
            daily_return=effective_returns[2],
        ),
    ]

    annualized_return = calculate_strategy_annualized_return(points)
    volatility = calculate_strategy_volatility(points)
    sharpe_ratio = calculate_strategy_sharpe_ratio(points, risk_free_rate=risk_free_rate)

    assert annualized_return == StrategyAnnualizedReturn(
        total_return=Decimal("0.025049"),
        annualized_return=Decimal("0.025049"),
    )
    assert volatility == StrategyVolatility(volatility=Decimal("0.163095"))
    assert sharpe_ratio == StrategySharpeRatio(sharpe_ratio=Decimal("12.798671"))

    daily_risk_free_rate = risk_free_rate / Decimal("252")
    mean_excess_return = sum(
        (daily_return - daily_risk_free_rate for daily_return in effective_returns), Decimal("0")
    ) / Decimal(len(effective_returns))
    mean_return = sum(effective_returns, Decimal("0")) / Decimal(len(effective_returns))
    population_variance = sum(
        ((daily_return - mean_return) ** 2 for daily_return in effective_returns), Decimal("0")
    ) / Decimal(len(effective_returns))
    annualized_arithmetic_excess_return = mean_excess_return * Decimal("252")
    unquantized_annualized_volatility = Decimal(str(sqrt(float(population_variance)) * sqrt(252)))
    reconstructed_sharpe = (
        annualized_arithmetic_excess_return / unquantized_annualized_volatility
    ).quantize(Decimal("0.000001"))
    cagr_based_ratio = (
        (annualized_return.annualized_return - risk_free_rate) / unquantized_annualized_volatility
    ).quantize(Decimal("0.000001"))

    assert annualized_arithmetic_excess_return == Decimal("2.087400000000000000000000000")
    assert reconstructed_sharpe == Decimal("12.798671")
    assert reconstructed_sharpe == sharpe_ratio.sharpe_ratio
    assert cagr_based_ratio == Decimal("0.076330")
    assert cagr_based_ratio != sharpe_ratio.sharpe_ratio


def test_calculate_strategy_annualized_return_returns_zero_for_flat_curve() -> None:
    result = calculate_strategy_annualized_return(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2027, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
        ]
    )

    assert result == StrategyAnnualizedReturn(
        total_return=Decimal("0.000000"),
        annualized_return=Decimal("0.000000"),
    )


def test_calculate_strategy_annualized_return_returns_none_for_single_point() -> None:
    result = calculate_strategy_annualized_return(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            )
        ]
    )

    assert result == StrategyAnnualizedReturn(total_return=None, annualized_return=None)


def test_calculate_strategy_annualized_return_returns_none_for_same_day_points() -> None:
    result = calculate_strategy_annualized_return(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.100000"),
                daily_return=Decimal("0.100000"),
            ),
        ]
    )

    assert result == StrategyAnnualizedReturn(total_return=None, annualized_return=None)


def test_calculate_strategy_annualized_return_returns_none_for_non_positive_start() -> None:
    result = calculate_strategy_annualized_return(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("0.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2027, 1, 1),
                net_value=Decimal("1.100000"),
                daily_return=Decimal("0.100000"),
            ),
        ]
    )

    assert result == StrategyAnnualizedReturn(total_return=None, annualized_return=None)


def test_calculate_strategy_maximum_drawdown_returns_deepest_peak_to_trough_interval() -> None:
    result = calculate_strategy_maximum_drawdown(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.250000"),
                daily_return=Decimal("0.250000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 3),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("-0.200000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 4),
                net_value=Decimal("1.300000"),
                daily_return=Decimal("0.300000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 5),
                net_value=Decimal("0.910000"),
                daily_return=Decimal("-0.300000"),
            ),
        ]
    )

    assert result == StrategyMaximumDrawdown(
        max_drawdown=Decimal("-0.300000"),
        peak_date=date(2026, 1, 4),
        trough_date=date(2026, 1, 5),
    )


def test_calculate_strategy_maximum_drawdown_returns_initial_peak_for_falling_curve() -> None:
    result = calculate_strategy_maximum_drawdown(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("0.900000"),
                daily_return=Decimal("-0.100000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 3),
                net_value=Decimal("0.750000"),
                daily_return=Decimal("-0.166667"),
            ),
        ]
    )

    assert result == StrategyMaximumDrawdown(
        max_drawdown=Decimal("-0.250000"),
        peak_date=date(2026, 1, 1),
        trough_date=date(2026, 1, 3),
    )


def test_calculate_strategy_maximum_drawdown_keeps_trough_when_curve_recovers() -> None:
    result = calculate_strategy_maximum_drawdown(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.200000"),
                daily_return=Decimal("0.200000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 3),
                net_value=Decimal("0.840000"),
                daily_return=Decimal("-0.300000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 4),
                net_value=Decimal("1.080000"),
                daily_return=Decimal("0.285714"),
            ),
        ]
    )

    assert result == StrategyMaximumDrawdown(
        max_drawdown=Decimal("-0.300000"),
        peak_date=date(2026, 1, 2),
        trough_date=date(2026, 1, 3),
    )


def test_calculate_strategy_maximum_drawdown_returns_zero_for_empty_curve() -> None:
    result = calculate_strategy_maximum_drawdown([])

    assert result == StrategyMaximumDrawdown(
        max_drawdown=Decimal("0.000000"),
        peak_date=None,
        trough_date=None,
    )


def test_calculate_strategy_maximum_drawdown_returns_zero_for_flat_curve() -> None:
    result = calculate_strategy_maximum_drawdown(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
        ]
    )

    assert result == StrategyMaximumDrawdown(
        max_drawdown=Decimal("0.000000"),
        peak_date=None,
        trough_date=None,
    )


def test_calculate_strategy_maximum_drawdown_returns_zero_for_rising_curve() -> None:
    result = calculate_strategy_maximum_drawdown(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.100000"),
                daily_return=Decimal("0.100000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 3),
                net_value=Decimal("1.200000"),
                daily_return=Decimal("0.090909"),
            ),
        ]
    )

    assert result == StrategyMaximumDrawdown(
        max_drawdown=Decimal("0.000000"),
        peak_date=None,
        trough_date=None,
    )


def test_calculate_strategy_volatility_excludes_initial_placeholder_return() -> None:
    result = calculate_strategy_volatility(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.990000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.010000"),
                daily_return=Decimal("0.010000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 3),
                net_value=Decimal("0.989800"),
                daily_return=Decimal("-0.020000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 4),
                net_value=Decimal("1.019494"),
                daily_return=Decimal("0.030000"),
            ),
        ]
    )

    assert result == StrategyVolatility(volatility=Decimal("0.326190"))


def test_calculate_strategy_volatility_returns_zero_for_flat_returns() -> None:
    result = calculate_strategy_volatility(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 3),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
        ]
    )

    assert result == StrategyVolatility(volatility=Decimal("0.000000"))


def test_calculate_strategy_volatility_returns_none_for_empty_curve() -> None:
    result = calculate_strategy_volatility([])

    assert result == StrategyVolatility(volatility=None)


def test_calculate_strategy_volatility_returns_none_for_one_effective_return() -> None:
    result = calculate_strategy_volatility(
        [
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 1),
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.010000"),
                daily_return=Decimal("0.010000"),
            ),
        ]
    )

    assert result == StrategyVolatility(volatility=None)


def test_calculate_strategy_sharpe_ratio_uses_effective_daily_excess_returns() -> None:
    # risk_free_rate = 0.0126 -> daily_rf = 0.0126 / 252 = 0.00005
    # Effective observations (points[1:]) and their excess returns:
    #   0.005050 - 0.00005 = 0.005000
    #   0.015050 - 0.00005 = 0.015000
    # mean_excess = (0.005 + 0.015) / 2 = 0.010000
    # population variance = ((0.005-0.01)^2 + (0.015-0.01)^2) / 2 = 0.000025
    # population stddev  = sqrt(0.000025) = 0.005000
    # sharpe = 0.01 / 0.005 * sqrt(252) = 2 * 15.874507... = 31.749015... -> 31.749016
    # The hand-derived value only holds when the initial placeholder return
    # (0.000000) is excluded: including it would shift both the mean and the
    # population standard deviation, producing a different result.
    # net_value is irrelevant to Sharpe (only daily_return is read).
    points = [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 1),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 2),
            net_value=Decimal("1.005050"),
            daily_return=Decimal("0.005050"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 3),
            net_value=Decimal("1.020253"),
            daily_return=Decimal("0.015050"),
        ),
    ]

    result = calculate_strategy_sharpe_ratio(points, risk_free_rate=Decimal("0.0126"))

    assert result == StrategySharpeRatio(sharpe_ratio=Decimal("31.749016"))


def test_calculate_strategy_sharpe_ratio_returns_negative_for_negative_excess_return() -> None:
    # risk_free_rate = 0.0126 -> daily_rf = 0.00005
    # Effective excess returns: -0.015000, -0.005000 (two non-constant returns)
    # mean_excess = -0.010000, population stddev = 0.005000
    # sharpe = -0.01 / 0.005 * sqrt(252) = -31.749016
    points = [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 1),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 2),
            net_value=Decimal("0.985050"),
            daily_return=Decimal("-0.014950"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 3),
            net_value=Decimal("0.980175"),
            daily_return=Decimal("-0.004950"),
        ),
    ]

    result = calculate_strategy_sharpe_ratio(points, risk_free_rate=Decimal("0.0126"))

    assert result == StrategySharpeRatio(sharpe_ratio=Decimal("-31.749016"))


def test_calculate_strategy_sharpe_ratio_returns_none_for_zero_effective_observations() -> None:
    # Only the initial placeholder point -> no effective observations.
    points = [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 1),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
    ]

    result = calculate_strategy_sharpe_ratio(points, risk_free_rate=Decimal("0.0126"))

    assert result == StrategySharpeRatio(sharpe_ratio=None)


def test_calculate_strategy_sharpe_ratio_returns_none_for_single_effective_observation() -> None:
    # Placeholder plus exactly one effective observation -> fewer than two.
    points = [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 1),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 2),
            net_value=Decimal("1.005050"),
            daily_return=Decimal("0.005050"),
        ),
    ]

    result = calculate_strategy_sharpe_ratio(points, risk_free_rate=Decimal("0.0126"))

    assert result == StrategySharpeRatio(sharpe_ratio=None)


def test_calculate_strategy_sharpe_ratio_returns_none_for_zero_dispersion() -> None:
    # All effective daily returns are equal (here, zero, matching a flat
    # equity curve over the backtest window) -> the population standard
    # deviation of daily excess returns is zero, so no Sharpe ratio is
    # returned. This also guards against a regression where Decimal rounding
    # in the mean left a tiny nonzero variance artifact on identical returns.
    points = [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 1),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 2),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
        StrategyEquityCurvePoint(
            trade_date=date(2026, 1, 3),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        ),
    ]

    result = calculate_strategy_sharpe_ratio(points, risk_free_rate=Decimal("0.02"))

    assert result == StrategySharpeRatio(sharpe_ratio=None)


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _strategy_config(transaction_cost_bps: float = 0) -> StrategyConfig:
    return validate_strategy_config(
        {
            "strategy_id": "Dual_momentum",
            "version": "v1",
            "type": "dual_momentum",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {
                "momentum": {"short_window_days": 63, "long_window_days": 126},
                "score_weights": {"short": 0.4, "long": 0.6},
                "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                "selection": {"top_n": 2},
                "defense": {"assets": [{"exchange": "SSE", "symbol": "511010"}]},
            },
            "costs": {
                "transaction_cost_bps": transaction_cost_bps,
            },
            "performance": {
                "risk_free_rate": 0.02,
            },
        }
    )


def _add_etf(session: Session, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf


def _add_signal(
    session: Session,
    *,
    signal_date: date,
    etf_id: int | None = None,
    positions: list[StrategySignalPositionInput] | None = None,
) -> None:
    persist_strategy_signal(
        session,
        strategy_id="Dual_momentum",
        signal_date=signal_date,
        config_version="v1",
        generated_at=datetime.combine(signal_date, datetime.min.time(), tzinfo=UTC),
        status="success",
        result="rebalance",
        source="manual",
        positions=positions
        if positions is not None
        else [
            StrategySignalPositionInput(
                etf_id=etf_id or 0,
                target_weight=Decimal("1.000000"),
            )
        ],
    )


def test_equity_curve_no_artificial_jump_on_ex_dividend_date() -> None:
    """Interval-forward-adjusted prices eliminate dividend-induced price jumps.

    On the ex-dividend date the unadjusted close drops by the dividend amount,
    but the backward-adjustment factor increases. Projection of both rows
    using the current interval date as anchor stays continuous.
    The equity curve's daily return reflects only real market movement,
    not the dividend artifact.
    """
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(
            session,
            signal_date=date(2026, 6, 22),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        # Pre-ex-dividend: close=100, factor=1.0 -> backward-adjusted price=100
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        # Ex-dividend: close drops to 90 (dividend payout), factor rises to 1.1
        # Backward-adjusted price = 90 * 1.1 = 99 (continuous, no artificial -10% jump)
        _add_price(
            session,
            etf_id=spy.id,
            trade_date=date(2026, 6, 24),
            close_price=90,
            factor_hfq=Decimal("1.1"),
        )
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(),
        )

    # Daily return should be -1% (99/100 - 1), NOT -10% (90/100 - 1)
    assert points[1].daily_return == Decimal("-0.010000")
    assert points[1].net_value == Decimal("0.990000")


def test_equity_curve_projects_each_interval_at_its_current_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    calls: list[tuple[tuple[date, ...], date]] = []
    real_projection = equity_curve_module.forward_adjusted_prices

    def recording_projection(
        prices: list[MarketPrice],
        *,
        rebalance_date: date,
    ):
        calls.append((tuple(price.trade_date for price in prices), rebalance_date))
        return real_projection(prices, rebalance_date=rebalance_date)

    monkeypatch.setattr(equity_curve_module, "forward_adjusted_prices", recording_projection)

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 22), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(
            session,
            etf_id=spy.id,
            trade_date=date(2026, 6, 24),
            close_price=50,
            factor_hfq=Decimal("2"),
        )
        _add_price(
            session,
            etf_id=spy.id,
            trade_date=date(2026, 6, 25),
            close_price=25,
            factor_hfq=Decimal("4"),
        )
        session.commit()

        calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24), date(2026, 6, 25)],
            strategy_config=_strategy_config(),
        )

    assert calls == [
        ((date(2026, 6, 23), date(2026, 6, 24)), date(2026, 6, 24)),
        ((date(2026, 6, 24), date(2026, 6, 25)), date(2026, 6, 25)),
    ]


def _market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: int | Decimal,
    factor_hfq: Decimal = Decimal("1"),
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=Decimal(close_price),
        high_price=Decimal(close_price),
        low_price=Decimal(close_price),
        close_price=Decimal(close_price),
        factor_hfq=factor_hfq,
        volume=1000,
    )


def _add_price(
    session: Session,
    *,
    etf_id: int,
    trade_date: date,
    close_price: int | Decimal,
    factor_hfq: Decimal = Decimal("1"),
) -> None:
    session.add(
        _market_price(
            etf_id=etf_id,
            trade_date=trade_date,
            close_price=close_price,
            factor_hfq=factor_hfq,
        )
    )
