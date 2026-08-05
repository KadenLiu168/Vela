# ruff: noqa: E501

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
    BacktestEquityCurve,
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
            "official_sessions": ["2025-01-01", "2026-01-01", "2026-12-31"],
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


def _add_history_windows(
    session,
    *,
    strategy_id: str,
    finished_at: datetime,
    official_sessions: list[str],
    windows: list[tuple[int, date, date, date, list[tuple[date, Decimal]]]],
) -> WalkForwardRun:
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=len(windows),
        walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": official_sessions,
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
    for ordinal, train_start, test_start, test_end, curve in windows:
        oos = BacktestRun(
            strategy_id=strategy_id,
            config_version="wf-000000000001",
            start_date=test_start,
            end_date=test_end,
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
        oos.equity_curve.extend(
            BacktestEquityCurve(
                trade_date=trade_date,
                net_value=net_value,
                cash=Decimal("0"),
                market_value=Decimal("1"),
                total_assets=Decimal("1"),
                positions_json="[]",
            )
            for trade_date, net_value in curve
        )
        parent.windows.append(
            WalkForwardRunWindow(
                ordinal=ordinal,
                train_start=train_start,
                train_end=train_start,
                test_start=test_start,
                test_end=test_end,
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
    assert body["stitched_oos"] == {
        "status": "available",
        "initial_net_value": "1.000000",
        "ending_net_value": "1.000000",
        "total_return": "0.000000",
        "points": [
            {
                "trade_date": "2026-01-01",
                "net_value": "1.000000",
                "window_ordinal": 0,
                "is_window_start": True,
            },
            {
                "trade_date": "2026-12-31",
                "net_value": "1.000000",
                "window_ordinal": 0,
                "is_window_start": False,
            },
        ],
    }
    openapi = client.get("/openapi.json").json()
    assert (
        "stitched_oos"
        in openapi["components"]["schemas"]["WalkForwardDetailResponse"]["properties"]
    )
    stitched_schema = openapi["components"]["schemas"]["StitchedOosResponse"]
    assert set(stitched_schema["properties"]) == {
        "status",
        "initial_net_value",
        "ending_net_value",
        "total_return",
        "points",
    }
    assert set(stitched_schema["properties"]["status"]["enum"]) == {
        "available",
        "unavailable_non_contiguous_windows",
    }
    point_schema = openapi["components"]["schemas"]["StitchedOosPointResponse"]
    assert set(point_schema["properties"]) == {
        "trade_date",
        "net_value",
        "window_ordinal",
        "is_window_start",
    }
    assert point_schema["properties"]["window_ordinal"]["type"] == "integer"
    assert point_schema["properties"]["is_window_start"]["type"] == "boolean"
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


def test_walk_forward_detail_fails_closed_on_corrupt_eligible_curve(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-curve-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        for point in parent.windows[0].oos_backtest_run.equity_curve:
            session.delete(point)
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
    assert response.json()["error"]["category"] == "unexpected"


def test_walk_forward_detail_stitches_adjacent_windows_with_compounding(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-stitched.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history_windows(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            official_sessions=[
                "2025-01-01",
                "2026-01-01",
                "2026-06-30",
                "2026-07-01",
                "2026-12-31",
            ],
            windows=[
                (
                    0,
                    date(2025, 1, 1),
                    date(2026, 1, 1),
                    date(2026, 6, 30),
                    [
                        (date(2026, 1, 1), Decimal("1.000000")),
                        (date(2026, 6, 30), Decimal("1.100000")),
                    ],
                ),
                (
                    1,
                    date(2026, 1, 1),
                    date(2026, 7, 1),
                    date(2026, 12, 31),
                    [
                        (date(2026, 7, 1), Decimal("1.000000")),
                        (date(2026, 12, 31), Decimal("0.900000")),
                    ],
                ),
            ],
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["stitched_oos"] == {
        "status": "available",
        "initial_net_value": "1.000000",
        "ending_net_value": "0.990000",
        "total_return": "-0.010000",
        "points": [
            {
                "trade_date": "2026-01-01",
                "net_value": "1.000000",
                "window_ordinal": 0,
                "is_window_start": True,
            },
            {
                "trade_date": "2026-06-30",
                "net_value": "1.100000",
                "window_ordinal": 0,
                "is_window_start": False,
            },
            {
                "trade_date": "2026-07-01",
                "net_value": "1.100000",
                "window_ordinal": 1,
                "is_window_start": True,
            },
            {
                "trade_date": "2026-12-31",
                "net_value": "0.990000",
                "window_ordinal": 1,
                "is_window_start": False,
            },
        ],
    }


def test_walk_forward_detail_reports_unavailable_for_non_contiguous_windows(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-gap.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history_windows(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            official_sessions=[
                "2025-01-01",
                "2026-01-01",
                "2026-06-30",
                "2026-07-15",
                "2026-09-01",
                "2026-12-31",
            ],
            windows=[
                (
                    0,
                    date(2025, 1, 1),
                    date(2026, 1, 1),
                    date(2026, 6, 30),
                    [
                        (date(2026, 1, 1), Decimal("1.000000")),
                        (date(2026, 6, 30), Decimal("1.100000")),
                    ],
                ),
                (
                    1,
                    date(2026, 1, 1),
                    date(2026, 9, 1),
                    date(2026, 12, 31),
                    [
                        (date(2026, 9, 1), Decimal("1.000000")),
                        (date(2026, 12, 31), Decimal("0.900000")),
                    ],
                ),
            ],
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["stitched_oos"] == {
        "status": "unavailable_non_contiguous_windows",
        "initial_net_value": None,
        "ending_net_value": None,
        "total_return": None,
        "points": [],
    }
    assert len(body["windows"]) == 2
    assert [window["ordinal"] for window in body["windows"]] == [0, 1]
    assert body["windows"][1]["oos_backtest"]["total_return"] == "0.100000"
    assert [item["key"] for item in body["windows"][0]["oos_backtest"]["benchmarks"]] == [
        "equal_weight_monthly",
        "csi_300_buy_hold",
    ]


def test_walk_forward_detail_fails_closed_on_missing_session_bound(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-session-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history_windows(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            official_sessions=["2025-01-01", "2026-01-01"],
            windows=[
                (
                    0,
                    date(2025, 1, 1),
                    date(2026, 1, 1),
                    date(2026, 12, 31),
                    [
                        (date(2026, 1, 1), Decimal("1.000000")),
                        (date(2026, 12, 31), Decimal("1.100000")),
                    ],
                ),
            ],
        )
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
