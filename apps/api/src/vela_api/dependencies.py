from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session
from vela_core import AppConfig, MarketDataProvider, TencentMarketDataProvider

from vela_api.database import get_database_session

DatabaseSession = Annotated[Session, Depends(get_database_session)]


def get_app_config(request: Request) -> AppConfig:
    return request.app.state.app_config


AppConfigDependency = Annotated[AppConfig, Depends(get_app_config)]


def get_market_data_provider() -> MarketDataProvider:
    return TencentMarketDataProvider()


MarketDataProviderDependency = Annotated[MarketDataProvider, Depends(get_market_data_provider)]
