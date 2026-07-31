from fastapi import APIRouter
from vela_core import get_dashboard_summary

from vela_api.config import get_config_summary
from vela_api.dependencies import AppConfigDependency, DatabaseSession
from vela_api.schemas import ConfigResponse, DashboardResponse, HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/api/config", response_model=ConfigResponse)
def config(app_config: AppConfigDependency) -> dict[str, object]:
    return get_config_summary(app_config)


@router.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(session: DatabaseSession, app_config: AppConfigDependency) -> dict[str, object]:
    config_summary = get_config_summary(app_config)
    return get_dashboard_summary(session, strategy_summary=config_summary["strategy"])
