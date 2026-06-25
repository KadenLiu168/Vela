from fastapi import FastAPI

app = FastAPI(title="Vela API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
