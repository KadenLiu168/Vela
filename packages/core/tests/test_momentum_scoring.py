from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import MomentumScore, calculate_momentum_score
from vela_core.models import Base, ETFInfo, MarketPrice
from vela_core.strategy_config import StrategyConfig


def test_calculates_weighted_momentum_score_from_complete_configured_windows() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("80"),
                20: Decimal("100"),
                30: Decimal("112"),
            },
            row_count=31,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )

    assert momentum_score == MomentumScore(
        etf_id=etf.id,
        as_of_date=_trade_date(30),
        short_return=Decimal("0.12"),
        long_return=Decimal("0.4"),
        score=Decimal("0.288"),
    )


def test_uses_configured_windows_instead_of_fixed_market_return_windows() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=7, long_window_days=13)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("65"),
                6: Decimal("100"),
                13: Decimal("130"),
            },
            row_count=14,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(13),
            config=config,
        )

    assert momentum_score.short_return == Decimal("0.3")
    assert momentum_score.long_return == Decimal("1")
    assert momentum_score.score == Decimal("0.72")


def test_reproduces_momentum_score_for_identical_inputs() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("80"),
                20: Decimal("100"),
                30: Decimal("112"),
            },
            row_count=31,
        )

        first_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )
        second_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )

    assert first_score == second_score


def test_returns_none_score_when_a_configured_window_has_insufficient_history() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=5, long_window_days=20)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                5: Decimal("100"),
                10: Decimal("125"),
            },
            row_count=11,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(10),
            config=config,
        )

    assert momentum_score.short_return == Decimal("0.25")
    assert momentum_score.long_return is None
    assert momentum_score.score is None


def test_returns_none_score_when_current_price_is_missing() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=31)

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(40),
            config=config,
        )

    assert momentum_score == MomentumScore(
        etf_id=etf.id,
        as_of_date=_trade_date(40),
        short_return=None,
        long_return=None,
        score=None,
    )


def test_uses_strategy_price_and_ignores_other_etf_histories() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        target_etf = _add_etf(session, symbol="SPY")
        other_etf = _add_etf(session, symbol="QQQ")
        _add_price_history(
            session,
            etf_id=target_etf.id,
            prices_by_offset={
                0: Decimal("1"),
                20: Decimal("1"),
                30: Decimal("1"),
            },
            adjusted_close_by_offset={
                0: Decimal("80"),
                20: Decimal("100"),
                30: Decimal("112"),
            },
            row_count=31,
        )
        _add_price_history(
            session,
            etf_id=other_etf.id,
            prices_by_offset={
                0: Decimal("1000"),
                20: Decimal("1000"),
                30: Decimal("1000"),
            },
            row_count=31,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=target_etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )

    assert momentum_score.short_return == Decimal("0.12")
    assert momentum_score.long_return == Decimal("0.4")
    assert momentum_score.score == Decimal("0.288")


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


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


def _add_price_history(
    session: Session,
    *,
    etf_id: int,
    prices_by_offset: dict[int, Decimal],
    row_count: int,
    adjusted_close_by_offset: dict[int, Decimal] | None = None,
) -> None:
    adjusted_close_by_offset = adjusted_close_by_offset or {}
    session.add_all(
        _market_price(
            etf_id=etf_id,
            trade_date=_trade_date(offset),
            close_price=prices_by_offset.get(offset, Decimal("100")),
            adjusted_close=adjusted_close_by_offset.get(offset),
        )
        for offset in range(row_count)
    )
    session.commit()


def _trade_date(offset: int) -> date:
    return date(2026, 1, 1) + timedelta(days=offset)


def _market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal,
    adjusted_close: Decimal | None = None,
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        adjusted_close=adjusted_close,
        volume=1000,
    )


def _strategy_config(
    *,
    short_window_days: int,
    long_window_days: int,
    short_weight: float = 0.4,
    long_weight: float = 0.6,
) -> StrategyConfig:
    config: dict[str, Any] = {
        "strategy_id": "dual_momentum",
        "version": "v1",
        "universe_config": "config/etf_pool.yaml",
        "momentum": {
            "short_window_days": short_window_days,
            "long_window_days": long_window_days,
        },
        "score_weights": {
            "short": short_weight,
            "long": long_weight,
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
            "transaction_cost_bps": 5,
        },
    }
    return StrategyConfig.model_validate(config)
