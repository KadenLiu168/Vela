from fastapi import FastAPI

from vela_api.database import initialize_database

app = FastAPI(title="Vela API")
initialize_database(app)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
