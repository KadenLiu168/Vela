from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import vela_core.backtest_runner as runner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import BacktestGapDetectionConfig, BacktestRunResult, run_backtest
from vela_core.database import managed_session
from vela_core.models import (
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
    StrategySharpeRatio,
    StrategyVolatility,
)
from vela_core.strategy_signal_generation import GenerateStrategySignalResult


def test_run_backtest_persists_metrics_and_normalized_curve_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)

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
        '"risk_free_rate": 0.02, "start_date": "2026-01-01", '
        '"strategy_id": "dual_momentum", "type": "dual_momentum"}'
    )
    assert [row.trade_date for row in curve_rows] == [date(2026, 1, 1), date(2026, 1, 3)]
    assert curve_rows[0].cash == Decimal("0.000000")
    assert curve_rows[0].market_value == Decimal("1.000000")
    assert curve_rows[0].total_assets == Decimal("1.000000")
    assert curve_rows[0].positions_json == '[{"etf_id": 1, "target_weight": "1.000000"}]'
    assert curve_rows[1].net_value == Decimal("1.100000")
    assert len(signals) == 1
    assert signals[0].source == "backtest"
    assert signals[0].backtest_run_id == run.id


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


def test_run_backtest_uses_distinct_ordered_local_market_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()
    captured_dates: list[date] = []

    with session_factory() as session:
        first = _add_etf(session, symbol="AAA")
        second = _add_etf(session, symbol="BBB")
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 3), close_price=100)
        _add_price(session, etf_id=second.id, trade_date=date(2026, 1, 3), close_price=100)
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 1), close_price=100)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=first.id, captured_dates=captured_dates)

        run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )

    assert captured_dates == [date(2026, 1, 1), date(2026, 1, 3)]


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


def test_run_backtest_fails_without_local_market_dates() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="No local market prices"):
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


@pytest.mark.parametrize(("lookback_days", "calendar_buffer_days"), [(0, 10), (126, 262)])
def test_run_backtest_sizes_price_panel_from_resolved_strategy_lookback(
    monkeypatch: pytest.MonkeyPatch,
    lookback_days: int,
    calendar_buffer_days: int,
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

        run_backtest(
            session,
            config=_strategy_config(),
            start_date=signal_date,
            end_date=signal_date,
        )

    assert captured_start_dates == [signal_date - timedelta(days=calendar_buffer_days)]


def test_backtest_runner_has_no_concrete_strategy_dependency() -> None:
    source = runner.__file__
    assert source is not None
    contents = Path(source).read_text(encoding="utf-8")

    assert "strategies.dual_momentum" not in contents
    assert "strategies.equal_weight" not in contents
    assert 'config.type == "' not in contents


def _patch_runner_helpers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    etf_id: int,
    holdings: list[PortfolioHolding] | None = None,
    captured_dates: list[date] | None = None,
    signal_status: str = "success",
    return_missing_id: bool = False,
) -> None:
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
    ) -> list[StrategyEquityCurvePoint]:
        return [
            StrategyEquityCurvePoint(
                trade_date=trading_dates[0],
                net_value=Decimal("1.000000"),
                daily_return=Decimal("0.000000"),
            ),
            StrategyEquityCurvePoint(
                trade_date=trading_dates[-1],
                net_value=Decimal("1.100000"),
                daily_return=Decimal("0.100000"),
            ),
        ][: len(trading_dates)]

    def fake_calculate_portfolio_holdings(
        session: Session,
        *,
        trading_dates: list[date],
        strategy_id: str,
        config_version: str,
    ) -> list[PortfolioHoldingSnapshot]:
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
    monkeypatch.setattr(runner, "calculate_portfolio_holdings", fake_calculate_portfolio_holdings)
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
    monkeypatch.setattr(
        runner,
        "calculate_strategy_sharpe_ratio",
        lambda annualized_return, volatility, *, risk_free_rate: StrategySharpeRatio(
            sharpe_ratio=Decimal("1.000000")
        ),
    )


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


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


def test_run_backtest_warns_about_systematic_gap_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        _add_calendar(session, date(2026, 1, 1))
        _add_calendar(session, date(2026, 1, 2))
        _add_calendar(session, date(2026, 1, 3))
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )
        session.commit()

    assert result.status == "success"


def test_run_backtest_strict_raises_when_systematic_gaps_exceed_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        _add_calendar(session, date(2026, 1, 1))
        _add_calendar(session, date(2026, 1, 2))
        _add_calendar(session, date(2026, 1, 3))
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)

        with pytest.raises(ValueError, match="Strict data-quality check failed"):
            run_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 3),
                gap_detection=BacktestGapDetectionConfig(strict=True, max_systematic_gaps=0),
            )

        assert session.query(BacktestRun).count() == 0


def test_run_backtest_strict_tolerates_gaps_within_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        _add_calendar(session, date(2026, 1, 1))
        _add_calendar(session, date(2026, 1, 2))
        _add_calendar(session, date(2026, 1, 3))
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            gap_detection=BacktestGapDetectionConfig(strict=True, max_systematic_gaps=5),
        )
        session.commit()

    assert result.status == "success"


def test_run_backtest_strict_never_fails_on_per_etf_gaps_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first = _add_etf(session, symbol="AAA")
        second = _add_etf(session, symbol="BBB")
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 2), close_price=100)
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 3), close_price=100)
        _add_price(session, etf_id=second.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=second.id, trade_date=date(2026, 1, 3), close_price=100)
        _add_calendar(session, date(2026, 1, 1))
        _add_calendar(session, date(2026, 1, 2))
        _add_calendar(session, date(2026, 1, 3))
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=first.id, holdings=[])

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            gap_detection=BacktestGapDetectionConfig(strict=True, max_systematic_gaps=0),
        )
        session.commit()

    assert result.status == "success"


def test_run_backtest_warns_and_proceeds_when_calendar_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)

        result = run_backtest(
            session,
            config=_strategy_config(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )
        session.commit()

    assert result.status == "success"


def test_run_backtest_strict_refuses_without_calendar(monkeypatch: pytest.MonkeyPatch) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=110)
        session.commit()
        _patch_runner_helpers(monkeypatch, etf_id=etf.id)

        with pytest.raises(ValueError, match="synced trading calendar"):
            run_backtest(
                session,
                config=_strategy_config(),
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 3),
                gap_detection=BacktestGapDetectionConfig(strict=True, max_systematic_gaps=5),
            )

        assert session.query(BacktestRun).count() == 0
