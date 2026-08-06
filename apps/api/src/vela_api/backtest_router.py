from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from vela_core import (
    MINIMUM_PUBLICATION_OBSERVATIONS,
    BacktestReturnStability,
    BacktestRunResult,
    BacktestSignalSummaryEntry,
    CalendarReturnBucket,
    ReturnStabilityResult,
    derive_backtest_return_stability,
    get_backtest_result,
    list_backtest_signals,
    run_backtest,
)
from vela_core.models import BacktestBenchmark, BacktestEquityCurve, BacktestRun

from vela_api.dependencies import AppConfigDependency, DatabaseSession
from vela_api.schemas import (
    BacktestDetailResponse,
    BacktestListResponse,
    BacktestRunResponse,
    BacktestSignalsResponse,
)

router = APIRouter()


@router.get("/api/backtests", response_model=BacktestListResponse)
def list_backtests(
    session: DatabaseSession,
    app_config: AppConfigDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    strategy_id: Annotated[str | None, Query(alias="strategyId")] = None,
    config_version: Annotated[str | None, Query(alias="configVersion")] = None,
) -> dict[str, object]:
    runs = session.scalars(
        select(BacktestRun)
        .where(BacktestRun.strategy_id == (strategy_id or app_config.strategy.strategy_id))
        .where(BacktestRun.config_version == (config_version or app_config.strategy.version))
        .order_by(BacktestRun.started_at.desc(), BacktestRun.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return {"runs": [_list_item_response(run) for run in runs]}


@router.post("/api/backtests/run", response_model=BacktestRunResponse)
def run_backtest_endpoint(
    session: DatabaseSession,
    app_config: AppConfigDependency,
    start_date: Annotated[date, Query(alias="startDate")],
    end_date: Annotated[date, Query(alias="endDate")],
) -> dict[str, object]:
    result = run_backtest(
        session,
        config=app_config.strategy,
        start_date=start_date,
        end_date=end_date,
        calculate_benchmarks=True,
    )
    return _run_response(result)


@router.get("/api/backtests/{run_id}", response_model=BacktestDetailResponse)
def backtest_detail(
    run_id: int, session: DatabaseSession, app_config: AppConfigDependency
) -> dict[str, object]:
    run = get_backtest_result(session, run_id=run_id)
    if run is None or run.strategy_id != app_config.strategy.strategy_id:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return {
        "run": _detail_run_response(run),
        "metrics": _metrics_response(run),
        "equity_curve": [_curve_point_response(row) for row in run.equity_curve],
        "signal_ids": [signal.id for signal in run.signals],
        "signal_count": len(run.signals),
        "benchmarks": _benchmark_responses(run),
        "return_stability": _return_stability_response(derive_backtest_return_stability(run)),
    }


@router.get("/api/backtests/{run_id}/signals", response_model=BacktestSignalsResponse)
def backtest_signals_endpoint(
    run_id: int,
    session: DatabaseSession,
    app_config: AppConfigDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    entries = list_backtest_signals(
        session,
        run_id=run_id,
        strategy_id=app_config.strategy.strategy_id,
        config_version=None,
        limit=limit,
        offset=offset,
    )
    if entries is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return {"signals": [_signal_summary_response(entry) for entry in entries]}


def _run_response(result: BacktestRunResult) -> dict[str, object]:
    return {
        "run_id": result.backtest_run_id,
        "status": result.status,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "trading_day_count": result.trading_day_count,
        "signal_count": result.signal_count,
        "total_return": _decimal(result.total_return),
        "annualized_return": _decimal(result.annualized_return),
        "max_drawdown": _decimal(result.max_drawdown),
        "volatility": _decimal(result.volatility),
        "sharpe_ratio": _decimal(result.sharpe_ratio),
        "sortino_ratio": _decimal(result.sortino_ratio),
        "calmar_ratio": _decimal(result.calmar_ratio),
        "longest_drawdown_duration_sessions": result.longest_drawdown_duration_sessions,
        "longest_drawdown_peak_date": _optional_date(result.longest_drawdown_peak_date),
        "longest_drawdown_trough_date": _optional_date(result.longest_drawdown_trough_date),
        "longest_drawdown_recovery_date": _optional_date(result.longest_drawdown_recovery_date),
        **_distribution_fields(
            historical_var_95=result.historical_var_95,
            historical_cvar_95=result.historical_cvar_95,
            return_skewness=result.return_skewness,
            return_excess_kurtosis=result.return_excess_kurtosis,
            distribution_observation_count=result.distribution_observation_count,
            tail_observation_count=result.tail_observation_count,
        ),
        "benchmarks": _benchmark_result_responses(result),
    }


def _list_item_response(run: BacktestRun) -> dict[str, object]:
    return {
        "run_id": run.id,
        "strategy_id": run.strategy_id,
        "config_version": run.config_version,
        "start_date": run.start_date.isoformat(),
        "end_date": run.end_date.isoformat(),
        "status": run.status,
        "started_at": _datetime(run.started_at),
        "finished_at": _optional_datetime(run.finished_at),
        "total_return": _decimal(run.total_return),
        "annualized_return": _decimal(run.annualized_return),
        "max_drawdown": _decimal(run.max_drawdown),
        "volatility": _decimal(run.volatility),
        "sharpe_ratio": _decimal(run.sharpe_ratio),
    }


def _detail_run_response(run: BacktestRun) -> dict[str, object]:
    return {
        "run_id": run.id,
        "strategy_id": run.strategy_id,
        "config_version": run.config_version,
        "start_date": run.start_date.isoformat(),
        "end_date": run.end_date.isoformat(),
        "parameters_json": run.parameters_json,
        "status": run.status,
        "error_message": run.error_message,
        "started_at": _datetime(run.started_at),
        "finished_at": _optional_datetime(run.finished_at),
    }


def _metrics_response(run: BacktestRun) -> dict[str, object]:
    return {
        "total_return": _decimal(run.total_return),
        "annualized_return": _decimal(run.annualized_return),
        "max_drawdown": _decimal(run.max_drawdown),
        "volatility": _decimal(run.volatility),
        "sharpe_ratio": _decimal(run.sharpe_ratio),
        "sortino_ratio": _decimal(run.sortino_ratio),
        "calmar_ratio": _decimal(run.calmar_ratio),
        "longest_drawdown_duration_sessions": run.longest_drawdown_duration_sessions,
        "longest_drawdown_peak_date": run.longest_drawdown_peak_date,
        "longest_drawdown_trough_date": run.longest_drawdown_trough_date,
        "longest_drawdown_recovery_date": run.longest_drawdown_recovery_date,
        **_distribution_fields(
            historical_var_95=run.historical_var_95,
            historical_cvar_95=run.historical_cvar_95,
            return_skewness=run.return_skewness,
            return_excess_kurtosis=run.return_excess_kurtosis,
            distribution_observation_count=run.distribution_observation_count,
            tail_observation_count=run.tail_observation_count,
        ),
    }


def _curve_point_response(row: BacktestEquityCurve) -> dict[str, object]:
    return {
        "trade_date": row.trade_date.isoformat(),
        "net_value": _decimal(row.net_value),
        "cash": _decimal(row.cash),
        "market_value": _decimal(row.market_value),
        "total_assets": _decimal(row.total_assets),
        "positions_json": row.positions_json,
    }


def _benchmark_responses(run: BacktestRun) -> list[dict[str, object]]:
    return [
        _benchmark_response(row, run.total_return, run.annualized_return) for row in run.benchmarks
    ]


def _benchmark_result_responses(result: BacktestRunResult) -> list[dict[str, object]]:
    return [
        {
            "key": benchmark.key,
            "name": benchmark.name,
            "total_return": _decimal(benchmark.annualized_return.total_return),
            "annualized_return": _decimal(benchmark.annualized_return.annualized_return),
            "max_drawdown": _decimal(benchmark.maximum_drawdown.max_drawdown),
            "volatility": _decimal(benchmark.volatility.volatility),
            "sharpe_ratio": _decimal(benchmark.sharpe_ratio.sharpe_ratio),
            "sortino_ratio": _decimal(benchmark.sortino_ratio.sortino_ratio),
            "calmar_ratio": _decimal(benchmark.calmar_ratio.calmar_ratio),
            "longest_drawdown_duration_sessions": (
                benchmark.longest_drawdown_duration.longest_drawdown_duration_sessions
            ),
            "longest_drawdown_peak_date": _optional_date(
                benchmark.longest_drawdown_duration.peak_date
            ),
            "longest_drawdown_trough_date": _optional_date(
                benchmark.longest_drawdown_duration.trough_date
            ),
            "longest_drawdown_recovery_date": _optional_date(
                benchmark.longest_drawdown_duration.recovery_date
            ),
            "tracking_error": _decimal(benchmark.tracking_error),
            "information_ratio": _decimal(benchmark.information_ratio),
            "capm_alpha": _decimal(benchmark.capm_alpha),
            "capm_beta": _decimal(benchmark.capm_beta),
            "capm_r_squared": _decimal(benchmark.capm_r_squared),
            "capm_observation_count": benchmark.capm_observation_count,
            "up_capture_ratio": _decimal(benchmark.up_capture_ratio),
            "up_capture_observation_count": benchmark.up_capture_observation_count,
            "down_capture_ratio": _decimal(benchmark.down_capture_ratio),
            "down_capture_observation_count": benchmark.down_capture_observation_count,
            **_distribution_fields(
                historical_var_95=benchmark.historical_var_95,
                historical_cvar_95=benchmark.historical_cvar_95,
                return_skewness=benchmark.return_skewness,
                return_excess_kurtosis=benchmark.return_excess_kurtosis,
                distribution_observation_count=benchmark.distribution_observation_count,
                tail_observation_count=benchmark.tail_observation_count,
            ),
            "total_return_difference": _difference(
                result.total_return, benchmark.annualized_return.total_return
            ),
            "annualized_return_difference": _difference(
                result.annualized_return, benchmark.annualized_return.annualized_return
            ),
            "equity_curve": [],
        }
        for benchmark in result.benchmarks
    ]


def _benchmark_response(
    benchmark: BacktestBenchmark,
    strategy_total_return: Decimal | None,
    strategy_annualized_return: Decimal | None,
) -> dict[str, object]:
    return {
        "key": benchmark.benchmark_key,
        "name": benchmark.display_name,
        "total_return": _decimal(benchmark.total_return),
        "annualized_return": _decimal(benchmark.annualized_return),
        "max_drawdown": _decimal(benchmark.max_drawdown),
        "volatility": _decimal(benchmark.volatility),
        "sharpe_ratio": _decimal(benchmark.sharpe_ratio),
        "sortino_ratio": _decimal(benchmark.sortino_ratio),
        "calmar_ratio": _decimal(benchmark.calmar_ratio),
        "longest_drawdown_duration_sessions": benchmark.longest_drawdown_duration_sessions,
        "longest_drawdown_peak_date": _optional_date(benchmark.longest_drawdown_peak_date),
        "longest_drawdown_trough_date": _optional_date(benchmark.longest_drawdown_trough_date),
        "longest_drawdown_recovery_date": _optional_date(benchmark.longest_drawdown_recovery_date),
        "tracking_error": _decimal(benchmark.tracking_error),
        "information_ratio": _decimal(benchmark.information_ratio),
        "capm_alpha": _decimal(benchmark.capm_alpha),
        "capm_beta": _decimal(benchmark.capm_beta),
        "capm_r_squared": _decimal(benchmark.capm_r_squared),
        "capm_observation_count": benchmark.capm_observation_count,
        "up_capture_ratio": _decimal(benchmark.up_capture_ratio),
        "up_capture_observation_count": benchmark.up_capture_observation_count,
        "down_capture_ratio": _decimal(benchmark.down_capture_ratio),
        "down_capture_observation_count": benchmark.down_capture_observation_count,
        **_distribution_fields(
            historical_var_95=benchmark.historical_var_95,
            historical_cvar_95=benchmark.historical_cvar_95,
            return_skewness=benchmark.return_skewness,
            return_excess_kurtosis=benchmark.return_excess_kurtosis,
            distribution_observation_count=benchmark.distribution_observation_count,
            tail_observation_count=benchmark.tail_observation_count,
        ),
        "total_return_difference": _difference(strategy_total_return, benchmark.total_return),
        "annualized_return_difference": _difference(
            strategy_annualized_return, benchmark.annualized_return
        ),
        "equity_curve": [
            {"trade_date": row.trade_date.isoformat(), "net_value": _decimal(row.net_value)}
            for row in benchmark.equity_curve
        ],
    }


def _difference(left: Decimal | None, right: Decimal | None) -> str | None:
    return _decimal(None if left is None or right is None else left - right)


def _distribution_fields(
    *,
    historical_var_95: Decimal | None,
    historical_cvar_95: Decimal | None,
    return_skewness: Decimal | None,
    return_excess_kurtosis: Decimal | None,
    distribution_observation_count: int | None,
    tail_observation_count: int | None,
) -> dict[str, object]:
    """Serialize stored tail-distribution evidence without recomputing it.

    Only the evidence label is derived from the persisted observation count;
    legacy owners with null counts expose an explicit unavailable status rather
    than an assumed zero sample.
    """
    return {
        "historical_var_95": _decimal(historical_var_95),
        "historical_cvar_95": _decimal(historical_cvar_95),
        "return_skewness": _decimal(return_skewness),
        "return_excess_kurtosis": _decimal(return_excess_kurtosis),
        "distribution_observation_count": distribution_observation_count,
        "tail_observation_count": tail_observation_count,
        "distribution_evidence_status": _distribution_evidence_status(
            distribution_observation_count
        ),
    }


def _distribution_evidence_status(count: int | None) -> str:
    if count is None:
        return "unavailable_legacy"
    return "sufficient" if count >= MINIMUM_PUBLICATION_OBSERVATIONS else "insufficient_evidence"


def _return_stability_response(result: BacktestReturnStability) -> dict[str, object]:
    return {
        "strategy": _stability_entity_response(result.strategy),
        "benchmarks": [
            {
                **_stability_entity_response(benchmark.result),
                "key": benchmark.key,
                "name": benchmark.name,
            }
            for benchmark in result.benchmarks
        ],
    }


def _stability_entity_response(result: ReturnStabilityResult) -> dict[str, object]:
    return {
        "window_sessions": result.window_sessions,
        "rolling_status": result.rolling_status,
        "sharpe_status": result.sharpe_status,
        "source_point_count": result.source_point_count,
        "effective_return_count": result.effective_return_count,
        "rolling": [
            {
                "window_start_date": point.window_start_date.isoformat(),
                "trade_date": point.trade_date.isoformat(),
                "total_return": _decimal(point.total_return),
                "volatility": _decimal(point.volatility),
                "sharpe_ratio": _decimal(point.sharpe_ratio),
            }
            for point in result.rolling
        ],
        "monthly": [_calendar_bucket_response(bucket) for bucket in result.monthly],
        "yearly": [_calendar_bucket_response(bucket) for bucket in result.yearly],
    }


def _calendar_bucket_response(
    bucket: CalendarReturnBucket,
) -> dict[str, object]:
    return {
        "period": bucket.period,
        "first_date": bucket.first_date.isoformat(),
        "last_date": bucket.last_date.isoformat(),
        "observation_count": bucket.observation_count,
        "total_return": _decimal(bucket.total_return),
        "is_partial": bucket.is_partial,
    }


def _signal_summary_response(entry: BacktestSignalSummaryEntry) -> dict[str, object]:
    return {
        "signal_id": entry.signal_id,
        "signal_date": entry.signal_date.isoformat(),
        "result": entry.result,
        "backtest_run_id": entry.backtest_run_id,
    }


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _optional_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _optional_datetime(value: datetime | None) -> str | None:
    return None if value is None else _datetime(value)


def _datetime(value: datetime) -> str:
    return value.replace(tzinfo=None).isoformat()
