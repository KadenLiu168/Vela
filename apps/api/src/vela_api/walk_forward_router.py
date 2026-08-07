from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Annotated, cast

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select
from vela_core import MINIMUM_PUBLICATION_OBSERVATIONS
from vela_core.config import ConfigError
from vela_core.database import create_engine_from_url, create_session_factory, managed_session
from vela_core.models import BacktestBenchmark, BacktestRun, WalkForwardRun, WalkForwardRunWindow
from vela_core.walk_forward.config import load_walk_forward_config
from vela_core.walk_forward.evidence import (
    EVIDENCE_VERSION_V2,
    EVIDENCE_VERSION_V3,
    WalkForwardEvidenceV1,
    WalkForwardEvidenceV2,
    WalkForwardEvidenceV3,
)
from vela_core.walk_forward.query import get_walk_forward_run, list_walk_forward_runs
from vela_core.walk_forward.runner import WalkForwardRunner
from vela_core.walk_forward.stitched_oos import StitchedOosResult

from vela_api.dependencies import AppConfigDependency, DatabaseSession
from vela_api.schemas import (
    WalkForwardDetailResponse,
    WalkForwardEvidenceResponse,
    WalkForwardEvidenceV2Response,
    WalkForwardEvidenceV3Response,
    WalkForwardPageResponse,
    WalkForwardRunAcceptedResponse,
)

router = APIRouter()


@router.get("/api/walk-forwards", response_model=WalkForwardPageResponse)
def list_walk_forwards(
    session: DatabaseSession,
    app_config: AppConfigDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    rows, total = list_walk_forward_runs(
        session,
        strategy_id=app_config.strategy.strategy_id,
        limit=limit,
        offset=offset,
    )
    return {
        "runs": [_summary(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/walk-forwards/{run_id}", response_model=WalkForwardDetailResponse)
def walk_forward_detail(
    run_id: int, session: DatabaseSession, app_config: AppConfigDependency
) -> dict[str, object]:
    row = get_walk_forward_run(
        session,
        run_id=run_id,
        strategy_id=app_config.strategy.strategy_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Walk-forward run not found")
    if row.status != "success":
        # Running and failed parents carry only placeholder evidence; expose the
        # persisted metadata without attempting to validate a full document.
        return {
            "run": {
                **_summary(row),
                "created_at": row.created_at,
            },
            "configuration": {
                "walk_forward": row.walk_forward_config_json,
                "base_strategy": row.base_strategy_config_json,
                "config_checksum": row.config_checksum,
            },
            "input_provenance": {
                "manifest": row.input_data_snapshot_json,
                "input_data_checksum": row.input_data_checksum,
            },
            "evidence_version": row.evidence_version,
            "evidence": None,
            "windows": [],
            "stitched_oos": _stitched_oos_response(
                cast(StitchedOosResult, getattr(row, "stitched_oos"))  # noqa: B009
            ),
        }
    if row.evidence_version == EVIDENCE_VERSION_V2:
        evidence: WalkForwardEvidenceV1 | WalkForwardEvidenceV2 | WalkForwardEvidenceV3 = (
            WalkForwardEvidenceV2.model_validate(row.evidence_json)
        )
        evidence_response: (
            WalkForwardEvidenceResponse
            | WalkForwardEvidenceV2Response
            | WalkForwardEvidenceV3Response
        ) = WalkForwardEvidenceV2Response.model_validate(evidence.model_dump(mode="json"))
    elif row.evidence_version == EVIDENCE_VERSION_V3:
        evidence = WalkForwardEvidenceV3.model_validate(row.evidence_json)
        evidence_response = WalkForwardEvidenceV3Response.model_validate(
            evidence.model_dump(mode="json")
        )
    else:
        evidence = WalkForwardEvidenceV1.model_validate(row.evidence_json)
        evidence_response = WalkForwardEvidenceResponse.model_validate(
            evidence.model_dump(mode="json")
        )
    return {
        "run": {
            **_summary(row),
            "created_at": row.created_at,
        },
        "configuration": {
            "walk_forward": row.walk_forward_config_json,
            "base_strategy": row.base_strategy_config_json,
            "config_checksum": row.config_checksum,
        },
        "input_provenance": {
            "manifest": row.input_data_snapshot_json,
            "input_data_checksum": row.input_data_checksum,
        },
        "evidence_version": row.evidence_version,
        "evidence": evidence_response,
        "windows": [_window_response(window) for window in row.windows],
        "stitched_oos": _stitched_oos_response(
            cast(StitchedOosResult, getattr(row, "stitched_oos"))  # noqa: B009
        ),
    }


@router.post(
    "/api/walk-forwards/run",
    status_code=202,
    response_model=WalkForwardRunAcceptedResponse,
)
async def run_walk_forward(
    request: Request,
    session: DatabaseSession,
    app_config: AppConfigDependency,
) -> dict[str, object]:
    if request.query_params:
        raise HTTPException(
            status_code=422,
            detail="Walk-forward run accepts no query parameters",
        )
    body = await request.body()
    if body:
        raise HTTPException(
            status_code=422,
            detail="Walk-forward run accepts no request body",
        )
    _reject_concurrent_run(session, app_config)
    database_url = request.app.state.database_url
    config_path = app_config.walk_forward_config_path
    try:
        run_id = await asyncio.to_thread(
            _begin_walk_forward_run,
            database_url=database_url,
            config_path=config_path,
        )
    except ConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    task = asyncio.create_task(
        asyncio.to_thread(
            _complete_walk_forward_run,
            database_url=database_url,
            run_id=run_id,
            config_path=config_path,
        )
    )
    task.add_done_callback(_consume_background_failure)
    return {"walk_forward_run_id": run_id}


def _consume_background_failure(task: asyncio.Task[object]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger = logging.getLogger(__name__)
        logger.error("walk_forward.background_run_failed run_id_unknown exception=%s", exc)


def _reject_concurrent_run(session, app_config) -> None:
    stale_before = datetime.now(UTC) - timedelta(hours=1)
    running = session.scalar(
        select(WalkForwardRun.id)
        .where(WalkForwardRun.strategy_id == app_config.strategy.strategy_id)
        .where(WalkForwardRun.status == "running")
        .where(WalkForwardRun.started_at >= stale_before)
        .limit(1)
    )
    if running is not None:
        raise HTTPException(
            status_code=409,
            detail="a walk-forward run is already in progress for this strategy",
        )


def _begin_walk_forward_run(*, database_url: str, config_path: Path) -> int:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    try:
        with managed_session(session_factory) as session:
            config = load_walk_forward_config(config_path)
            runner = WalkForwardRunner(config)
            run_id, _started_at = runner.begin(session)
            return run_id
    finally:
        engine.dispose()


def _complete_walk_forward_run(*, database_url: str, run_id: int, config_path: Path) -> None:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    try:
        with managed_session(session_factory) as session:
            row = session.get(WalkForwardRun, run_id)
            if row is None:
                return
            config = load_walk_forward_config(config_path)
            runner = WalkForwardRunner(config)
            runner.complete(session, run_id, row.started_at)
    finally:
        engine.dispose()


def _summary(row: WalkForwardRun) -> dict[str, object]:
    return {
        "run_id": row.id,
        "strategy_id": row.strategy_id,
        "start_date": row.start_date,
        "end_date": row.end_date,
        "window_count": row.window_count,
        "provenance_version": row.provenance_version,
        "evidence_version": row.evidence_version,
        "config_checksum": row.config_checksum,
        "input_data_checksum": row.input_data_checksum,
        "status": row.status,
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
    }


def _window_response(row: WalkForwardRunWindow) -> dict[str, object]:
    if row.oos_backtest_run is None:
        raise ValueError("Walk-forward window has no selected OOS backtest")
    return {
        "ordinal": row.ordinal,
        "train_start": row.train_start,
        "train_end": row.train_end,
        "test_start": row.test_start,
        "test_end": row.test_end,
        "oos_version": row.oos_version,
        "selected_parameters": row.selected_parameters_json,
        "candidate_count": row.candidate_count,
        "eligible_count": row.eligible_count,
        "skipped_count": row.skipped_count,
        "skip_reason_counts": row.skip_reason_counts_json,
        "train_sharpe": _decimal(row.train_sharpe),
        "oos_backtest": _oos_response(row.oos_backtest_run),
    }


def _stitched_oos_response(result: StitchedOosResult) -> dict[str, object]:
    return {
        "status": result.status,
        "initial_net_value": _decimal(result.initial_net_value),
        "ending_net_value": _decimal(result.ending_net_value),
        "total_return": _decimal(result.total_return),
        "points": [
            {
                "trade_date": point.trade_date,
                "net_value": _decimal(point.net_value),
                "window_ordinal": point.window_ordinal,
                "is_window_start": point.is_window_start,
            }
            for point in result.points
        ],
    }


def _oos_response(row: BacktestRun) -> dict[str, object]:
    return {
        "run_id": row.id,
        "strategy_id": row.strategy_id,
        "config_version": row.config_version,
        "start_date": row.start_date,
        "end_date": row.end_date,
        "status": row.status,
        "total_return": _decimal(row.total_return),
        "annualized_return": _decimal(row.annualized_return),
        "max_drawdown": _decimal(row.max_drawdown),
        "volatility": _decimal(row.volatility),
        "sharpe_ratio": _decimal(row.sharpe_ratio),
        "sortino_ratio": _decimal(row.sortino_ratio),
        "calmar_ratio": _decimal(row.calmar_ratio),
        "longest_drawdown_duration_sessions": row.longest_drawdown_duration_sessions,
        "longest_drawdown_peak_date": row.longest_drawdown_peak_date,
        "longest_drawdown_trough_date": row.longest_drawdown_trough_date,
        "longest_drawdown_recovery_date": row.longest_drawdown_recovery_date,
        "benchmarks": [_benchmark_response(item, row) for item in row.benchmarks],
    }


def _benchmark_response(row: BacktestBenchmark, strategy: BacktestRun) -> dict[str, object]:
    return {
        "key": row.benchmark_key,
        "name": row.display_name,
        "total_return": _decimal(row.total_return),
        "annualized_return": _decimal(row.annualized_return),
        "max_drawdown": _decimal(row.max_drawdown),
        "volatility": _decimal(row.volatility),
        "sharpe_ratio": _decimal(row.sharpe_ratio),
        "sortino_ratio": _decimal(row.sortino_ratio),
        "calmar_ratio": _decimal(row.calmar_ratio),
        "longest_drawdown_duration_sessions": row.longest_drawdown_duration_sessions,
        "longest_drawdown_peak_date": row.longest_drawdown_peak_date,
        "longest_drawdown_trough_date": row.longest_drawdown_trough_date,
        "longest_drawdown_recovery_date": row.longest_drawdown_recovery_date,
        "total_return_difference": _difference(strategy.total_return, row.total_return),
        "annualized_return_difference": _difference(
            strategy.annualized_return, row.annualized_return
        ),
        "tracking_error": _decimal(row.tracking_error),
        "information_ratio": _decimal(row.information_ratio),
        "capm_alpha": _decimal(row.capm_alpha),
        "capm_beta": _decimal(row.capm_beta),
        "capm_r_squared": _decimal(row.capm_r_squared),
        "capm_observation_count": row.capm_observation_count,
        "up_capture_ratio": _decimal(row.up_capture_ratio),
        "up_capture_observation_count": row.up_capture_observation_count,
        "down_capture_ratio": _decimal(row.down_capture_ratio),
        "down_capture_observation_count": row.down_capture_observation_count,
        "historical_var_95": _decimal(row.historical_var_95),
        "historical_cvar_95": _decimal(row.historical_cvar_95),
        "return_skewness": _decimal(row.return_skewness),
        "return_excess_kurtosis": _decimal(row.return_excess_kurtosis),
        "distribution_observation_count": row.distribution_observation_count,
        "tail_observation_count": row.tail_observation_count,
        "distribution_evidence_status": _distribution_evidence_status(
            row.distribution_observation_count
        ),
    }


def _decimal(value: Decimal | float | int | None) -> str | None:
    return None if value is None else str(value)


def _distribution_evidence_status(count: int | None) -> str:
    if count is None:
        return "unavailable_legacy"
    return "sufficient" if count >= MINIMUM_PUBLICATION_OBSERVATIONS else "insufficient_evidence"


def _difference(left: Decimal | None, right: Decimal | None) -> str | None:
    return None if left is None or right is None else str(left - right)
