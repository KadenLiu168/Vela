from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from vela_core import (
    GeneratedSignalPosition,
    GenerateStrategySignalResult,
    StrategySignalListEntry,
    StrategySignalReport,
    StrategySignalReportPosition,
    generate_and_persist_strategy_signal,
    get_latest_strategy_signal_report,
    get_strategy_signal_report,
    list_strategy_signals,
)
from vela_core.models import StrategySignal

from vela_api.dependencies import AppConfigDependency, DatabaseSession
from vela_api.schemas import (
    GenerateSignalResponse,
    LatestSignalResponse,
    SignalDetailResponse,
    SignalListResponse,
)

router = APIRouter()
StrategySignalSourceFilter = Literal["manual", "scheduled", "backtest", "legacy"]


@router.post("/api/strategy-signals/generate", response_model=GenerateSignalResponse)
def generate_strategy_signal_endpoint(
    session: DatabaseSession,
    app_config: AppConfigDependency,
    signal_date: Annotated[date | None, Query(alias="signalDate")] = None,
    source: str = "manual",
) -> dict[str, object]:
    if source not in StrategySignal.LIVE_SOURCES:
        raise HTTPException(status_code=400, detail="Unsupported strategy signal source")
    try:
        result = generate_and_persist_strategy_signal(
            session, config=app_config.strategy, signal_date=signal_date, source=source
        )
    except ValueError as exc:
        if str(exc) != "No local market prices found":
            raise
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _strategy_signal_response(result, source=source)


@router.get("/api/strategy-signals/latest", response_model=LatestSignalResponse)
def latest_strategy_signal(
    session: DatabaseSession, app_config: AppConfigDependency
) -> dict[str, object]:
    report = get_latest_strategy_signal_report(
        session,
        strategy_id=app_config.strategy.strategy_id,
        config_version=app_config.strategy.version,
    )
    if report is None:
        return {"has_signal": False, "signal": None, "positions": []}
    return {
        "has_signal": True,
        "signal": _latest_strategy_signal_metadata_response(report),
        "positions": [_position_response(position) for position in report.positions],
    }


@router.get("/api/strategy-signals", response_model=SignalListResponse)
def list_strategy_signals_endpoint(
    session: DatabaseSession,
    app_config: AppConfigDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    source: Annotated[StrategySignalSourceFilter | None, Query()] = None,
) -> dict[str, object]:
    entries = list_strategy_signals(
        session,
        strategy_id=app_config.strategy.strategy_id,
        config_version=app_config.strategy.version,
        limit=limit,
        offset=offset,
        source=source,
    )
    return {"signals": [_list_item_response(entry) for entry in entries]}


@router.get("/api/strategy-signals/{signal_id}", response_model=SignalDetailResponse)
def strategy_signal_detail(
    signal_id: int, session: DatabaseSession, app_config: AppConfigDependency
) -> dict[str, object]:
    report = get_strategy_signal_report(session, signal_id=signal_id)
    if (
        report is None
        or report.strategy_id != app_config.strategy.strategy_id
        or report.config_version != app_config.strategy.version
    ):
        raise HTTPException(status_code=404, detail="Strategy signal not found")
    return {
        "signal": _detail_metadata_response(report),
        "positions": [_position_response(position) for position in report.positions],
    }


def _strategy_signal_response(
    result: GenerateStrategySignalResult, *, source: str
) -> dict[str, object]:
    return {
        "signal_id": result.strategy_signal_id,
        "signal_date": result.signal_date.isoformat(),
        "config_version": result.config_version,
        "status": result.status,
        "result": result.result,
        "error_message": result.error_message,
        "source": source,
        "positions": [_generated_position_response(position) for position in result.positions],
    }


def _generated_position_response(position: GeneratedSignalPosition) -> dict[str, object]:
    return {
        "etf_id": position.etf_id,
        "exchange": position.exchange,
        "symbol": position.symbol,
        "target_weight": _decimal(position.target_weight),
        "rank": position.rank,
        "score": _decimal(position.score),
    }


def _latest_strategy_signal_metadata_response(report: StrategySignalReport) -> dict[str, object]:
    return {
        "signal_id": report.signal_id,
        "signal_date": report.signal_date.isoformat(),
        "config_version": report.config_version,
        "generated_at": report.generated_at,
        "result": report.result,
        "is_fallback": report.is_fallback,
    }


def _position_response(position: StrategySignalReportPosition) -> dict[str, object]:
    return {
        "exchange": position.exchange,
        "symbol": position.symbol,
        "name": position.name,
        "target_weight": _decimal(position.target_weight),
        "rank": position.rank,
        "score": _decimal(position.score),
        "is_fallback": position.is_fallback,
    }


def _list_item_response(entry: StrategySignalListEntry) -> dict[str, object]:
    return {
        "signal_id": entry.signal_id,
        "signal_date": entry.signal_date.isoformat(),
        "config_version": entry.config_version,
        "result": entry.result,
        "generated_at": entry.generated_at,
        "is_fallback": entry.is_fallback,
        "position_count": entry.position_count,
        "source": entry.source,
        "backtest_run_id": entry.backtest_run_id,
    }


def _detail_metadata_response(report: StrategySignalReport) -> dict[str, object]:
    return {
        "signal_id": report.signal_id,
        "signal_date": report.signal_date.isoformat(),
        "strategy_id": report.strategy_id,
        "config_version": report.config_version,
        "generated_at": report.generated_at,
        "result": report.result,
        "is_fallback": report.is_fallback,
        "source": report.source,
        "backtest_run_id": report.backtest_run_id,
    }


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)
