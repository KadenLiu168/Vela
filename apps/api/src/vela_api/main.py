from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from vela_core import (
    AkShareMarketDataProvider,
    MarketDataFetchResult,
    MarketDataProvider,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
    get_dashboard_summary,
)

from vela_api.config import get_config_summary
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
