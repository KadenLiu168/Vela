from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from vela_core import (
    BootstrapResult,
    MarketDataFetchResult,
    PriceTrendRange,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
    get_etf_price_trend,
    load_app_config,
    run_local_setup_bootstrap,
)

from vela_api.config import DEFAULT_ALEMBIC_SCRIPT_LOCATION, DEFAULT_STRATEGY_CONFIG_PATH
from vela_api.dependencies import DatabaseSession, MarketDataProviderDependency
from vela_api.schemas import BootstrapResponse, EtfPriceTrendResponse, MarketDataFetchResponse

router = APIRouter()
MarketDataFetchMode = Literal["incremental", "full"]


@router.get("/api/etfs/{etf_id}/prices", response_model=EtfPriceTrendResponse)
def etf_price_trend_endpoint(
    etf_id: int,
    session: DatabaseSession,
    range_: Annotated[PriceTrendRange, Query(alias="range")] = "1y",
) -> dict[str, object]:
    result = get_etf_price_trend(session, etf_id=etf_id, range_=range_)
    if result is None:
        raise HTTPException(status_code=404, detail="ETF not found")
    return result.to_dict()


@router.post("/api/market-data/fetch", response_model=MarketDataFetchResponse)
def fetch_market_data(
    mode: MarketDataFetchMode, session: DatabaseSession, provider: MarketDataProviderDependency
) -> dict[str, object]:
    result = (
        fetch_incremental_market_prices(session, provider=provider)
        if mode == "incremental"
        else fetch_full_market_prices(session, provider=provider)
    )
    return _market_data_fetch_response(result)


@router.post("/api/setup/bootstrap", response_model=BootstrapResponse)
def setup_bootstrap(
    request: Request, session: DatabaseSession, provider: MarketDataProviderDependency
) -> dict[str, object]:
    app_config = load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)
    result = run_local_setup_bootstrap(
        session,
        provider=provider,
        app_config=app_config,
        database_url=request.app.state.database_url,
        script_location=DEFAULT_ALEMBIC_SCRIPT_LOCATION,
    )
    return _bootstrap_response(result)


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
