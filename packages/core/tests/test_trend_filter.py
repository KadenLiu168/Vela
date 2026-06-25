from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import TrendFilterResult, apply_trend_filter
from vela_core.models import Base, ETFInfo, MarketPrice
from vela_core.strategy_config import StrategyConfig


def test_passes_when_current_price_is_above_120_day_moving_average() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={119: Decimal("150")},
            row_count=120,
        )

        result = apply_trend_filter(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(119),
            config=config,
        )

    assert result == TrendFilterResult(
        etf_id=etf.id,
        as_of_date=_trade_date(119),
        current_price=Decimal("150"),
        moving_average=Decimal("100.4166666666666666666666667"),
        passes_filter=True,
    )


def test_fails_when_current_price_equals_120_day_moving_average() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=120)

        result = apply_trend_filter(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(119),
            config=config,
        )

    assert result.current_price == Decimal("100")
    assert result.moving_average == Decimal("100")
    assert result.passes_filter is False


def test_fails_when_current_price_is_below_120_day_moving_average() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={119: Decimal("50")},
            row_count=120,
        )

        result = apply_trend_filter(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(119),
            config=config,
        )

    assert result.current_price == Decimal("50")
    assert result.moving_average == Decimal("99.58333333333333333333333333")
    assert result.passes_filter is False


def test_distinguishes_passing_and_failing_etfs_for_same_date() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        passing_etf = _add_etf(session, symbol="SPY")
        failing_etf = _add_etf(session, symbol="QQQ")
        _add_price_history(
            session,
            etf_id=passing_etf.id,
            prices_by_offset={119: Decimal("150")},
            row_count=120,
        )
        _add_price_history(
            session,
            etf_id=failing_etf.id,
            prices_by_offset={},
            row_count=120,
        )

        passing_result = apply_trend_filter(
            session,
            etf_id=passing_etf.id,
            as_of_date=_trade_date(119),
            config=config,
        )
        failing_result = apply_trend_filter(
            session,
            etf_id=failing_etf.id,
            as_of_date=_trade_date(119),
            config=config,
        )

    results = [passing_result, failing_result]
    assert [result.etf_id for result in results if result.passes_filter] == [passing_etf.id]
    assert passing_result.current_price == Decimal("150")
    assert passing_result.passes_filter is True
    assert failing_result.current_price == Decimal("100")
    assert failing_result.moving_average == Decimal("100")
    assert failing_result.passes_filter is False


def test_fails_when_current_price_is_missing() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=120)

        result = apply_trend_filter(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(130),
            config=config,
        )

    assert result == TrendFilterResult(
        etf_id=etf.id,
        as_of_date=_trade_date(130),
        current_price=None,
        moving_average=None,
        passes_filter=False,
    )


def test_fails_when_moving_average_is_missing() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=119)

        result = apply_trend_filter(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(118),
            config=config,
        )

    assert result == TrendFilterResult(
        etf_id=etf.id,
        as_of_date=_trade_date(118),
        current_price=Decimal("100"),
        moving_average=None,
        passes_filter=False,
    )


def test_uses_strategy_price_and_ignores_other_etf_histories() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config()

    with session_factory() as session:
        target_etf = _add_etf(session, symbol="SPY")
        other_etf = _add_etf(session, symbol="QQQ")
        _add_price_history(
            session,
            etf_id=target_etf.id,
            prices_by_offset={119: Decimal("1")},
            adjusted_close_by_offset={119: Decimal("150")},
            row_count=120,
        )
        _add_price_history(
            session,
            etf_id=other_etf.id,
            prices_by_offset={offset: Decimal("1000") for offset in range(120)},
            row_count=120,
        )

        result = apply_trend_filter(
            session,
            etf_id=target_etf.id,
            as_of_date=_trade_date(119),
            config=config,
        )

    assert result.current_price == Decimal("150")
    assert result.moving_average == Decimal("100.4166666666666666666666667")
    assert result.passes_filter is True


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


def _strategy_config() -> StrategyConfig:
    config: dict[str, Any] = {
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
            "transaction_cost_bps": 5,
        },
        "performance": {
            "risk_free_rate": 0.02,
        },
    }
    return StrategyConfig.model_validate(config)
