import uvicorn
from vela_core.logging import setup_logging


def main() -> None:
    setup_logging()
    uvicorn.run("vela_api.main:app", host="127.0.0.1", port=8000, reload=True)
