# ruff: noqa: E501

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from vela_api import walk_forward_router as router_module
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import (
    BacktestBenchmark,
    BacktestEquityCurve,
    BacktestRun,
    WalkForwardRun,
    WalkForwardRunWindow,
)

from tests.integration_data import prepare_sqlite_database

_STRATEGY_ID = "Dual_momentum"


def _manifest() -> dict[str, object]:
    return {
        "version": "wf_provenance_v1",
        "earliest_required_session": "2025-01-01",
        "configured_end_date": "2026-12-31",
        "following_session": None,
        "official_sessions": ["2025-01-01", "2026-01-01", "2026-12-31"],
        "active_etfs": [],
        "loaded_price_row_count": 0,
        "first_loaded_price_date": None,
        "last_loaded_price_date": None,
    }


def _running_row(session_factory, *, started_at: datetime) -> int:
    with session_factory() as session:
        row = WalkForwardRun(
            strategy_id=_STRATEGY_ID,
            start_date=date(2025, 1, 1),
            end_date=date(2026, 12, 31),
            window_count=0,
            walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
            base_strategy_config_json={"strategy_id": _STRATEGY_ID},
            provenance_version="wf_provenance_v1",
            config_checksum="a" * 64,
            input_data_snapshot_json=_manifest(),
            input_data_checksum="b" * 64,
            evidence_version="wf_evidence_v3",
            evidence_json={},
            status="running",
            started_at=started_at,
            finished_at=None,
        )
        session.add(row)
        session.commit()
        return row.id


def _success_row(session_factory) -> int:
    with session_factory() as session:
        oos = BacktestRun(
            strategy_id=_STRATEGY_ID,
            config_version="wf-000000000001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            parameters_json="{}",
            started_at=datetime(2026, 2, 2, tzinfo=UTC),
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            status="success",
            total_return=Decimal("0.100000"),
            annualized_return=Decimal("0.100000"),
            max_drawdown=Decimal("-0.050000"),
            volatility=Decimal("0.100000"),
            sharpe_ratio=Decimal("1.000000"),
        )
        oos.benchmarks.extend(
            BacktestBenchmark(
                benchmark_key=key,
                display_name=key,
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
            )
            for key in ("equal_weight_monthly", "csi_300_buy_hold")
        )
        oos.equity_curve.extend(
            BacktestEquityCurve(
                trade_date=trade_date,
                net_value=Decimal("1.000000"),
                cash=Decimal("0"),
                market_value=Decimal("1"),
                total_assets=Decimal("1"),
                positions_json="[]",
            )
            for trade_date in (date(2026, 1, 1), date(2026, 12, 31))
        )
        parent = WalkForwardRun(
            strategy_id=_STRATEGY_ID,
            start_date=date(2025, 1, 1),
            end_date=date(2026, 12, 31),
            window_count=1,
            walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
            base_strategy_config_json={"strategy_id": _STRATEGY_ID},
            provenance_version="wf_provenance_v1",
            config_checksum="a" * 64,
            input_data_snapshot_json=_manifest(),
            input_data_checksum="b" * 64,
            evidence_version="wf_evidence_v1",
            evidence_json={
                "metrics": {
                    key: {
                        "mean": 0.1,
                        "median": 0.1,
                        "min": 0.05,
                        "max": 0.15,
                        "std": 0.04,
                        "window_count": 1,
                        "valid_count": 1,
                        "evidence_status": "insufficient_evidence",
                    }
                    for key in (
                        "total_return",
                        "annualized_return",
                        "sharpe_ratio",
                        "max_drawdown",
                        "volatility",
                        "sortino_ratio",
                        "calmar_ratio",
                        "longest_drawdown_duration_sessions",
                    )
                },
                "positive_window_rate": {
                    "numerator": 1,
                    "denominator": 1,
                    "value": 1.0,
                    "window_count": 1,
                    "valid_count": 1,
                    "evidence_status": "insufficient_evidence",
                },
                "generalization_gap": {
                    "mean": 0.1,
                    "median": 0.1,
                    "min": 0.05,
                    "max": 0.15,
                    "std": 0.04,
                    "window_count": 1,
                    "valid_count": 1,
                    "evidence_status": "insufficient_evidence",
                },
                "benchmarks": {
                    benchmark: {
                        "total_return_difference": {
                            "mean": 0.1,
                            "median": 0.1,
                            "min": 0.05,
                            "max": 0.15,
                            "std": 0.04,
                            "window_count": 1,
                            "valid_count": 1,
                            "evidence_status": "insufficient_evidence",
                        },
                        "annualized_return_difference": {
                            "mean": 0.1,
                            "median": 0.1,
                            "min": 0.05,
                            "max": 0.15,
                            "std": 0.04,
                            "window_count": 1,
                            "valid_count": 1,
                            "evidence_status": "insufficient_evidence",
                        },
                        "tracking_error": {
                            "mean": 0.1,
                            "median": 0.1,
                            "min": 0.05,
                            "max": 0.15,
                            "std": 0.04,
                            "window_count": 1,
                            "valid_count": 1,
                            "evidence_status": "insufficient_evidence",
                        },
                        "information_ratio": {
                            "mean": 0.1,
                            "median": 0.1,
                            "min": 0.05,
                            "max": 0.15,
                            "std": 0.04,
                            "window_count": 1,
                            "valid_count": 1,
                            "evidence_status": "insufficient_evidence",
                        },
                        "outperformance_rate": {
                            "numerator": 1,
                            "denominator": 1,
                            "value": 1.0,
                            "window_count": 1,
                            "valid_count": 1,
                            "evidence_status": "insufficient_evidence",
                        },
                    }
                    for benchmark in ("equal_weight_monthly", "csi_300_buy_hold")
                },
                "parameter_stability": {},
            },
            status="success",
            started_at=datetime(2026, 2, 2, tzinfo=UTC),
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        parent.windows.append(
            WalkForwardRunWindow(
                ordinal=0,
                train_start=date(2025, 1, 1),
                train_end=date(2025, 12, 31),
                test_start=date(2026, 1, 1),
                test_end=date(2026, 12, 31),
                oos_version="wf-000000000001",
                selected_parameters_json={"parameters.selection.top_n": 1},
                candidate_count=1,
                eligible_count=1,
                skipped_count=0,
                skip_reason_counts_json={},
                train_sharpe=Decimal("1.100000"),
                oos_backtest_run=oos,
            )
        )
        session.add(parent)
        session.commit()
        return parent.id


def test_run_trigger_accepts_run_and_returns_running_identity(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-accepted.db'}"
    session_factory = prepare_sqlite_database(database_url)

    def fake_begin(*, database_url: str, config_path: Path) -> int:
        return _running_row(session_factory, started_at=datetime.now(UTC))

    monkeypatch.setattr(router_module, "_begin_walk_forward_run", fake_begin)
    monkeypatch.setattr(router_module, "_complete_walk_forward_run", lambda **kwargs: None)
    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).post("/api/walk-forwards/run")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 202
    body = response.json()
    assert body["walk_forward_run_id"] > 0
    with session_factory() as session:
        row = session.get(WalkForwardRun, body["walk_forward_run_id"])
        assert row is not None
        assert row.status == "running"
        assert row.started_at is not None
        assert row.finished_at is None


def test_run_trigger_missing_market_data_returns_400_without_running_row(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-no-market-data.db'}"
    prepare_sqlite_database(database_url)
    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).post("/api/walk-forwards/run")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 400
    assert response.json()["error"]["category"] == "operation_failed"
    with prepare_sqlite_database(database_url)() as session:
        assert session.query(WalkForwardRun).count() == 0


def test_run_trigger_rejects_client_supplied_config_path(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-reject-path.db'}"
    session_factory = prepare_sqlite_database(database_url)
    begin_calls: list[tuple[str, Path]] = []

    def fake_begin(*, database_url: str, config_path: Path) -> int:
        begin_calls.append((database_url, config_path))
        return 7

    monkeypatch.setattr(router_module, "_begin_walk_forward_run", fake_begin)
    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        query_response = client.post("/api/walk-forwards/run?configPath=/etc/passwd")
        body_response = client.post("/api/walk-forwards/run", json={"configPath": "/etc/passwd"})
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert query_response.status_code == 422
    assert query_response.json()["error"]["category"] == "validation"
    assert body_response.status_code == 422
    assert body_response.json()["error"]["category"] == "validation"
    assert begin_calls == []
    with session_factory() as session:
        assert session.query(WalkForwardRun).count() == 0


def test_run_trigger_rejects_concurrent_non_stale_running_record(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-concurrent.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _running_row(session_factory, started_at=datetime.now(UTC))
    begin_calls: list[Path] = []

    def fake_begin(*, database_url: str, config_path: Path) -> int:
        begin_calls.append(config_path)
        return 7

    monkeypatch.setattr(router_module, "_begin_walk_forward_run", fake_begin)
    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).post("/api/walk-forwards/run")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 409
    assert response.json()["error"]["category"] == "operation_failed"
    assert begin_calls == []


def test_run_trigger_legacy_success_row_reports_backfilled_status(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-legacy.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _success_row(session_factory)
    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
        page = TestClient(app).get("/api/walk-forwards?limit=10&offset=0")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json()["run"]["status"] == "success"
    assert response.json()["run"]["error_message"] is None
    assert page.status_code == 200
    assert page.json()["runs"][0]["status"] == "success"
