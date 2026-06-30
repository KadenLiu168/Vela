from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from vela_core import (
    AkShareMarketDataProvider,
    GeneratedSignalPosition,
    GenerateStrategySignalResult,
    MarketDataFetchResult,
    MarketDataProvider,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
    generate_strategy_signal,
    get_dashboard_summary,
)
from vela_core.models import MarketPrice
from vela_core.strategy_config import load_strategy_config

from vela_api.config import DEFAULT_STRATEGY_CONFIG_PATH, get_config_summary
from vela_api.database import get_database_session, initialize_database

app = FastAPI(title="Vela API")
initialize_database(app)
DatabaseSession = Annotated[Session, Depends(get_database_session)]
MarketDataFetchMode = Literal["incremental", "full"]


def get_market_data_provider() -> MarketDataProvider:
    return AkShareMarketDataProvider()


MarketDataProviderDependency = Annotated[MarketDataProvider, Depends(get_market_data_provider)]


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


@app.post("/api/strategy-signals/generate")
def generate_strategy_signal_endpoint(
    session: DatabaseSession,
    signal_date: Annotated[date | None, Query(alias="signalDate")] = None,
) -> dict[str, object]:
    resolved_signal_date = signal_date or session.scalar(select(func.max(MarketPrice.trade_date)))
    if resolved_signal_date is None:
        raise HTTPException(status_code=400, detail="No local market prices found")

    config = load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)
    result = generate_strategy_signal(
        session,
        signal_date=resolved_signal_date,
        config=config,
    )
    return _strategy_signal_response(result)


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


def _strategy_signal_position_response(position: GeneratedSignalPosition) -> dict[str, object]:
    return {
        "etf_id": position.etf_id,
        "exchange": position.exchange,
        "symbol": position.symbol,
        "target_weight": _format_decimal(position.target_weight),
        "rank": position.rank,
        "score": _format_decimal(position.score),
    }


def _format_decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)
