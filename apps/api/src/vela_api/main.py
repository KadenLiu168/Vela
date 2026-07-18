from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request
from vela_core import (
    BacktestRunResult,
    BootstrapResult,
    ConfigError,
    GeneratedSignalPosition,
    GenerateStrategySignalResult,
    MarketDataFetchResult,
    MarketDataProvider,
    PriceTrendRange,
    StrategySignalListEntry,
    StrategySignalReport,
    StrategySignalReportPosition,
    TencentMarketDataProvider,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
    generate_and_persist_strategy_signal,
    get_backtest_result,
    get_dashboard_summary,
    get_etf_price_trend,
    get_latest_strategy_signal_report,
    get_strategy_signal_report,
    list_strategy_signals,
    load_app_config,
    run_backtest,
    run_local_setup_bootstrap,
)
from vela_core.models import BacktestEquityCurve, BacktestRun
from vela_core.strategy_config import load_strategy_config

from vela_api.config import (
    DEFAULT_ALEMBIC_SCRIPT_LOCATION,
    DEFAULT_STRATEGY_CONFIG_PATH,
    get_config_summary,
)
from vela_api.database import get_database_session, initialize_database

app = FastAPI(title="Vela API")
initialize_database(app)
app.state.strategy_config = load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)
DatabaseSession = Annotated[Session, Depends(get_database_session)]
MarketDataFetchMode = Literal["incremental", "full"]
ErrorCategory = Literal["validation", "not_found", "operation_failed", "unexpected"]


def get_market_data_provider() -> MarketDataProvider:
    return TencentMarketDataProvider()


MarketDataProviderDependency = Annotated[MarketDataProvider, Depends(get_market_data_provider)]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        status_code=422,
        code="validation_error",
        category="validation",
        message="Request validation failed",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = _http_exception_message(exc)
    return _error_response(
        status_code=exc.status_code,
        code=_http_error_code(exc.status_code, message),
        category=_http_error_category(exc.status_code),
        message=message,
    )


@app.exception_handler(ConfigError)
async def config_exception_handler(_request: Request, exc: ConfigError) -> JSONResponse:
    return _error_response(
        status_code=500,
        code="config_error",
        category="operation_failed",
        message=str(exc),
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return _error_response(
        status_code=500,
        code="unexpected_error",
        category="unexpected",
        message="Unexpected API error",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/config")
def config() -> dict[str, object]:
    return get_config_summary()


@app.get("/api/dashboard")
def dashboard(session: DatabaseSession) -> dict[str, object]:
    config_summary = get_config_summary()
    return get_dashboard_summary(session, strategy_summary=config_summary["strategy"])


@app.get("/api/etfs/{etf_id}/prices")
def etf_price_trend_endpoint(
    etf_id: int,
    session: DatabaseSession,
    range_: Annotated[PriceTrendRange, Query(alias="range")] = "1y",
) -> dict[str, object]:
    result = get_etf_price_trend(session, etf_id=etf_id, range_=range_)
    if result is None:
        raise HTTPException(status_code=404, detail="ETF not found")

    return result.to_dict()


@app.post("/api/market-data/fetch")
def fetch_market_data(
    mode: MarketDataFetchMode,
    session: DatabaseSession,
    provider: MarketDataProviderDependency,
) -> dict[str, object]:
    if mode == "incremental":
        result = fetch_incremental_market_prices(session, provider=provider)
    else:
        result = fetch_full_market_prices(session, provider=provider)

    return _market_data_fetch_response(result)


@app.post("/api/setup/bootstrap")
def setup_bootstrap(
    request: Request,
    session: DatabaseSession,
    provider: MarketDataProviderDependency,
) -> dict[str, object]:
    result = run_local_setup_bootstrap(
        session,
        provider=provider,
        app_config=request.app.state.strategy_config,
        database_url=request.app.state.database_url,
        script_location=DEFAULT_ALEMBIC_SCRIPT_LOCATION,
    )
    return _bootstrap_response(result)


@app.post("/api/strategy-signals/generate")
def generate_strategy_signal_endpoint(
    session: DatabaseSession,
    signal_date: Annotated[date | None, Query(alias="signalDate")] = None,
) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    try:
        result = generate_and_persist_strategy_signal(
            session,
            config=config,
            signal_date=signal_date,
        )
    except ValueError as exc:
        if str(exc) != "No local market prices found":
            raise
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _strategy_signal_response(result)


@app.get("/api/strategy-signals/latest")
def latest_strategy_signal(session: DatabaseSession) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    report = get_latest_strategy_signal_report(
        session,
        config_version=config.version,
    )
    if report is None:
        return {
            "has_signal": False,
            "signal": None,
            "positions": [],
        }

    return {
        "has_signal": True,
        "signal": _latest_strategy_signal_metadata_response(report),
        "positions": [
            _latest_strategy_signal_position_response(position) for position in report.positions
        ],
    }


@app.get("/api/strategy-signals")
def list_strategy_signals_endpoint(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    entries = list_strategy_signals(
        session,
        strategy_id=config.strategy_id,
        config_version=config.version,
        limit=limit,
        offset=offset,
    )
    return {"signals": [_strategy_signal_list_item_response(entry) for entry in entries]}


@app.get("/api/strategy-signals/{signal_id}")
def strategy_signal_detail(
    signal_id: int,
    session: DatabaseSession,
) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    report = get_strategy_signal_report(session, signal_id=signal_id)
    if (
        report is None
        or report.strategy_id != config.strategy_id
        or report.config_version != config.version
    ):
        raise HTTPException(status_code=404, detail="Strategy signal not found")

    return {
        "signal": _strategy_signal_detail_metadata_response(report),
        "positions": [
            _strategy_signal_detail_position_response(position) for position in report.positions
        ],
    }


@app.get("/api/backtests")
def list_backtests(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    strategy_id: Annotated[str | None, Query(alias="strategyId")] = None,
    config_version: Annotated[str | None, Query(alias="configVersion")] = None,
) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    resolved_strategy_id = strategy_id or config.strategy_id
    resolved_config_version = config_version or config.version
    runs = session.scalars(
        select(BacktestRun)
        .where(BacktestRun.strategy_id == resolved_strategy_id)
        .where(BacktestRun.config_version == resolved_config_version)
        .order_by(BacktestRun.started_at.desc(), BacktestRun.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return {"runs": [_backtest_list_item_response(run) for run in runs]}


@app.post("/api/backtests/run")
def run_backtest_endpoint(
    session: DatabaseSession,
    start_date: Annotated[date, Query(alias="startDate")],
    end_date: Annotated[date, Query(alias="endDate")],
) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    try:
        result = run_backtest(
            session,
            config=config,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _backtest_run_response(result)


@app.get("/api/backtests/{run_id}")
def backtest_detail(run_id: int, session: DatabaseSession) -> dict[str, object]:
    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    run = get_backtest_result(session, run_id=run_id)
    if run is None or run.strategy_id != config.strategy_id or run.config_version != config.version:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    return {
        "run": _backtest_detail_run_response(run),
        "metrics": _backtest_metrics_response(run),
        "equity_curve": [_backtest_curve_point_response(row) for row in run.equity_curve],
    }


def _bootstrap_response(result: BootstrapResult) -> dict[str, object]:
    return {
        "status": result.status,
        "failed_step": result.failed_step,
        "total_duration_seconds": result.total_duration_seconds,
        "steps": [
            {
                "name": step.name,
                "status": step.status,
                "duration_seconds": step.duration_seconds,
                "error_message": step.error_message,
            }
            for step in result.steps
        ],
    }


def _market_data_fetch_response(result: MarketDataFetchResult) -> dict[str, object]:
    return {
        "status": result.status,
        "requested_etf_count": result.requested_symbol_count,
        "rows_fetched": result.rows_fetched,
        "rows_inserted": result.rows_inserted,
        "rows_updated": result.rows_updated,
        "failed_symbols": list(result.failed_symbols),
        "error_message": result.error_message,
    }


def _strategy_signal_response(result: GenerateStrategySignalResult) -> dict[str, object]:
    return {
        "signal_id": result.strategy_signal_id,
        "signal_date": result.signal_date.isoformat(),
        "config_version": result.config_version,
        "status": result.status,
        "result": result.result,
        "error_message": result.error_message,
        "positions": [
            _strategy_signal_position_response(position) for position in result.positions
        ],
    }


def _backtest_run_response(result: BacktestRunResult) -> dict[str, object]:
    return {
        "run_id": result.backtest_run_id,
        "status": result.status,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "trading_day_count": result.trading_day_count,
        "signal_count": result.signal_count,
        "total_return": _format_decimal(result.total_return),
        "annualized_return": _format_decimal(result.annualized_return),
        "max_drawdown": _format_decimal(result.max_drawdown),
        "volatility": _format_decimal(result.volatility),
        "sharpe_ratio": _format_decimal(result.sharpe_ratio),
    }


def _backtest_list_item_response(run: BacktestRun) -> dict[str, object]:
    return {
        "run_id": run.id,
        "strategy_id": run.strategy_id,
        "config_version": run.config_version,
        "start_date": run.start_date.isoformat(),
        "end_date": run.end_date.isoformat(),
        "status": run.status,
        "started_at": _format_datetime(run.started_at),
        "finished_at": _format_optional_datetime(run.finished_at),
        "total_return": _format_decimal(run.total_return),
        "annualized_return": _format_decimal(run.annualized_return),
        "max_drawdown": _format_decimal(run.max_drawdown),
        "volatility": _format_decimal(run.volatility),
        "sharpe_ratio": _format_decimal(run.sharpe_ratio),
    }


def _backtest_detail_run_response(run: BacktestRun) -> dict[str, object]:
    return {
        "run_id": run.id,
        "strategy_id": run.strategy_id,
        "config_version": run.config_version,
        "start_date": run.start_date.isoformat(),
        "end_date": run.end_date.isoformat(),
        "parameters_json": run.parameters_json,
        "status": run.status,
        "error_message": run.error_message,
        "started_at": _format_datetime(run.started_at),
        "finished_at": _format_optional_datetime(run.finished_at),
    }


def _backtest_metrics_response(run: BacktestRun) -> dict[str, object]:
    return {
        "total_return": _format_decimal(run.total_return),
        "annualized_return": _format_decimal(run.annualized_return),
        "max_drawdown": _format_decimal(run.max_drawdown),
        "volatility": _format_decimal(run.volatility),
        "sharpe_ratio": _format_decimal(run.sharpe_ratio),
    }


def _backtest_curve_point_response(row: BacktestEquityCurve) -> dict[str, object]:
    return {
        "trade_date": row.trade_date.isoformat(),
        "net_value": _format_decimal(row.net_value),
        "cash": _format_decimal(row.cash),
        "market_value": _format_decimal(row.market_value),
        "total_assets": _format_decimal(row.total_assets),
        "positions_json": row.positions_json,
    }


def _strategy_signal_position_response(position: GeneratedSignalPosition) -> dict[str, object]:
    return {
        "etf_id": position.etf_id,
        "exchange": position.exchange,
        "symbol": position.symbol,
        "target_weight": _format_decimal(position.target_weight),
        "rank": position.rank,
        "score": _format_decimal(position.score),
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


def _latest_strategy_signal_position_response(
    position: StrategySignalReportPosition,
) -> dict[str, object]:
    return {
        "exchange": position.exchange,
        "symbol": position.symbol,
        "name": position.name,
        "target_weight": _format_decimal(position.target_weight),
        "rank": position.rank,
        "score": _format_decimal(position.score),
        "is_fallback": position.is_fallback,
    }


def _strategy_signal_list_item_response(entry: StrategySignalListEntry) -> dict[str, object]:
    return {
        "signal_id": entry.signal_id,
        "signal_date": entry.signal_date.isoformat(),
        "config_version": entry.config_version,
        "result": entry.result,
        "generated_at": entry.generated_at,
        "is_fallback": entry.is_fallback,
        "position_count": entry.position_count,
    }


def _strategy_signal_detail_metadata_response(
    report: StrategySignalReport,
) -> dict[str, object]:
    return {
        "signal_id": report.signal_id,
        "signal_date": report.signal_date.isoformat(),
        "strategy_id": report.strategy_id,
        "config_version": report.config_version,
        "generated_at": report.generated_at,
        "result": report.result,
        "is_fallback": report.is_fallback,
    }


def _strategy_signal_detail_position_response(
    position: StrategySignalReportPosition,
) -> dict[str, object]:
    return {
        "exchange": position.exchange,
        "symbol": position.symbol,
        "name": position.name,
        "target_weight": _format_decimal(position.target_weight),
        "rank": position.rank,
        "score": _format_decimal(position.score),
        "is_fallback": position.is_fallback,
    }


def _format_decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _format_optional_datetime(value: datetime | None) -> str | None:
    return None if value is None else _format_datetime(value)


def _format_datetime(value: datetime) -> str:
    return value.replace(tzinfo=None).isoformat()


def _error_response(
    *,
    status_code: int,
    code: str,
    category: ErrorCategory,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "category": category,
                "message": message,
            }
        },
    )


def _http_exception_message(exc: HTTPException) -> str:
    return exc.detail if isinstance(exc.detail, str) else "HTTP request failed"


def _http_error_category(status_code: int) -> ErrorCategory:
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation"
    if status_code >= 500:
        return "unexpected"
    return "operation_failed"


def _http_error_code(status_code: int, message: str) -> str:
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation_error"
    if status_code >= 500:
        return "unexpected_error"

    known_operation_errors = {
        "No local market prices found": "no_market_data",
        "start_date must be on or before end_date": "invalid_date_range",
    }
    return known_operation_errors.get(message, "operation_failed")
