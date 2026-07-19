from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from vela_core.models import Base, ETFInfo, MarketPrice, StrategySignal, StrategySignalPosition
from vela_core.strategy_config import StrategyConfig
from vela_core.strategy_signal_service import generate_and_persist_strategy_signal


def test_generate_and_persist_strategy_signal_uses_latest_local_market_date() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)
    latest_trade_date = _trade_date(120)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))
        _add_price_history(session, etf_id=second.id, current_price=Decimal("170"))

        result = generate_and_persist_strategy_signal(session, config=config)

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert result.signal_date == latest_trade_date
    assert signal is not None
    assert signal.signal_date == latest_trade_date
    assert signal.strategy_id == "dual_momentum"
    assert signal.config_version == "v1"
    assert signal.source == "manual"
    assert signal.backtest_run_id is None


def test_generate_and_persist_strategy_signal_preserves_explicit_signal_date() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)
    explicit_signal_date = _trade_date(119)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))
        _add_price_history(session, etf_id=second.id, current_price=Decimal("170"))

        result = generate_and_persist_strategy_signal(
            session,
            config=config,
            signal_date=explicit_signal_date,
        )

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert result.signal_date == explicit_signal_date
    assert signal is not None
    assert signal.signal_date == explicit_signal_date


def test_generate_and_persist_strategy_signal_rejects_missing_local_market_prices() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        with pytest.raises(ValueError, match="No local market prices found"):
            generate_and_persist_strategy_signal(session, config=config)

        signals = session.scalars(select(StrategySignal)).all()

    assert signals == []


def test_generate_and_persist_strategy_signal_persists_signal_and_positions() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))
        _add_price_history(session, etf_id=second.id, current_price=Decimal("170"))

        result = generate_and_persist_strategy_signal(session, config=config)

        signal = session.get(StrategySignal, result.strategy_signal_id)
        positions = session.scalars(select(StrategySignalPosition)).all()

    assert signal is not None
    assert result.strategy_signal_id == signal.id
    assert signal.status == "success"
    assert signal.result == "rebalance"
    assert [position.symbol for position in result.positions] == ["510300", "159915"]
    assert len(positions) == 2
    assert {position.target_weight for position in positions} == {Decimal("0.500000")}


def test_generate_and_persist_strategy_signal_records_scheduled_source() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))
        _add_price_history(session, etf_id=second.id, current_price=Decimal("170"))

        result = generate_and_persist_strategy_signal(
            session,
            config=config,
            source="scheduled",
        )
        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert signal is not None
    assert signal.source == "scheduled"
    assert signal.backtest_run_id is None


@pytest.mark.parametrize("source", ["backtest", "legacy", "unknown"])
def test_generate_and_persist_strategy_signal_rejects_non_live_source_before_write(
    source: str,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="Unsupported live strategy signal source"):
            generate_and_persist_strategy_signal(
                session,
                config=_strategy_config(top_n=2),
                source=source,
            )

        assert session.scalars(select(StrategySignal)).all() == []


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _add_etf(session: Session, *, exchange: str, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange=exchange,
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="CNY",
    )
    session.add(etf)
    session.flush()
    return etf


def _add_price_history(
    session: Session,
    *,
    etf_id: int,
    current_price: Decimal,
    end_offset: int = 120,
) -> None:
    session.add_all(
        MarketPrice(
            etf_id=etf_id,
            trade_date=_trade_date(offset),
            open_price=current_price if offset in {119, 120} else Decimal("100"),
            high_price=current_price if offset in {119, 120} else Decimal("100"),
            low_price=current_price if offset in {119, 120} else Decimal("100"),
            close_price=current_price if offset in {119, 120} else Decimal("100"),
            factor_hfq=Decimal("1"),
            volume=1000,
        )
        for offset in range(end_offset + 1)
    )
    session.commit()


def _trade_date(offset: int) -> date:
    return date(2026, 1, 1) + timedelta(days=offset)


def _strategy_config(*, top_n: int) -> StrategyConfig:
    return StrategyConfig.model_validate(
        {
            "strategy_id": "dual_momentum",
            "version": "v1",
            "universe_config": "config/etf_pool.yaml",
            "momentum": {
                "short_window_days": 63,
                "long_window_days": 120,
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
                "top_n": top_n,
            },
            "defense": {
                "assets": [
                    {
                        "exchange": "SSE",
                        "symbol": "511010",
                    },
                ],
            },
            "costs": {
                "transaction_cost_bps": 5,
            },
            "performance": {
                "risk_free_rate": 0.02,
            },
        }
    )
