from datetime import UTC, date, datetime
from decimal import Decimal

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
from vela_core.strategy_config import StrategyConfig


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
            signal_date=date(2026, 6, 23),
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


def test_calculate_strategy_equity_curve_carries_and_rebalances_holdings() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 25), etf_id=qqq.id)
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
        Decimal("1.210000"),
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


def test_calculate_strategy_equity_curve_treats_missing_price_input_as_neutral() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(),
        )

    assert points[1].net_value == Decimal("1.000000")
    assert points[1].daily_return == Decimal("0.000000")


def test_calculate_strategy_equity_curve_deducts_initial_entry_transaction_cost() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 24), etf_id=spy.id)
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
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 24), etf_id=qqq.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=110)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_config=_strategy_config(transaction_cost_bps=10),
        )

    assert points[1].daily_return == Decimal("0.098000")
    assert points[1].net_value == Decimal("1.098000")


def test_calculate_strategy_equity_curve_skips_transaction_cost_when_configured_zero() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 24), etf_id=spy.id)
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


def test_calculate_strategy_sharpe_ratio_uses_configured_risk_free_rate() -> None:
    config = _strategy_config()

    result = calculate_strategy_sharpe_ratio(
        StrategyAnnualizedReturn(
            total_return=Decimal("0.100000"),
            annualized_return=Decimal("0.120000"),
        ),
        StrategyVolatility(volatility=Decimal("0.200000")),
        risk_free_rate=Decimal(str(config.performance.risk_free_rate)),
    )

    assert result == StrategySharpeRatio(sharpe_ratio=Decimal("0.500000"))


def test_calculate_strategy_sharpe_ratio_returns_negative_for_negative_excess_return() -> None:
    result = calculate_strategy_sharpe_ratio(
        StrategyAnnualizedReturn(
            total_return=Decimal("0.010000"),
            annualized_return=Decimal("0.010000"),
        ),
        StrategyVolatility(volatility=Decimal("0.100000")),
        risk_free_rate=Decimal("0.030000"),
    )

    assert result == StrategySharpeRatio(sharpe_ratio=Decimal("-0.200000"))


def test_calculate_strategy_sharpe_ratio_returns_none_for_unavailable_annualized_return() -> None:
    result = calculate_strategy_sharpe_ratio(
        StrategyAnnualizedReturn(total_return=None, annualized_return=None),
        StrategyVolatility(volatility=Decimal("0.100000")),
        risk_free_rate=Decimal("0.020000"),
    )

    assert result == StrategySharpeRatio(sharpe_ratio=None)


def test_calculate_strategy_sharpe_ratio_returns_none_for_unavailable_volatility() -> None:
    result = calculate_strategy_sharpe_ratio(
        StrategyAnnualizedReturn(
            total_return=Decimal("0.100000"),
            annualized_return=Decimal("0.120000"),
        ),
        StrategyVolatility(volatility=None),
        risk_free_rate=Decimal("0.020000"),
    )

    assert result == StrategySharpeRatio(sharpe_ratio=None)


def test_calculate_strategy_sharpe_ratio_returns_none_for_zero_volatility() -> None:
    result = calculate_strategy_sharpe_ratio(
        StrategyAnnualizedReturn(
            total_return=Decimal("0.000000"),
            annualized_return=Decimal("0.000000"),
        ),
        StrategyVolatility(volatility=Decimal("0.000000")),
        risk_free_rate=Decimal("0.020000"),
    )

    assert result == StrategySharpeRatio(sharpe_ratio=None)


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _strategy_config(transaction_cost_bps: float = 0) -> StrategyConfig:
    return StrategyConfig.model_validate(
        {
            "strategy_id": "dual_momentum",
            "version": "v1",
            "universe_config": "config/etf_pool.yaml",
            "momentum": {
                "short_window_days": 63,
                "long_window_days": 126,
            },
            "score_weights": {
                "short": 0.4,
                "long": 0.6,
            },
            "trend_filter": {
                "moving_average_days": 120,
                "price_relation": "above",
            },
            "selection": {
                "top_n": 2,
            },
            "defense": {
                "asset": {
                    "exchange": "SSE",
                    "symbol": "511010",
                },
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
        signal_date=signal_date,
        config_version="v1",
        generated_at=datetime.combine(signal_date, datetime.min.time(), tzinfo=UTC),
        status="success",
        result="rebalance",
        positions=positions
        if positions is not None
        else [
            StrategySignalPositionInput(
                etf_id=etf_id or 0,
                target_weight=Decimal("1.000000"),
            )
        ],
    )


def _add_price(
    session: Session,
    *,
    etf_id: int,
    trade_date: date,
    close_price: int,
) -> None:
    session.add(
        MarketPrice(
            etf_id=etf_id,
            trade_date=trade_date,
            open_price=Decimal(close_price),
            high_price=Decimal(close_price),
            low_price=Decimal(close_price),
            close_price=Decimal(close_price),
            adjusted_close=None,
            volume=1000,
        )
    )
