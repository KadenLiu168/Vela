import logging

from fastapi.testclient import TestClient
from vela_api.main import app
from vela_core.errors import MissingMarketDataError


def test_request_ids_are_generated_preserved_and_sanitized(caplog) -> None:
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="vela_api.main"):
        generated = client.get("/api/health")
        accepted = client.get("/api/health", headers={"X-Request-ID": "request_42"})
        rejected = client.get("/api/health?token=secret", headers={"X-Request-ID": "bad value"})
        over_length = client.get("/api/health", headers={"X-Request-ID": "a" * 129})

    assert generated.headers["X-Request-ID"]
    assert accepted.headers["X-Request-ID"] == "request_42"
    assert rejected.headers["X-Request-ID"] != "bad value"
    assert over_length.headers["X-Request-ID"] != "a" * 129
    completion_messages = [
        record.getMessage()
        for record in caplog.records
        if record.msg.startswith("api.request.completed")
    ]
    assert len(completion_messages) == 4
    assert (
        f"request_id={generated.headers['X-Request-ID']} method=GET route=/api/health status=200"
        in completion_messages[0]
    )
    assert "duration_ms=" in completion_messages[0]
    assert "request_id=request_42 method=GET route=/api/health status=200" in completion_messages[1]
    assert f"request_id={rejected.headers['X-Request-ID']}" in completion_messages[2]
    assert f"request_id={over_length.headers['X-Request-ID']}" in completion_messages[3]
    assert "bad value" not in "\n".join(completion_messages)
    assert "token=secret" not in "\n".join(completion_messages)


def test_unclassified_value_error_is_safe_and_correlated(monkeypatch, caplog) -> None:
    def raise_value_error(*_args, **_kwargs):
        raise ValueError("No local market prices found")

    monkeypatch.setattr(
        "vela_api.signal_router.generate_and_persist_strategy_signal", raise_value_error
    )

    with caplog.at_level(logging.INFO):
        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/strategy-signals/generate", headers={"X-Request-ID": "request_500"}
        )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "request_500"
    assert response.json() == {
        "error": {
            "code": "unexpected_error",
            "category": "unexpected",
            "message": "Unexpected API error",
        }
    }
    diagnostics = [record for record in caplog.records if record.msg.startswith("api.unexpected")]
    assert len(diagnostics) == 1
    assert "request_500" in diagnostics[0].getMessage()
    assert "ValueError" in diagnostics[0].getMessage()
    completion_messages = [
        record.getMessage()
        for record in caplog.records
        if record.msg.startswith("api.request.completed")
    ]
    assert len(completion_messages) == 1
    assert (
        "request_id=request_500 method=POST route=/api/strategy-signals/generate status=500"
        in completion_messages[0]
    )
    assert "duration_ms=" in completion_messages[0]


def test_request_id_is_returned_for_validation_typed_and_http_errors(monkeypatch) -> None:
    def raise_missing_market_data(*_args, **_kwargs):
        raise MissingMarketDataError("No local market prices found")

    monkeypatch.setattr(
        "vela_api.signal_router.generate_and_persist_strategy_signal", raise_missing_market_data
    )
    client = TestClient(app, raise_server_exceptions=False)

    validation = client.post("/api/market-data/fetch?mode=invalid")
    typed = client.post("/api/strategy-signals/generate")
    explicit_http = client.post("/api/strategy-signals/generate?source=unsupported")

    assert validation.status_code == 422
    assert typed.status_code == 400
    assert explicit_http.status_code == 400
    assert validation.headers["X-Request-ID"]
    assert typed.headers["X-Request-ID"]
    assert explicit_http.headers["X-Request-ID"]
