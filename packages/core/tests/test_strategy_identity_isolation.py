from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from vela_core.backtest_runner import run_backtest
from vela_core.models import BacktestRun, Base, ETFInfo, MarketPrice, StrategySignal
from vela_core.portfolio_holdings import calculate_portfolio_holdings
from vela_core.strategy_config import StrategyConfig, validate_strategy_config
from vela_core.strategy_equity_curve import calculate_strategy_equity_curve


def test_config_only_strategy_switch_keeps_persisted_identity_isolated() -> None:
    session_factory = _create_session_factory()
    dual_config = _dual_momentum_config()
    equal_config = _equal_weight_config()
    trading_dates = [date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)]

    with session_factory() as session:
        risk = _add_etf(session, exchange="SSE", symbol="510300")
        defense = _add_etf(session, exchange="SSE", symbol="511010")
        for trade_date, risk_price, defense_price in [
            (trading_dates[0], 100, 100),
            (trading_dates[1], 110, 101),
            (trading_dates[2], 121, 102),
        ]:
            _add_price(session, etf_id=risk.id, trade_date=trade_date, close_price=risk_price)
            _add_price(
                session,
                etf_id=defense.id,
                trade_date=trade_date,
                close_price=defense_price,
            )
        session.commit()

        dual_run = run_backtest(
            session,
            config=dual_config,
            start_date=trading_dates[0],
            end_date=trading_dates[-1],
            started_at=datetime(2026, 1, 13, tzinfo=UTC),
        )
        equal_run = run_backtest(
            session,
            config=equal_config,
            start_date=trading_dates[0],
            end_date=trading_dates[-1],
            started_at=datetime(2026, 1, 14, tzinfo=UTC),
        )
        session.commit()

        dual_signals = _signals_for(session, dual_config)
        equal_signals = _signals_for(session, equal_config)
        dual_holdings = calculate_portfolio_holdings(
            session,
            trading_dates=trading_dates,
            strategy_id=dual_config.strategy_id,
            config_version=dual_config.version,
        )
        equal_holdings = calculate_portfolio_holdings(
            session,
            trading_dates=trading_dates,
            strategy_id=equal_config.strategy_id,
            config_version=equal_config.version,
        )
        dual_curve = calculate_strategy_equity_curve(
            session,
            trading_dates=trading_dates,
            strategy_config=dual_config,
        )
        equal_curve = calculate_strategy_equity_curve(
            session,
            trading_dates=trading_dates,
            strategy_config=equal_config,
        )
        runs = session.scalars(select(BacktestRun).order_by(BacktestRun.id)).all()

    assert (dual_run.signal_count, equal_run.signal_count) == (3, 3)
    assert [(signal.strategy_id, signal.config_version) for signal in dual_signals] == [
        ("dual_momentum_test", "v1")
    ] * 3
    assert [(signal.strategy_id, signal.config_version) for signal in equal_signals] == [
        ("equal_weight_test", "v2")
    ] * 3
    assert [holding.etf_id for holding in dual_holdings[-1].holdings] == [defense.id]
    assert [holding.etf_id for holding in equal_holdings[-1].holdings] == [risk.id, defense.id]
    assert (dual_curve[-1].net_value, equal_curve[-1].net_value) == (
        Decimal("1.009901"),
        Decimal("1.054950"),
    )
    assert [(run.id, run.strategy_id, run.config_version) for run in runs] == [
        (dual_run.backtest_run_id, "dual_momentum_test", "v1"),
        (equal_run.backtest_run_id, "equal_weight_test", "v2"),
    ]


def _dual_momentum_config() -> StrategyConfig:
    return validate_strategy_config(
        {
            "strategy_id": "dual_momentum_test",
            "version": "v1",
            "type": "dual_momentum",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {
                "momentum": {"short_window_days": 63, "long_window_days": 126},
                "score_weights": {"short": 0.4, "long": 0.6},
                "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                "selection": {"top_n": 1},
                "defense": {"assets": [{"exchange": "SSE", "symbol": "511010"}]},
            },
            "costs": {"transaction_cost_bps": 0},
            "performance": {"risk_free_rate": 0},
        }
    )


def _equal_weight_config() -> StrategyConfig:
    return validate_strategy_config(
        {
            "strategy_id": "equal_weight_test",
            "version": "v2",
            "type": "equal_weight",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {},
            "costs": {"transaction_cost_bps": 0},
            "performance": {"risk_free_rate": 0},
        }
    )


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _add_etf(session: Session, *, exchange: str, symbol: str) -> ETFInfo:
    etf = ETFInfo(exchange=exchange, symbol=symbol, name=symbol, currency="CNY")
    session.add(etf)
    session.flush()
    return etf


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
            factor_hfq=Decimal("1"),
            volume=1000,
        )
    )


def _signals_for(session: Session, config: StrategyConfig) -> list[StrategySignal]:
    return list(
        session.scalars(
            select(StrategySignal)
            .where(StrategySignal.strategy_id == config.strategy_id)
            .where(StrategySignal.config_version == config.version)
            .order_by(StrategySignal.signal_date)
        )
    )
