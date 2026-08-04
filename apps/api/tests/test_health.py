from fastapi.testclient import TestClient
from vela_api.cli import main
from vela_api.main import app


def test_health_endpoint_reports_healthy_status() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_skeleton_exposes_health_and_config_endpoints() -> None:
    routes = {
        (path, tuple(sorted(method.upper() for method in operations)))
        for path, operations in app.openapi()["paths"].items()
    }

    assert routes == {
        ("/api/backtests", ("GET",)),
        ("/api/backtests/{run_id}", ("GET",)),
        ("/api/backtests/{run_id}/signals", ("GET",)),
        ("/api/backtests/run", ("POST",)),
        ("/api/config", ("GET",)),
        ("/api/dashboard", ("GET",)),
        ("/api/etfs/{etf_id}/prices", ("GET",)),
        ("/api/health", ("GET",)),
        ("/api/market-data/fetch", ("POST",)),
        ("/api/setup/bootstrap", ("POST",)),
        ("/api/strategy-signals", ("GET",)),
        ("/api/strategy-signals/{signal_id}", ("GET",)),
        ("/api/strategy-signals/generate", ("POST",)),
        ("/api/strategy-signals/latest", ("GET",)),
        ("/api/walk-forwards", ("GET",)),
        ("/api/walk-forwards/{run_id}", ("GET",)),
    }


def test_api_command_starts_uvicorn(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    logging_initialized: list[bool] = []

    def fake_run(app_path: str, **kwargs: object) -> None:
        calls.append({"app_path": app_path, **kwargs})

    monkeypatch.setattr("vela_api.cli.uvicorn.run", fake_run)
    monkeypatch.setattr("vela_api.cli.setup_logging", lambda: logging_initialized.append(True))

    main()

    assert calls == [
        {
            "app_path": "vela_api.main:app",
            "host": "127.0.0.1",
            "port": 8000,
            "reload": True,
        }
    ]
    assert logging_initialized == [True]
