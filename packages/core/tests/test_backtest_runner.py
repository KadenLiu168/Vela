import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import vela_core.backtest_runner as runner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import BacktestRunResult
from vela_core import run_backtest as run_core_backtest
from vela_core.database import managed_session
from vela_core.models import (
    BacktestBenchmark,
    BacktestBenchmarkEquityCurve,
    BacktestEquityCurve,
    BacktestRun,
    Base,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    TradingCalendar,
)
from vela_core.portfolio_holdings import PortfolioHolding, PortfolioHoldingSnapshot
from vela_core.strategy_config import StrategyConfig, validate_strategy_config
from vela_core.strategy_equity_curve import (
    StrategyAnnualizedReturn,
    StrategyEquityCurvePoint,
    StrategyMaximumDrawdown,
    StrategyPortfolioPosition,
    StrategyPortfolioState,
    StrategySharpeRatio,
    StrategyVolatility,
)
from vela_core.strategy_signal_generation import GenerateStrategySignalResult


def run_backtest(*args: Any, **kwargs: Any) -> BacktestRunResult:
    return run_core_backtest(*args, calculate_benchmarks=False, **kwargs)


def test_run_backtest_persists_metrics_and_normalized_curve_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    captured_sharpe_calls: list[tuple[list[StrategyEquityCurvePoint], Decimal]] = []

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id, sharpe_calls=captured_sharpe_calls)

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            started_at=datetime(2026, 1, 4, 9, 0, tzinfo=UTC),
        )
        session.commit()

        run = session.get(BacktestRun, result.backtest_run_id)
        curve_rows = (
            session.query(BacktestEquityCurve).order_by(BacktestEquityCurve.trade_date).all()
        )
        signals = session.query(StrategySignal).all()

    assert result == BacktestRunResult(
        backtest_run_id=result.backtest_run_id,
        status="success",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        trading_day_count=2,
        signal_count=1,
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.200000"),
        max_drawdown=Decimal("-0.050000"),
        sharpe_ratio=Decimal("1.000000"),
        volatility=Decimal("0.180000"),
    )
    assert run is not None
    assert run.strategy_id == "dual_momentum"
    assert run.parameters_json == (
        '{"config_version": "v1", "end_date": "2026-01-03", '
        '"equity_model_version": "drift_v1", '
        '"risk_free_rate": 0.02, "start_date": "2026-01-01", '
        '"strategy_id": "dual_momentum", "type": "dual_momentum"}'
    )
    assert [row.trade_date for row in curve_rows] == [date(2026, 1, 1), date(2026, 1, 3)]
    assert curve_rows[0].cash == Decimal("0.000000")
    assert curve_rows[0].market_value == Decimal("1.000000")
    assert curve_rows[0].total_assets == Decimal("1.000000")
    assert curve_rows[0].positions_json == (
        '[{"actual_weight": "1.000000", "etf_id": 1, "target_weight": "1.000000"}]'
    )
    assert curve_rows[1].net_value == Decimal("1.100000")
    assert len(signals) == 1
    assert signals[0].source == "backtest"
    assert signals[0].backtest_run_id == run.id
    assert captured_sharpe_calls == [
        (
            [
                StrategyEquityCurvePoint(
                    trade_date=date(2026, 1, 1),
                    net_value=Decimal("1.000000"),
                    daily_return=Decimal("0.000000"),
                ),
                StrategyEquityCurvePoint(
                    trade_date=date(2026, 1, 3),
                    net_value=Decimal("1.100000"),
                    daily_return=Decimal("0.100000"),
                ),
            ],
            Decimal("0.02"),
        )
    ]


def test_run_backtest_links_failed_generated_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id, signal_status="failed")

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
        )
        session.commit()
        signal = session.query(StrategySignal).one()

    assert result.status == "partial"
    assert signal.status == "failed"
    assert signal.source == "backtest"
    assert signal.backtest_run_id == result.backtest_run_id


def test_to_curve_inputs_persists_calculated_drifted_state_and_rejects_missing_state() -> None:
    point = StrategyEquityCurvePoint(
        trade_date=date(2026, 1, 2),
        net_value=Decimal("1.500000"),
        daily_return=Decimal("0.500000"),
        portfolio_state=StrategyPortfolioState(
            cash=Decimal("0.000000"),
            market_value=Decimal("1.500000"),
            total_assets=Decimal("1.500000"),
            positions=(
                StrategyPortfolioPosition(
                    etf_id=7,
                    target_weight=Decimal("0.500000"),
                    actual_weight=Decimal("0.666667"),
                ),
                StrategyPortfolioPosition(
                    etf_id=8,
                    target_weight=Decimal("0.500000"),
                    actual_weight=Decimal("0.333333"),
                ),
            ),
        ),
    )

    row = runner._to_curve_inputs([point])[0]

    assert row.cash + row.market_value == row.total_assets == point.net_value
    assert row.positions_json == (
        '[{"actual_weight": "0.666667", "etf_id": 7, "target_weight": "0.500000"}, '
        '{"actual_weight": "0.333333", "etf_id": 8, "target_weight": "0.500000"}]'
    )
    with pytest.raises(ValueError, match="missing calculated portfolio state"):
        runner._to_curve_inputs(
            [
                StrategyEquityCurvePoint(
                    trade_date=date(2026, 1, 2),
                    net_value=Decimal("1.000000"),
                    daily_return=Decimal("0.000000"),
                )
            ]
        )


def test_run_backtest_passes_generated_signal_ids_before_persistence_and_linking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    calculation_signal_ids: list[tuple[str, list[int] | None]] = []

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        _patch_runner_helpers(
            monkeypatch,
            etf_id=etf.id,
            calculation_signal_ids=calculation_signal_ids,
        )
        real_persist = runner.persist_backtest_result
        real_link = runner.link_signals_to_backtest_run

        def persist_after_calculations(*args: Any, **kwargs: Any) -> Any:
            assert calculation_signal_ids == [("curve", [1])]
            return real_persist(*args, **kwargs)

        def link_after_calculations(*args: Any, **kwargs: Any) -> Any:
            assert calculation_signal_ids == [("curve", [1])]
            return real_link(*args, **kwargs)

        monkeypatch.setattr(runner, "persist_backtest_result", persist_after_calculations)
        monkeypatch.setattr(runner, "link_signals_to_backtest_run", link_after_calculations)
        run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
        )

    assert calculation_signal_ids == [("curve", [1])]


def test_run_backtest_reruns_keep_signal_scopes_and_persisted_results_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    call_count = 0

    def fake_generate_historical_strategy_signals(
        *,
        config: StrategyConfig,
        generated_at: datetime,
        persist: Any,
        **_: Any,
    ) -> list[GenerateStrategySignalResult]:
        nonlocal call_count
        call_count += 1
        first_run = call_count == 1
        first_id = persist(
            signal_date=date(2026, 1, 1),
            generated_at=generated_at,
            status="success",
            result="rebalance",
            positions=[
                {
                    "etf_id": spy.id,
                    "rank": 1,
                    "score": Decimal("1"),
                    "target_weight": Decimal("1"),
                }
            ],
            error_message=None,
        )
        second_id = persist(
            signal_date=date(2026, 1, 2),
            generated_at=generated_at,
            status="success" if first_run else "failed",
            result="rebalance" if first_run else None,
            positions=(
                [
                    {
                        "etf_id": qqq.id,
                        "rank": 1,
                        "score": Decimal("1"),
                        "target_weight": Decimal("1"),
                    }
                ]
                if first_run
                else []
            ),
            error_message=None if first_run else "generation failed",
        )
        return [
            GenerateStrategySignalResult(
                strategy_signal_id=first_id,
                signal_date=date(2026, 1, 1),
                config_version=config.version,
                status="success",
                result="rebalance",
                error_message=None,
                positions=[],
            ),
            GenerateStrategySignalResult(
                strategy_signal_id=second_id,
                signal_date=date(2026, 1, 2),
                config_version=config.version,
                status="success" if first_run else "failed",
                result="rebalance" if first_run else None,
                error_message=None if first_run else "generation failed",
                positions=[],
            ),
        ]

    monkeypatch.setattr(
        runner,
        "generate_historical_strategy_signals",
        fake_generate_historical_strategy_signals,
    )
    monkeypatch.setattr(
        runner,
        "_load_trading_dates",
        lambda session, *, start_date, end_date: list(
            session.scalars(
                runner.select(MarketPrice.trade_date)
                .where(MarketPrice.trade_date >= start_date)
                .where(MarketPrice.trade_date <= end_date)
                .distinct()
                .order_by(MarketPrice.trade_date)
            )
        ),
    )
    monkeypatch.setattr(
        runner,
        "_load_required_trading_dates",
        lambda session, *, trading_dates, first_rebalance_date, lookback_days: trading_dates,
    )
    monkeypatch.setattr(runner, "_validate_required_prices", lambda **_kwargs: None)

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        for trade_date, spy_price, qqq_price in [
            (date(2026, 1, 1), 100, 100),
            (date(2026, 1, 2), 110, 90),
            (date(2026, 1, 3), 121, 81),
        ]:
            _add_price(session, etf_id=spy.id, trade_date=trade_date, close_price=spy_price)
            _add_price(session, etf_id=qqq.id, trade_date=trade_date, close_price=qqq_price)
        session.commit()

        first = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            started_at=datetime(2026, 1, 4, tzinfo=UTC),
        )
        session.commit()
        first_curve_before = [
            (row.trade_date, row.positions_json, row.net_value)
            for row in session.query(BacktestEquityCurve)
            .filter_by(backtest_run_id=first.backtest_run_id)
            .order_by(BacktestEquityCurve.trade_date)
        ]
        first_metrics_before = (
            session.get(BacktestRun, first.backtest_run_id).total_return,
            session.get(BacktestRun, first.backtest_run_id).annualized_return,
            session.get(BacktestRun, first.backtest_run_id).max_drawdown,
            session.get(BacktestRun, first.backtest_run_id).sharpe_ratio,
            session.get(BacktestRun, first.backtest_run_id).volatility,
        )

        second = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            started_at=datetime(2026, 1, 5, tzinfo=UTC),
        )
        session.commit()
        first_curve_after = [
            (row.trade_date, row.positions_json, row.net_value)
            for row in session.query(BacktestEquityCurve)
            .filter_by(backtest_run_id=first.backtest_run_id)
            .order_by(BacktestEquityCurve.trade_date)
        ]
        first_metrics_after = (
            session.get(BacktestRun, first.backtest_run_id).total_return,
            session.get(BacktestRun, first.backtest_run_id).annualized_return,
            session.get(BacktestRun, first.backtest_run_id).max_drawdown,
            session.get(BacktestRun, first.backtest_run_id).sharpe_ratio,
            session.get(BacktestRun, first.backtest_run_id).volatility,
        )
        second_final_row = (
            session.query(BacktestEquityCurve)
            .filter_by(backtest_run_id=second.backtest_run_id, trade_date=date(2026, 1, 3))
            .one()
        )
        second_snapshot = session.get(BacktestRun, second.backtest_run_id).data_snapshot_json
        run_signal_ids = {
            run_id: {
                signal.id
                for signal in session.query(StrategySignal).filter_by(backtest_run_id=run_id)
            }
            for run_id in [first.backtest_run_id, second.backtest_run_id]
        }

    assert second.status == "partial"
    assert second_final_row.positions_json == (
        '[{"actual_weight": "1.000000", "etf_id": '
        + str(spy.id)
        + ', "target_weight": "1.000000"}]'
    )
    assert first_curve_after == first_curve_before
    assert first_metrics_after == first_metrics_before
    assert run_signal_ids[first.backtest_run_id].isdisjoint(run_signal_ids[second.backtest_run_id])
    assert len(run_signal_ids[first.backtest_run_id]) == 2
    assert len(run_signal_ids[second.backtest_run_id]) == 2
    assert second_snapshot is not None


def test_run_backtest_missing_signal_id_rolls_back_all_persisted_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        etf_id = etf.id

    _patch_runner_helpers(monkeypatch, etf_id=etf_id, return_missing_id=True)

    with pytest.raises(ValueError, match="did not persist every signal"):
        with managed_session(session_factory) as session:
            run_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 1),
            )

    with session_factory() as session:
        assert session.query(BacktestRun).count() == 0
        assert session.query(BacktestEquityCurve).count() == 0
        assert session.query(StrategySignal).count() == 0


def test_load_trading_dates_uses_ordered_calendar_not_market_price_union() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=100)
        _add_calendar(session, date(2026, 1, 1))
        _add_calendar(session, date(2026, 1, 2))
        session.commit()

        trading_dates = runner._load_trading_dates(
            session,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )

    assert trading_dates == [date(2026, 1, 1), date(2026, 1, 2)]


def test_load_required_trading_dates_uses_exact_preceding_calendar_sessions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        for trade_date in [
            date(2025, 12, 30),
            date(2025, 12, 31),
            date(2026, 1, 2),
            date(2026, 1, 5),
        ]:
            _add_calendar(session, trade_date)
        session.commit()

        required_dates = runner._load_required_trading_dates(
            session,
            trading_dates=[date(2026, 1, 2), date(2026, 1, 5)],
            first_rebalance_date=date(2026, 1, 2),
            lookback_days=1,
        )

    assert required_dates == [date(2025, 12, 31), date(2026, 1, 2), date(2026, 1, 5)]


def test_load_required_trading_dates_does_not_require_history_before_requested_sessions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        for trade_date in [
            date(2025, 12, 30),
            date(2025, 12, 31),
            date(2026, 1, 2),
            date(2026, 1, 5),
        ]:
            _add_calendar(session, trade_date)
        session.commit()

        required_dates = runner._load_required_trading_dates(
            session,
            trading_dates=[date(2026, 1, 2), date(2026, 1, 5)],
            first_rebalance_date=date(2026, 1, 5),
            lookback_days=1,
        )

    assert required_dates == [date(2026, 1, 2), date(2026, 1, 5)]


def test_load_required_trading_dates_rejects_insufficient_calendar_lookback() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        _add_calendar(session, date(2026, 1, 2))
        session.commit()

        with pytest.raises(ValueError, match="requires 1 preceding official session"):
            runner._load_required_trading_dates(
                session,
                trading_dates=[date(2026, 1, 2)],
                first_rebalance_date=date(2026, 1, 2),
                lookback_days=1,
            )


def test_run_backtest_rejects_required_price_gap_before_any_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    class ZeroLookbackStrategy:
        def lookback_days(self) -> int:
            return 0

    with session_factory() as session:
        complete = _add_etf(session, symbol="AAA")
        missing = _add_etf(session, symbol="BBB")
        for trade_date in [date(2026, 1, 1), date(2026, 1, 2)]:
            _add_calendar(session, trade_date)
            _add_price(session, etf_id=complete.id, trade_date=trade_date, close_price=100)
        _add_price(session, etf_id=missing.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        monkeypatch.setattr(runner, "resolve_strategy", lambda config: ZeroLookbackStrategy())

        with pytest.raises(ValueError, match=r"ETF 2 on 2026-01-02"):
            run_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 2),
            )

        assert session.query(StrategySignal).count() == 0
        assert session.query(BacktestRun).count() == 0
        assert session.query(BacktestEquityCurve).count() == 0


def test_run_backtest_rejects_missing_csi_price_before_any_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    class ZeroLookbackStrategy:
        def lookback_days(self) -> int:
            return 0

    with session_factory() as session:
        csi = ETFInfo(
            exchange="SSE",
            symbol="510300",
            name="CSI 300 ETF",
            currency="CNY",
        )
        other = ETFInfo(
            exchange="SSE",
            symbol="510500",
            name="CSI 500 ETF",
            currency="CNY",
        )
        session.add_all([csi, other])
        session.flush()
        for trade_date in [date(2026, 1, 1), date(2026, 1, 2)]:
            _add_calendar(session, trade_date)
            _add_price(session, etf_id=other.id, trade_date=trade_date, close_price=100)
        _add_price(session, etf_id=csi.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        monkeypatch.setattr(runner, "resolve_strategy", lambda config: ZeroLookbackStrategy())

        with pytest.raises(ValueError, match=r"SSE:510300 on 2026-01-02"):
            run_core_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 2),
            )

        assert session.query(StrategySignal).count() == 0
        assert session.query(BacktestRun).count() == 0
        assert session.query(BacktestEquityCurve).count() == 0
        assert session.query(BacktestBenchmark).count() == 0
        assert session.query(BacktestBenchmarkEquityCurve).count() == 0


def test_validate_required_prices_applies_inception_boundary_without_first_price_exemption() -> (
    None
):
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        etf.inception_date = date(2026, 1, 2)
        session.flush()
        price_panel = {
            etf.id: [
                _price_row(
                    etf_id=etf.id,
                    trade_date=date(2026, 1, 2),
                    close_price=Decimal("100"),
                    factor_hfq=Decimal("1"),
                )
            ]
        }

        runner._validate_required_prices(
            active_etfs=[etf],
            required_dates=[date(2026, 1, 1), date(2026, 1, 2)],
            price_panel=price_panel,
        )

        etf.inception_date = None
        with pytest.raises(ValueError, match="2026-01-01"):
            runner._validate_required_prices(
                active_etfs=[etf],
                required_dates=[date(2026, 1, 1), date(2026, 1, 2)],
                price_panel=price_panel,
            )


def test_run_backtest_persists_empty_holdings_as_cash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id, holdings=[])

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
        )
        session.commit()

        row = (
            session.query(BacktestEquityCurve)
            .filter_by(backtest_run_id=result.backtest_run_id)
            .one()
        )

    assert row.cash == Decimal("1.000000")
    assert row.market_value == Decimal("0.000000")
    assert row.positions_json == "[]"


def test_run_backtest_fails_without_requested_trading_calendar_sessions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="Trading calendar has no official sessions"):
            run_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 3),
            )

        assert session.query(BacktestRun).count() == 0


def test_run_backtest_rejects_negative_strategy_lookback_before_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    class NegativeLookbackStrategy:
        def lookback_days(self) -> int:
            return -1

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_calendar(session, date(2026, 1, 1))
        session.commit()
        monkeypatch.setattr(runner, "resolve_strategy", lambda config: NegativeLookbackStrategy())

        with pytest.raises(ValueError, match="lookback_days must be non-negative"):
            run_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 1),
            )

        assert session.query(BacktestRun).count() == 0


@pytest.mark.parametrize("lookback_days", [0, 126])
def test_run_backtest_loads_price_panel_from_exact_required_session_start(
    monkeypatch: pytest.MonkeyPatch,
    lookback_days: int,
) -> None:
    session_factory = _create_session_factory()
    captured_start_dates: list[date] = []

    class StrategyWithLookback:
        def lookback_days(self) -> int:
            return lookback_days

    def fake_load_price_panel(session: Session, **kwargs: Any) -> dict[int, list[Any]]:
        del session
        captured_start_dates.append(kwargs["start_date"])
        return {}

    with session_factory() as session:
        etf = _add_etf(session)
        signal_date = date(2026, 6, 15)
        _add_price(session, etf_id=etf.id, trade_date=signal_date, close_price=100)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)
        monkeypatch.setattr(runner, "resolve_strategy", lambda config: StrategyWithLookback())
        monkeypatch.setattr(runner, "load_price_panel", fake_load_price_panel)
        required_start = signal_date - timedelta(days=lookback_days)
        monkeypatch.setattr(
            runner,
            "_load_required_trading_dates",
            lambda session, *, trading_dates, first_rebalance_date, lookback_days: (
                [required_start, *trading_dates] if lookback_days else trading_dates
            ),
        )

        run_backtest(
            session,
            config=_strategy_config(),
            start_date=signal_date,
            end_date=signal_date,
        )

    assert captured_start_dates == [signal_date - timedelta(days=lookback_days)]


def test_backtest_runner_has_no_concrete_strategy_dependency() -> None:
    source = runner.__file__
    assert source is not None
    contents = Path(source).read_text(encoding="utf-8")

    assert "strategies.dual_momentum" not in contents
    assert "strategies.equal_weight" not in contents
    assert 'config.type == "' not in contents


def test_build_data_snapshot_is_deterministic_and_detects_row_changes() -> None:
    first = _price_row(
        etf_id=2,
        trade_date=date(2026, 1, 2),
        close_price=Decimal("12.34"),
        factor_hfq=Decimal("1.25"),
    )
    second = _price_row(
        etf_id=1,
        trade_date=date(2026, 1, 1),
        close_price=Decimal("10"),
        factor_hfq=Decimal("1"),
    )
    third = _price_row(
        etf_id=2,
        trade_date=date(2026, 1, 1),
        close_price=Decimal("11"),
        factor_hfq=Decimal("1.2"),
    )
    unchanged = runner.build_data_snapshot({2: [first, third], 1: [second]})

    assert unchanged == runner.build_data_snapshot({1: [second], 2: [first, third]})
    assert unchanged == runner.build_data_snapshot({2: [third, first], 1: [second]})
    assert unchanged["min_trade_date"] == "2026-01-01"
    assert unchanged["max_trade_date"] == "2026-01-02"
    assert unchanged["trading_day_count"] == 2
    assert unchanged["active_etf_count"] == 2
    assert unchanged["per_etf_row_counts"] == {"1": 1, "2": 2}

    changed_close = _price_row(
        etf_id=2,
        trade_date=date(2026, 1, 2),
        close_price=Decimal("12.35"),
        factor_hfq=Decimal("1.25"),
    )
    changed_factor = _price_row(
        etf_id=2,
        trade_date=date(2026, 1, 2),
        close_price=Decimal("12.34"),
        factor_hfq=Decimal("1.26"),
    )

    changed_close_checksum = runner.build_data_snapshot({2: [changed_close, third], 1: [second]})[
        "data_checksum"
    ]
    changed_factor_checksum = runner.build_data_snapshot({2: [changed_factor, third], 1: [second]})[
        "data_checksum"
    ]

    assert unchanged["data_checksum"] != changed_close_checksum
    assert unchanged["data_checksum"] != changed_factor_checksum


def test_build_data_snapshot_checksum_matches_canonical_byte_protocol() -> None:
    first = _price_row(
        etf_id=2,
        trade_date=date(2026, 1, 2),
        close_price=Decimal("12.34"),
        factor_hfq=Decimal("1.25"),
    )
    second = _price_row(
        etf_id=1,
        trade_date=date(2026, 1, 1),
        close_price=Decimal("10"),
        factor_hfq=Decimal("1"),
    )

    snapshot = runner.build_data_snapshot({2: [first], 1: [second]})

    assert snapshot["data_checksum"] == (
        "73171e60a67823b72d721505311588360b2e42f5cfb4fd988ee3a08e740661c6"
    )


def test_build_data_snapshot_uses_structured_rows_and_handles_empty_panel() -> None:
    empty_snapshot = runner.build_data_snapshot({})
    first = _price_row(
        etf_id=1,
        trade_date=date(2026, 1, 1),
        close_price=Decimal("2"),
        factor_hfq=Decimal("34"),
    )
    second = _price_row(
        etf_id=1,
        trade_date=date(2026, 1, 1),
        close_price=Decimal("23"),
        factor_hfq=Decimal("4"),
    )

    assert empty_snapshot == {
        "min_trade_date": None,
        "max_trade_date": None,
        "trading_day_count": 0,
        "active_etf_count": 0,
        "per_etf_row_counts": {},
        "data_checksum": hashlib.sha256().hexdigest(),
    }
    assert (
        runner.build_data_snapshot({1: [first]})["data_checksum"]
        != runner.build_data_snapshot({1: [second]})["data_checksum"]
    )
    single_snapshot = runner.build_data_snapshot({1: [first]})
    assert json.loads(json.dumps(single_snapshot))["per_etf_row_counts"] == {"1": 1}
    assert single_snapshot["min_trade_date"] == "2026-01-01"
    assert single_snapshot["max_trade_date"] == "2026-01-01"
    assert single_snapshot["trading_day_count"] == 1
    assert single_snapshot["active_etf_count"] == 1


def test_build_data_snapshot_uses_global_trade_date_bounds() -> None:
    late_low_id = _price_row(
        etf_id=1,
        trade_date=date(2026, 1, 3),
        close_price=Decimal("10"),
        factor_hfq=Decimal("1"),
    )
    early_high_id = _price_row(
        etf_id=2,
        trade_date=date(2026, 1, 1),
        close_price=Decimal("10"),
        factor_hfq=Decimal("1"),
    )

    snapshot = runner.build_data_snapshot({1: [late_low_id], 2: [early_high_id]})

    assert snapshot["min_trade_date"] == "2026-01-01"
    assert snapshot["max_trade_date"] == "2026-01-03"


def test_run_backtest_snapshots_full_panel_without_future_signal_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    captured_panels: list[dict[int, list[Any]]] = []
    captured_curve_panels: list[dict[int, list[Any]]] = []

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 2), close_price=101)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=102)
        session.commit()
        _patch_runner_helpers(
            monkeypatch,
            etf_id=etf.id,
            captured_panels=captured_panels,
            captured_curve_panels=captured_curve_panels,
        )

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )
        run = session.get(BacktestRun, result.backtest_run_id)
        assert session.in_transaction() is True

    assert run is not None
    assert run.data_snapshot_json is not None
    assert run.data_snapshot_json["max_trade_date"] == "2026-01-03"
    assert run.data_snapshot_json["per_etf_row_counts"] == {str(etf.id): 3}
    assert [price.trade_date for price in captured_panels[0][etf.id]] == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]
    assert captured_curve_panels == captured_panels


def _price_row(
    *, etf_id: int, trade_date: date, close_price: Decimal, factor_hfq: Decimal
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        close_price=close_price,
        factor_hfq=factor_hfq,
    )


def _patch_runner_helpers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    etf_id: int,
    holdings: list[PortfolioHolding] | None = None,
    captured_dates: list[date] | None = None,
    signal_status: str = "success",
    return_missing_id: bool = False,
    sharpe_calls: list[tuple[list[StrategyEquityCurvePoint], Decimal]] | None = None,
    calculation_signal_ids: list[tuple[str, list[int] | None]] | None = None,
    captured_panels: list[dict[int, list[Any]]] | None = None,
    captured_curve_panels: list[dict[int, list[Any]]] | None = None,
) -> None:
    monkeypatch.setattr(
        runner,
        "_load_trading_dates",
        lambda session, *, start_date, end_date: list(
            session.scalars(
                runner.select(MarketPrice.trade_date)
                .where(MarketPrice.trade_date >= start_date)
                .where(MarketPrice.trade_date <= end_date)
                .distinct()
                .order_by(MarketPrice.trade_date)
            )
        ),
    )
    monkeypatch.setattr(
        runner,
        "_load_required_trading_dates",
        lambda session, *, trading_dates, first_rebalance_date, lookback_days: trading_dates,
    )
    monkeypatch.setattr(runner, "_validate_required_prices", lambda **_kwargs: None)

    def fake_generate_historical_strategy_signals(
        *,
        historical_trading_dates: Iterable[date],
        config: StrategyConfig,
        price_panel: dict[int, list[Any]] | None = None,
        active_etfs: list[Any] | None = None,
        generated_at: datetime | None = None,
        persist: Any = None,
    ) -> list[GenerateStrategySignalResult]:
        dates = list(historical_trading_dates)
        if captured_panels is not None:
            captured_panels.append(price_panel or {})
        if captured_dates is not None:
            captured_dates.extend(dates)
        signal_id = (
            persist(
                signal_date=dates[0],
                generated_at=generated_at or datetime.now(UTC),
                status=signal_status,
                result="rebalance" if signal_status == "success" else None,
                positions=[],
                error_message=None if signal_status == "success" else "generation failed",
            )
            if persist is not None
            else 1
        )
        return [
            GenerateStrategySignalResult(
                strategy_signal_id=None if return_missing_id else signal_id,
                signal_date=dates[0],
                config_version=config.version,
                status=signal_status,
                result="rebalance" if signal_status == "success" else None,
                error_message=None if signal_status == "success" else "generation failed",
                positions=[],
            )
        ]

    def fake_calculate_strategy_equity_curve(
        session: Session,
        *,
        trading_dates: list[date],
        strategy_config: StrategyConfig,
        signal_ids: list[int] | None = None,
        price_panel: dict[int, list[Any]] | None = None,
    ) -> list[StrategyEquityCurvePoint]:
        if captured_curve_panels is not None:
            captured_curve_panels.append(price_panel or {})
        if calculation_signal_ids is not None:
            calculation_signal_ids.append(("curve", signal_ids))
        has_holdings = holdings != []
        first_state = _portfolio_state(
            etf_id,
            Decimal("1.000000"),
            has_holdings=has_holdings,
        )
        last_state = _portfolio_state(
            etf_id,
            Decimal("1.100000"),
            has_holdings=has_holdings,
        )
        return [
            StrategyEquityCurvePoint(
                trade_date=trading_dates[0],
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
                portfolio_state=first_state,
            ),
            StrategyEquityCurvePoint(
                trade_date=trading_dates[-1],
                net_value=Decimal("1.100000"),
                daily_return=Decimal("0.100000"),
                portfolio_state=last_state,
            ),
        ][: len(trading_dates)]

    def fake_calculate_portfolio_holdings(
        session: Session,
        *,
        trading_dates: list[date],
        strategy_id: str,
        config_version: str,
        signal_ids: list[int] | None = None,
    ) -> list[PortfolioHoldingSnapshot]:
        if calculation_signal_ids is not None:
            calculation_signal_ids.append(("holdings", signal_ids))
        snapshot_holdings = (
            [PortfolioHolding(etf_id=etf_id, target_weight=Decimal("1.000000"))]
            if holdings is None
            else holdings
        )
        return [
            PortfolioHoldingSnapshot(
                trade_date=trade_date,
                signal_date=trading_dates[0],
                strategy_signal_id=1,
                holdings=snapshot_holdings,
            )
            for trade_date in trading_dates
        ]

    monkeypatch.setattr(
        runner,
        "generate_historical_strategy_signals",
        fake_generate_historical_strategy_signals,
    )
    monkeypatch.setattr(
        runner,
        "calculate_strategy_equity_curve",
        fake_calculate_strategy_equity_curve,
    )
    monkeypatch.setattr(
        runner,
        "calculate_strategy_annualized_return",
        lambda points: StrategyAnnualizedReturn(
            total_return=Decimal("0.100000"),
            annualized_return=Decimal("0.200000"),
        ),
    )
    monkeypatch.setattr(
        runner,
        "calculate_strategy_maximum_drawdown",
        lambda points: StrategyMaximumDrawdown(
            max_drawdown=Decimal("-0.050000"),
            peak_date=date(2026, 1, 1),
            trough_date=date(2026, 1, 3),
        ),
    )
    monkeypatch.setattr(
        runner,
        "calculate_strategy_volatility",
        lambda points: StrategyVolatility(volatility=Decimal("0.180000")),
    )

    def fake_calculate_strategy_sharpe_ratio(
        points: list[StrategyEquityCurvePoint],
        *,
        risk_free_rate: Decimal,
    ) -> StrategySharpeRatio:
        if sharpe_calls is not None:
            sharpe_calls.append((list(points), risk_free_rate))
        return StrategySharpeRatio(sharpe_ratio=Decimal("1.000000"))

    monkeypatch.setattr(
        runner,
        "calculate_strategy_sharpe_ratio",
        fake_calculate_strategy_sharpe_ratio,
    )


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _portfolio_state(
    etf_id: int,
    total_assets: Decimal,
    *,
    has_holdings: bool,
) -> StrategyPortfolioState:
    if not has_holdings:
        return StrategyPortfolioState(
            cash=total_assets,
            market_value=Decimal("0.000000"),
            total_assets=total_assets,
            positions=(),
        )
    return StrategyPortfolioState(
        cash=Decimal("0.000000"),
        market_value=total_assets,
        total_assets=total_assets,
        positions=(
            StrategyPortfolioPosition(
                etf_id=etf_id,
                target_weight=Decimal("1.000000"),
                actual_weight=Decimal("1.000000"),
            ),
        ),
    )


def _strategy_config() -> StrategyConfig:
    return validate_strategy_config(
        {
            "strategy_id": "dual_momentum",
            "version": "v1",
            "type": "dual_momentum",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {
                "momentum": {"short_window_days": 63, "long_window_days": 126},
                "score_weights": {"short": 0.4, "long": 0.6},
                "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                "selection": {"top_n": 2},
                "defense": {
                    "assets": [
                        {"exchange": "SSE", "symbol": "511010"},
                        {"exchange": "SSE", "symbol": "511880"},
                        {"exchange": "SSE", "symbol": "518880"},
                    ]
                },
            },
            "costs": {"transaction_cost_bps": 5},
            "performance": {"risk_free_rate": 0.02},
        }
    )


def _add_etf(session: Session, symbol: str = "SPY") -> ETFInfo:
    etf = ETFInfo(exchange="NYSEARCA", symbol=symbol, name=f"{symbol} ETF", currency="USD")
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


def _add_calendar(session: Session, trade_date: date) -> None:
    session.add(TradingCalendar(trade_date=trade_date, source="akshare"))
