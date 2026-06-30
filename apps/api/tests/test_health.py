from fastapi.routing import APIRoute
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
        (route.path, tuple(sorted(route.methods or ())))
        for route in app.routes
        if isinstance(route, APIRoute) and route.include_in_schema
    }

    assert routes == {
        ("/api/config", ("GET",)),
        ("/api/dashboard", ("GET",)),
        ("/api/health", ("GET",)),
        ("/api/market-data/fetch", ("POST",)),
        ("/api/strategy-signals/generate", ("POST",)),
    }


def test_api_command_starts_uvicorn(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(app_path: str, **kwargs: object) -> None:
        calls.append({"app_path": app_path, **kwargs})

    monkeypatch.setattr("vela_api.cli.uvicorn.run", fake_run)

    main()

    assert calls == [
        {
            "app_path": "vela_api.main:app",
            "host": "127.0.0.1",
            "port": 8000,
            "reload": True,
        }
    ]
