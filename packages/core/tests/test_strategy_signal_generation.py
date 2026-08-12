from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    generate_historical_strategy_signals,
    generate_strategy_signal,
    load_price_panel,
)
from vela_core.models import Base, ETFInfo, MarketPrice, StrategySignal, StrategySignalPosition
from vela_core.resolved_session_price import ResolvedSessionPrice
from vela_core.strategy_config import RebalanceConfig, StrategyConfig, validate_strategy_config
from vela_core.strategy_signal_persistence import (
    StrategySignalPositionInput,
    persist_strategy_signal,
)


def test_generate_strategy_signal_persists_ranked_positions() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence.strategy_signal.id

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))
        _add_price_history(session, etf_id=second.id, current_price=Decimal("160"))

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(120),
        )
        result = generate_strategy_signal(
            signal_date=_trade_date(120),
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

        signal = session.get(StrategySignal, result.strategy_signal_id)
        positions = session.scalars(_select_positions()).all()

    assert signal is not None
    assert signal.status == "success"
    assert signal.result == "rebalance"
    assert [position.symbol for position in result.positions] == ["510300", "159915"]
    assert [position.rank for position in result.positions] == [1, 2]
    assert {position.target_weight for position in positions} == {Decimal("0.500000")}


def test_generate_strategy_signal_persists_defensive_fallback() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence.strategy_signal.id

    with session_factory() as session:
        _add_etf(session, exchange="SSE", symbol="510300")
        defense = _add_etf(session, exchange="SSE", symbol="511010")
        defense_id = defense.id

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(120),
        )

        result = generate_strategy_signal(
            signal_date=_trade_date(120),
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

        signal = session.get(StrategySignal, result.strategy_signal_id)
        position = session.scalar(_select_positions())

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

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence.strategy_signal.id

    with session_factory() as session:
        result = generate_strategy_signal(
            signal_date=_trade_date(120),
            config=config,
            price_panel={},
            active_etfs=[],
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert signal is not None
    assert signal.status == "failed"
    assert signal.error_message == "No active ETFs found"
    assert result.error_message == "No active ETFs found"
    assert result.positions == []


def test_generate_strategy_signal_persists_failure_when_defensive_asset_is_missing() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=2)

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence.strategy_signal.id

    with session_factory() as session:
        only = _add_etf(session, exchange="SSE", symbol="510300")

        active_etfs = [only]
        price_panel = load_price_panel(
            session,
            etf_ids=[only.id],
            start_date=None,
            end_date=_trade_date(120),
        )

        result = generate_strategy_signal(
            signal_date=_trade_date(120),
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert signal is not None
    assert signal.status == "failed"
    assert signal.error_message == "Defensive asset not found as active ETF: SSE 511010"
    assert result.error_message == "Defensive asset not found as active ETF: SSE 511010"
    assert result.positions == []


def test_generate_strategy_signal_names_second_missing_defensive_asset() -> None:
    session_factory = _create_session_factory()
    config = validate_strategy_config(
        {
            "strategy_id": "dual_momentum",
            "version": "v1",
            "type": "dual_momentum",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {
                "momentum": {"short_window_days": 63, "long_window_days": 120},
                "score_weights": {"short": 0.4, "long": 0.6},
                "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                "selection": {"top_n": 2},
                "defense": {
                    "assets": [
                        {"exchange": "SSE", "symbol": "511010"},
                        {"exchange": "SSE", "symbol": "511880"},
                    ]
                },
            },
            "costs": {"transaction_cost_bps": 5},
            "performance": {"risk_free_rate": 0.02},
        }
    )

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence.strategy_signal.id

    with session_factory() as session:
        first_defense = _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first_defense.id, current_price=Decimal("180"))

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(120),
        )

        result = generate_strategy_signal(
            signal_date=_trade_date(120),
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

        signal = session.get(StrategySignal, result.strategy_signal_id)

    assert signal is not None
    assert signal.status == "failed"
    assert signal.error_message == "Defensive asset not found as active ETF: SSE 511880"
    assert result.error_message == "Defensive asset not found as active ETF: SSE 511880"
    assert result.positions == []


def test_generate_historical_strategy_signals_persists_rebalance_date_positions() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    captured_signal_ids: list[int] = []

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            captured_signal_ids.append(persistence.strategy_signal.id)
            return persistence.strategy_signal.id

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        first_id = first.id
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"), end_offset=127)
        _add_price_history(session, etf_id=second.id, current_price=Decimal("160"), end_offset=127)

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(127),
        )

        results = generate_historical_strategy_signals(
            historical_trading_dates=[_trade_date(120), _trade_date(127)],
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

        signals = session.scalars(_select_signals().order_by(StrategySignal.signal_date)).all()
        positions = session.scalars(
            _select_positions().order_by(StrategySignalPosition.strategy_signal_id)
        ).all()

    assert [result.signal_date for result in results] == [_trade_date(120), _trade_date(127)]
    assert [signal.signal_date for signal in signals] == [_trade_date(120), _trade_date(127)]
    assert [position.etf_id for position in positions] == [first_id, first_id]
    assert {position.target_weight for position in positions} == {Decimal("1.000000")}
    assert len(captured_signal_ids) == 2


def test_generate_historical_strategy_signals_do_not_use_future_prices() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    def _persist(
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[dict[str, object]],
        error_message: str | None,
    ) -> int:
        with session_factory() as session:
            persistence = persist_strategy_signal(
                session,
                strategy_id="dual_momentum",
                signal_date=signal_date,
                config_version="v1",
                generated_at=generated_at,
                status=status,
                result=result,
                source="manual",
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence.strategy_signal.id

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

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(127),
        )

        results = generate_historical_strategy_signals(
            historical_trading_dates=[_trade_date(120)],
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=_persist,
        )

    assert [result.signal_date for result in results] == [_trade_date(120)]
    assert [position.etf_id for position in results[0].positions] == [first_id]


def test_generate_historical_strategy_signals_returns_empty_without_persisting_rows() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    with session_factory() as session:
        results = generate_historical_strategy_signals(
            historical_trading_dates=[],
            config=config,
            price_panel={},
            active_etfs=[],
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=None,
        )

        signal_count = len(session.scalars(_select_signals()).all())

    assert results == []
    assert signal_count == 0


def test_historical_signals_use_listing_boundary_and_keep_non_tradable_target() -> None:
    config = validate_strategy_config(
        {
            "strategy_id": "equal_weight",
            "version": "v1",
            "type": "equal_weight",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {},
            "costs": {"transaction_cost_bps": 5},
            "performance": {"risk_free_rate": 0.02},
        }
    )
    first = _etf_for_resolved_panel(1, "510300", date(2026, 1, 2))
    second = _etf_for_resolved_panel(2, "513100", date(2026, 1, 5))
    panel = {
        1: [_resolved_signal_point(1, date(2026, 1, 2), "10")],
        2: [
            _resolved_signal_point(
                2,
                date(2026, 1, 5),
                "20",
                tradable=False,
                resolution="confirmed_non_trading_carry",
            )
        ],
    }

    results = generate_historical_strategy_signals(
        historical_trading_dates=[date(2026, 1, 2), date(2026, 1, 5)],
        config=config,
        price_panel=panel,
        active_etfs=[first, second],
    )

    assert [result.signal_date for result in results] == [
        date(2026, 1, 2),
        date(2026, 1, 5),
    ]
    assert [[position.etf_id for position in result.positions] for result in results] == [
        [1],
        [1, 2],
    ]


def test_single_date_signal_excludes_etf_before_listing_date() -> None:
    config = validate_strategy_config(
        {
            "strategy_id": "equal_weight",
            "version": "v1",
            "type": "equal_weight",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {},
            "costs": {"transaction_cost_bps": 5},
            "performance": {"risk_free_rate": 0.02},
        }
    )
    signal_date = date(2026, 1, 2)
    listed = _etf_for_resolved_panel(1, "510300", signal_date)
    future = _etf_for_resolved_panel(2, "513100", date(2026, 1, 5))

    result = generate_strategy_signal(
        signal_date=signal_date,
        config=config,
        price_panel={},
        active_etfs=[listed, future],
    )

    assert [position.etf_id for position in result.positions] == [1]


def test_historical_signal_generation_rejects_missing_listing_metadata() -> None:
    config = validate_strategy_config(
        {
            "strategy_id": "equal_weight",
            "version": "v1",
            "type": "equal_weight",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {},
            "costs": {"transaction_cost_bps": 5},
            "performance": {"risk_free_rate": 0.02},
        }
    )
    missing = _etf_for_resolved_panel(1, "510300", date(2026, 1, 2))
    missing.listing_date = None

    with pytest.raises(ValueError, match="missing listing_date.*510300"):
        generate_historical_strategy_signals(
            historical_trading_dates=[date(2026, 1, 2)],
            config=config,
            price_panel={},
            active_etfs=[missing],
        )


def test_generate_historical_strategy_signals_uses_configured_rebalance_frequency() -> None:
    weekly_config = _strategy_config(top_n=1).model_copy(
        update={"rebalance": RebalanceConfig(frequency="weekly")}
    )
    monthly_config = _strategy_config(top_n=1).model_copy(
        update={"rebalance": RebalanceConfig(frequency="monthly")}
    )

    trading_dates = [_trade_date(offset) for offset in range(0, 130)]

    session_factory = _create_session_factory()

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"), end_offset=130)
        _add_price_history(session, etf_id=second.id, current_price=Decimal("160"), end_offset=130)

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(130),
        )

        weekly_results = generate_historical_strategy_signals(
            historical_trading_dates=trading_dates,
            config=weekly_config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=None,
        )
        weekly_count = len(weekly_results)

        monthly_results = generate_historical_strategy_signals(
            historical_trading_dates=trading_dates,
            config=monthly_config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            persist=None,
        )
        monthly_signal_dates = [result.signal_date for result in monthly_results]

    # Precondition: ensure trading dates span at least 4 months so monthly < weekly is meaningful
    months_in_range = {(d.year, d.month) for d in trading_dates}
    assert len(months_in_range) >= 4

    assert weekly_count > 0
    assert len(monthly_signal_dates) < weekly_count
    assert monthly_signal_dates == sorted(monthly_signal_dates)
    # Each monthly signal date must be the last available trading date of its calendar month
    last_per_month = {(d.year, d.month): d for d in sorted(set(trading_dates))}
    last_per_month_by_key = last_per_month
    for signal_date in monthly_signal_dates:
        assert signal_date == last_per_month_by_key[(signal_date.year, signal_date.month)]


def test_generate_strategy_signal_performs_zero_market_price_queries() -> None:
    """Performance guard: signal generation must not touch MarketPrice."""
    session_factory = _create_session_factory()
    config = _strategy_config(top_n=1)

    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        _add_price_history(session, etf_id=first.id, current_price=Decimal("180"))

        active_etfs = list(session.scalars(_select_etfs().order_by(ETFInfo.id)))
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=_trade_date(120),
        )

        original_scalars = session.scalars

        def counting_scalars(stmt: object, *args: object, **kwargs: object) -> object:
            from sqlalchemy.sql.elements import ClauseElement

            compiled_sql = (
                str(stmt.compile(compile_kwargs={"literal_binds": True}))
                if isinstance(stmt, ClauseElement)
                else ""
            )
            if "market_price" in compiled_sql.lower():
                raise AssertionError(
                    "generate_strategy_signal must not query market_price directly; "
                    f"got statement: {compiled_sql}"
                )
            return original_scalars(stmt, *args, **kwargs)

        session.scalars = counting_scalars  # type: ignore[method-assign]

        try:
            generate_strategy_signal(
                signal_date=_trade_date(120),
                config=config,
                price_panel=price_panel,
                active_etfs=active_etfs,
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                persist=None,
            )
        finally:
            session.scalars = original_scalars  # type: ignore[method-assign]


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _select_etfs() -> object:
    from sqlalchemy import select as _select

    return _select(ETFInfo).where(ETFInfo.is_active.is_(True))


def _select_signals() -> object:
    from sqlalchemy import select as _select

    return _select(StrategySignal)


def _select_positions() -> object:
    from sqlalchemy import select as _select

    return _select(StrategySignalPosition)


def _add_etf(session: Session, *, exchange: str, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange=exchange,
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="CNY",
        listing_date=date(2026, 1, 1),
    )
    session.add(etf)
    session.flush()
    return etf


def _etf_for_resolved_panel(etf_id: int, symbol: str, listing_date: date) -> ETFInfo:
    return ETFInfo(
        id=etf_id,
        exchange="SSE",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="CNY",
        listing_date=listing_date,
        is_active=True,
    )


def _resolved_signal_point(
    etf_id: int,
    trade_date: date,
    value: str,
    *,
    tradable: bool = True,
    resolution: str = "market_price",
) -> ResolvedSessionPrice:
    adjusted_value = Decimal(value)
    return ResolvedSessionPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        adjusted_value=adjusted_value,
        raw_close=adjusted_value if tradable else None,
        raw_factor=Decimal("1") if tradable else None,
        tradable=tradable,
        resolution=resolution,
    )


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
        factor_hfq=Decimal("1"),
        volume=1000,
    )


def _strategy_config(*, top_n: int) -> StrategyConfig:
    config: dict[str, Any] = {
        "strategy_id": "dual_momentum",
        "version": "v1",
        "type": "dual_momentum",
        "universe_config": "config/etf_pool.yaml",
        "parameters": {
            "momentum": {"short_window_days": 63, "long_window_days": 120},
            "score_weights": {"short": 0.4, "long": 0.6},
            "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
            "selection": {"top_n": top_n},
            "defense": {"assets": [{"exchange": "SSE", "symbol": "511010"}]},
        },
        "costs": {
            "transaction_cost_bps": 5,
        },
        "performance": {
            "risk_free_rate": 0.02,
        },
    }
    return validate_strategy_config(config)
