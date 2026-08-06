import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import (
    BacktestBenchmark,
    BacktestBenchmarkEquityCurve,
    BacktestEquityCurve,
    BacktestRun,
)
from vela_core.return_stability import (
    BacktestReturnStability,
    BacktestReturnStabilityBenchmark,
    ReturnStabilitySourcePoint,
    derive_return_stability,
)


@dataclass(frozen=True)
class BacktestResultRunInput:
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    parameters_json: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    error_message: str | None = None
    total_return: Decimal | None = None
    annualized_return: Decimal | None = None
    max_drawdown: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    volatility: Decimal | None = None
    data_snapshot_json: dict[str, object] | None = None
    sortino_ratio: Decimal | None = None
    calmar_ratio: Decimal | None = None
    longest_drawdown_duration_sessions: int | None = None
    longest_drawdown_peak_date: date | None = None
    longest_drawdown_trough_date: date | None = None
    longest_drawdown_recovery_date: date | None = None


@dataclass(frozen=True)
class BacktestEquityCurveInput:
    trade_date: date
    net_value: Decimal
    cash: Decimal
    market_value: Decimal
    total_assets: Decimal
    positions_json: str


@dataclass(frozen=True)
class BacktestBenchmarkInput:
    key: str
    name: str
    total_return: Decimal | None
    annualized_return: Decimal | None
    max_drawdown: Decimal | None
    sharpe_ratio: Decimal | None
    volatility: Decimal | None
    equity_curve: Sequence[tuple[date, Decimal]]
    sortino_ratio: Decimal | None = None
    calmar_ratio: Decimal | None = None
    longest_drawdown_duration_sessions: int | None = None
    longest_drawdown_peak_date: date | None = None
    longest_drawdown_trough_date: date | None = None
    longest_drawdown_recovery_date: date | None = None
    tracking_error: Decimal | None = None
    information_ratio: Decimal | None = None
    capm_alpha: Decimal | None = None
    capm_beta: Decimal | None = None
    capm_r_squared: Decimal | None = None
    capm_observation_count: int | None = None
    up_capture_ratio: Decimal | None = None
    up_capture_observation_count: int | None = None
    down_capture_ratio: Decimal | None = None
    down_capture_observation_count: int | None = None


@dataclass(frozen=True)
class BacktestResultPersistenceResult:
    backtest_run: BacktestRun
    equity_curve: list[BacktestEquityCurve]


def persist_backtest_result(
    session: Session,
    *,
    run: BacktestResultRunInput,
    equity_curve: Sequence[BacktestEquityCurveInput],
    benchmarks: Sequence[BacktestBenchmarkInput] = (),
) -> BacktestResultPersistenceResult:
    keys = [item.key for item in benchmarks]
    if len(keys) != len(set(keys)):
        raise ValueError("Backtest benchmark keys must be unique")
    backtest_run = BacktestRun(
        strategy_id=run.strategy_id,
        config_version=run.config_version,
        start_date=run.start_date,
        end_date=run.end_date,
        parameters_json=run.parameters_json,
        data_snapshot_json=run.data_snapshot_json,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        error_message=run.error_message,
        total_return=run.total_return,
        annualized_return=run.annualized_return,
        max_drawdown=run.max_drawdown,
        sharpe_ratio=run.sharpe_ratio,
        volatility=run.volatility,
        sortino_ratio=run.sortino_ratio,
        calmar_ratio=run.calmar_ratio,
        longest_drawdown_duration_sessions=run.longest_drawdown_duration_sessions,
        longest_drawdown_peak_date=run.longest_drawdown_peak_date,
        longest_drawdown_trough_date=run.longest_drawdown_trough_date,
        longest_drawdown_recovery_date=run.longest_drawdown_recovery_date,
    )
    session.add(backtest_run)
    session.flush()

    curve_rows = [
        BacktestEquityCurve(
            backtest_run_id=backtest_run.id,
            trade_date=row.trade_date,
            net_value=row.net_value,
            cash=row.cash,
            market_value=row.market_value,
            total_assets=row.total_assets,
            positions_json=row.positions_json,
        )
        for row in equity_curve
    ]
    session.add_all(curve_rows)
    for input_row in benchmarks:
        benchmark = BacktestBenchmark(
            backtest_run_id=backtest_run.id,
            benchmark_key=input_row.key,
            display_name=input_row.name,
            total_return=input_row.total_return,
            annualized_return=input_row.annualized_return,
            max_drawdown=input_row.max_drawdown,
            sharpe_ratio=input_row.sharpe_ratio,
            volatility=input_row.volatility,
            sortino_ratio=input_row.sortino_ratio,
            calmar_ratio=input_row.calmar_ratio,
            longest_drawdown_duration_sessions=input_row.longest_drawdown_duration_sessions,
            longest_drawdown_peak_date=input_row.longest_drawdown_peak_date,
            longest_drawdown_trough_date=input_row.longest_drawdown_trough_date,
            longest_drawdown_recovery_date=input_row.longest_drawdown_recovery_date,
            tracking_error=input_row.tracking_error,
            information_ratio=input_row.information_ratio,
            capm_alpha=input_row.capm_alpha,
            capm_beta=input_row.capm_beta,
            capm_r_squared=input_row.capm_r_squared,
            capm_observation_count=input_row.capm_observation_count,
            up_capture_ratio=input_row.up_capture_ratio,
            up_capture_observation_count=input_row.up_capture_observation_count,
            down_capture_ratio=input_row.down_capture_ratio,
            down_capture_observation_count=input_row.down_capture_observation_count,
        )
        session.add(benchmark)
        session.flush()
        session.add_all(
            BacktestBenchmarkEquityCurve(
                benchmark_id=benchmark.id, trade_date=trade_date, net_value=net_value
            )
            for trade_date, net_value in input_row.equity_curve
        )
    session.flush()

    return BacktestResultPersistenceResult(
        backtest_run=backtest_run,
        equity_curve=curve_rows,
    )


def get_backtest_result(session: Session, *, run_id: int) -> BacktestRun | None:
    return session.scalar(
        select(BacktestRun)
        .options(
            selectinload(BacktestRun.equity_curve),
            selectinload(BacktestRun.signals),
            selectinload(BacktestRun.benchmarks).selectinload(BacktestBenchmark.equity_curve),
        )
        .where(BacktestRun.id == run_id)
    )


def derive_backtest_return_stability(run: BacktestRun) -> BacktestReturnStability:
    """Derive rolling/calendar stability for a run's strategy and fixed benchmarks.

    The run must already own its equity curves (e.g. via ``get_backtest_result``).
    The historical risk-free rate is parsed explicitly from ``parameters_json``;
    missing or malformed evidence yields ``None`` so legacy runs keep readable
    rolling return/volatility with an explicit unavailable Sharpe status.
    """
    risk_free_rate = _parse_risk_free_rate(run.parameters_json)
    strategy = derive_return_stability(
        points=tuple(
            ReturnStabilitySourcePoint(trade_date=point.trade_date, net_value=point.net_value)
            for point in run.equity_curve
        ),
        requested_start_date=run.start_date,
        requested_end_date=run.end_date,
        risk_free_rate=risk_free_rate,
    )
    benchmarks = tuple(
        BacktestReturnStabilityBenchmark(
            key=benchmark.benchmark_key,
            name=benchmark.display_name,
            result=derive_return_stability(
                points=tuple(
                    ReturnStabilitySourcePoint(
                        trade_date=point.trade_date, net_value=point.net_value
                    )
                    for point in benchmark.equity_curve
                ),
                requested_start_date=run.start_date,
                requested_end_date=run.end_date,
                risk_free_rate=risk_free_rate,
            ),
        )
        for benchmark in run.benchmarks
    )
    return BacktestReturnStability(strategy=strategy, benchmarks=benchmarks)


def _parse_risk_free_rate(parameters_json: str) -> Decimal | None:
    try:
        parameters = json.loads(parameters_json)
    except (ValueError, TypeError):
        return None
    # Persisted parameters may be null/array/scalar on corrupt evidence; treat
    # anything that is not a JSON object as missing risk-free-rate evidence.
    if not isinstance(parameters, dict):
        return None
    value = parameters.get("risk_free_rate")
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError):
        return None
