from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import (
    BacktestBenchmark,
    BacktestRun,
    WalkForwardRun,
    WalkForwardRunWindow,
)

from tests.integration_data import prepare_sqlite_database


def _summary() -> dict[str, object]:
    return {
        "mean": 0.1,
        "median": 0.1,
        "min": 0.1,
        "max": 0.1,
        "std": 0.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }


def _evidence() -> dict[str, object]:
    summary = _summary()
    rate = {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }
    benchmark = {
        "total_return_difference": summary,
        "annualized_return_difference": summary,
        "tracking_error": summary,
        "information_ratio": summary,
        "outperformance_rate": rate,
    }
    return {
        "metrics": {
            key: summary
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
        "positive_window_rate": rate,
        "generalization_gap": summary,
        "benchmarks": {
            "equal_weight_monthly": benchmark,
            "csi_300_buy_hold": benchmark,
        },
        "parameter_stability": {},
    }


def _add_history(session, *, strategy_id: str, finished_at: datetime) -> WalkForwardRun:
    oos = BacktestRun(
        strategy_id=strategy_id,
        config_version="wf-000000000001",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        parameters_json="{}",
        started_at=finished_at,
        finished_at=finished_at,
        status="success",
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.100000"),
        max_drawdown=Decimal("-0.050000"),
        volatility=Decimal("0.100000"),
        sharpe_ratio=Decimal("1.000000"),
        sortino_ratio=Decimal("1.200000"),
        calmar_ratio=Decimal("2.000000"),
        longest_drawdown_duration_sessions=3,
        longest_drawdown_peak_date=date(2026, 2, 2),
        longest_drawdown_trough_date=date(2026, 2, 3),
    )
    oos.benchmarks.extend(
        [
            BacktestBenchmark(
                benchmark_key=key,
                display_name=key,
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
                sortino_ratio=Decimal("1.100000"),
                calmar_ratio=Decimal("1.900000"),
                longest_drawdown_duration_sessions=2,
                longest_drawdown_peak_date=date(2026, 2, 2),
                longest_drawdown_trough_date=date(2026, 2, 3),
                longest_drawdown_recovery_date=date(2026, 2, 4),
                tracking_error=Decimal("0.020000"),
                information_ratio=Decimal("0.300000"),
            )
            for key in ("equal_weight_monthly", "csi_300_buy_hold")
        ]
    )
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=1,
        walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2025-01-01", "2026-12-31"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v1",
        evidence_json=_evidence(),
        started_at=finished_at,
        finished_at=finished_at,
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
    session.flush()
    return parent


def test_walk_forward_history_api_returns_typed_current_strategy_page_and_detail(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-api.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        current = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        older = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 1, tzinfo=UTC),
        )
        foreign = _add_history(
            session,
            strategy_id="other",
            finished_at=datetime(2026, 2, 3, tzinfo=UTC),
        )
        session.commit()
        current_id, older_id, foreign_id = current.id, older.id, foreign.id

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        page = client.get("/api/walk-forwards?limit=10&offset=0")
        offset_page = client.get("/api/walk-forwards?limit=1&offset=1")
        detail = client.get(f"/api/walk-forwards/{current_id}")
        foreign_detail = client.get(f"/api/walk-forwards/{foreign_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert [item["run_id"] for item in page.json()["runs"]] == [current_id, older_id]
    assert offset_page.status_code == 200
    assert offset_page.json()["total"] == 2
    assert offset_page.json()["limit"] == 1
    assert offset_page.json()["offset"] == 1
    assert [item["run_id"] for item in offset_page.json()["runs"]] == [older_id]
    assert b"strategyId" not in page.request.url.query
    assert detail.status_code == 200
    body = detail.json()
    assert body["run"]["provenance_version"] == "wf_provenance_v1"
    assert body["evidence_version"] == "wf_evidence_v1"
    assert body["configuration"]["config_checksum"] == "a" * 64
    assert body["input_provenance"]["manifest"]["following_session"] is None
    assert set(body["evidence"]["metrics"]) == {
        "total_return",
        "annualized_return",
        "sharpe_ratio",
        "max_drawdown",
        "volatility",
        "sortino_ratio",
        "calmar_ratio",
        "longest_drawdown_duration_sessions",
    }
    assert set(body["evidence"]["benchmarks"]) == {
        "equal_weight_monthly",
        "csi_300_buy_hold",
    }
    assert body["windows"][0]["train_sharpe"] == "1.100000"
    assert body["windows"][0]["oos_backtest"]["sortino_ratio"] == "1.200000"
    assert [item["key"] for item in body["windows"][0]["oos_backtest"]["benchmarks"]] == [
        "equal_weight_monthly",
        "csi_300_buy_hold",
    ]
    assert "equity_curve" not in str(body)
    assert foreign_detail.status_code == 404
    assert foreign_detail.json()["error"]["category"] == "not_found"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_walk_forward_history_api_rejects_invalid_pagination(tmp_path, query: str) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-pagination.db'}"
    prepare_sqlite_database(database_url)
    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards?{query}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert response.json()["error"]["category"] == "validation"


def test_walk_forward_detail_fails_closed_on_foreign_oos_ownership(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        parent.windows[0].oos_backtest_run.strategy_id = "other"
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app, raise_server_exceptions=False).get(
            f"/api/walk-forwards/{run_id}"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "unexpected_error",
            "category": "unexpected",
            "message": "Unexpected API error",
        }
    }
