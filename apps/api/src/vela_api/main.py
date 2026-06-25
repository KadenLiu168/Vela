from fastapi import FastAPI

from vela_api.config import get_config_summary
from vela_api.database import initialize_database

app = FastAPI(title="Vela API")
initialize_database(app)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/config")
def config() -> dict[str, object]:
    return get_config_summary()
