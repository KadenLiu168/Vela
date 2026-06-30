from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from vela_core import get_dashboard_summary

from vela_api.config import get_config_summary
from vela_api.database import get_database_session, initialize_database

app = FastAPI(title="Vela API")
initialize_database(app)
DatabaseSession = Annotated[Session, Depends(get_database_session)]


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
