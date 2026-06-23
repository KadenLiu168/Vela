from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from vela_core import generate_historical_strategy_signals, generate_strategy_signal
from vela_core.models import Base, ETFInfo, MarketPrice, StrategySignal, StrategySignalPosition
from vela_core.strategy_config import StrategyConfig


def test_generate_strategy_signal_persists_ranked_positions() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))
        _add_price_history(session, etf_id=second.id, current_price=Decimal("160"))

        result = generate_strategy_signal(
            session,
            signal_date=_trade_date(120),
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

        signal = session.get(StrategySignal, result.strategy_signal_id)
        positions = session.scalars(select(StrategySignalPosition)).all()

    assert signal is not None
    assert signal.status == "success"
    assert signal.result == "rebalance"
    assert [position.symbol for position in result.positions] == ["510300", "159915"]
    assert [position.rank for position in result.positions] == [1, 2]
    assert {position.target_weight for position in positions} == {Decimal("0.500000")}


def test_generate_strategy_signal_persists_defensive_fallback() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        _add_etf(session, exchange="SSE", symbol="510300")
        defense = _add_etf(session, exchange="SSE", symbol="511010")
        defense_id = defense.id

        result = generate_strategy_signal(
            session,
            signal_date=_trade_date(120),
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

        signal = session.get(StrategySignal, result.strategy_signal_id)
        position = session.scalar(select(StrategySignalPosition))

    assert signal is not None
    assert signal.status == "success"
    assert result.positions[0].etf_id == defense_id
    assert result.positions[0].symbol == "511010"
    assert result.positions[0].rank is None
    assert result.positions[0].score is None
    assert result.positions[0].target_weight == Decimal("1")
    assert position is not None
    assert position.etf_id == defense_id


def test_generate_strategy_signal_persists_failure_when_no_active_etfs_exist() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        result = generate_strategy_signal(
            session,
            signal_date=_trade_date(120),
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert signal is not None
    assert signal.status == "failed"
    assert signal.error_message == "No active ETFs found"
    assert result.error_message == "No active ETFs found"
    assert result.positions == []


def test_generate_strategy_signal_persists_failure_when_defensive_asset_is_missing() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    with session_factory() as session:
        _add_etf(session, exchange="SSE", symbol="510300")

        result = generate_strategy_signal(
            session,
            signal_date=_trade_date(120),
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert signal is not None
    assert signal.status == "failed"
    assert signal.error_message == "Defensive asset not found as active ETF: SSE 511010"
    assert result.error_message == "Defensive asset not found as active ETF: SSE 511010"
    assert result.positions == []


def test_generate_historical_strategy_signals_persists_rebalance_date_positions() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        first_id = first.id
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"), end_offset=127)
        _add_price_history(session, etf_id=second.id, current_price=Decimal("160"), end_offset=127)

        results = generate_historical_strategy_signals(
            session,
            historical_trading_dates=[_trade_date(120), _trade_date(127)],
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

        signals = session.scalars(select(StrategySignal).order_by(StrategySignal.signal_date)).all()
        positions = session.scalars(
            select(StrategySignalPosition).order_by(StrategySignalPosition.strategy_signal_id)
        ).all()

    assert [result.signal_date for result in results] == [_trade_date(120), _trade_date(127)]
    assert [signal.signal_date for signal in signals] == [_trade_date(120), _trade_date(127)]
    assert [position.etf_id for position in positions] == [first_id, first_id]
    assert {position.target_weight for position in positions} == {Decimal("1.000000")}


def test_generate_historical_strategy_signals_do_not_use_future_prices() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        first_id = first.id
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"), end_offset=127)
        _add_price_history(
            session,
            etf_id=second.id,
            current_price=Decimal("160"),
            end_offset=127,
            prices_by_offset={127: Decimal("1000")},
        )

        results = generate_historical_strategy_signals(
            session,
            historical_trading_dates=[_trade_date(120)],
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

    assert [result.signal_date for result in results] == [_trade_date(120)]
    assert [position.etf_id for position in results[0].positions] == [first_id]


def test_generate_historical_strategy_signals_returns_empty_without_persisting_rows() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    with session_factory() as session:
        results = generate_historical_strategy_signals(
            session,
            historical_trading_dates=[],
            config=config,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        )
        session.commit()

        signal_count = len(session.scalars(select(StrategySignal)).all())

    assert results == []
    assert signal_count == 0


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


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
    prices_by_offset: dict[int, Decimal] | None = None,
) -> None:
    prices_by_offset = prices_by_offset or {}
    session.add_all(
        _market_price(
            etf_id=etf_id,
            trade_date=_trade_date(offset),
            close_price=prices_by_offset.get(
                offset,
                current_price if offset in {120, end_offset} else Decimal("100"),
            ),
        )
        for offset in range(end_offset + 1)
    )
    session.commit()


def _trade_date(offset: int) -> date:
    return date(2026, 1, 1) + timedelta(days=offset)


def _market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal,
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        adjusted_close=None,
        volume=1000,
    )


def _strategy_config(*, top_n: int) -> StrategyConfig:
    config: dict[str, Any] = {
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
            "asset": {
                "exchange": "SSE",
                "symbol": "511010",
            },
        },
        "costs": {
            "transaction_cost_bps": 5,
        },
    }
    return StrategyConfig.model_validate(config)
