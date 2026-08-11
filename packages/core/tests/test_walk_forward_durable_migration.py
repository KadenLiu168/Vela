from __future__ import annotations

from pathlib import Path

import alembic.command
import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).parents[3]


def _config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _insert_parent(connection, *, strategy_id: str, status: str) -> int:
    result = connection.execute(
        text(
            "INSERT INTO walk_forward_run "
            "(strategy_id, start_date, end_date, window_count, walk_forward_config_json, "
            "base_strategy_config_json, provenance_version, config_checksum, "
            "input_data_snapshot_json, input_data_checksum, evidence_version, evidence_json, "
            "status, error_message, started_at, finished_at) VALUES "
            "(:strategy_id, '2026-01-01', '2026-12-31', 0, '{}', '{}', 'wf_provenance_v1', "
            "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', '{}', "
            "'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', "
            "'wf_evidence_v3', '{}', :status, NULL, '2026-01-01 00:00:00', :finished_at) "
            "RETURNING id"
        ),
        {
            "strategy_id": strategy_id,
            "status": status,
            "finished_at": None if status == "running" else "2026-01-02 00:00:00",
        },
    )
    return int(result.scalar_one())


def test_durable_migration_adds_columns_and_partial_indexes(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'durable-head.db'}"
    alembic.command.upgrade(_config(database_url), "20260807_0018")

    engine = create_engine(database_url)
    alembic.command.upgrade(_config(database_url), "head")

    with engine.connect() as connection:
        columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(walk_forward_run)"))
        }
        assert {
            "attempt_count",
            "claimed_at",
            "heartbeat_at",
            "lease_expires_at",
            "worker_id",
            "claim_token",
        } <= columns
        indexes = {
            row[1] for row in connection.execute(text("PRAGMA index_list(walk_forward_run)"))
        }
        assert "uq_walk_forward_run_active_strategy" in indexes
        assert "uq_walk_forward_run_sqlite_running" in indexes

        _insert_parent(connection, strategy_id="demo", status="queued")
        connection.commit()
        with pytest.raises(IntegrityError):
            _insert_parent(connection, strategy_id="demo", status="running")
        connection.rollback()

        _insert_parent(connection, strategy_id="other", status="running")
        connection.commit()
        with pytest.raises(IntegrityError):
            _insert_parent(connection, strategy_id="third", status="running")
        connection.rollback()


def test_durable_migration_preserves_terminal_history_and_fails_legacy_running(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'durable-cutover.db'}"
    alembic.command.upgrade(_config(database_url), "20260807_0018")
    engine = create_engine(database_url)

    with engine.begin() as connection:
        success_id = _insert_parent(connection, strategy_id="success", status="success")
        running_id = _insert_parent(connection, strategy_id="running", status="running")

    alembic.command.upgrade(_config(database_url), "head")

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT id, status, attempt_count, worker_id, claim_token, "
                "finished_at, error_message "
                "FROM walk_forward_run ORDER BY id"
            )
        ).fetchall()
        assert rows[0] == (success_id, "success", 0, None, None, "2026-01-02 00:00:00", None)
        assert rows[1][0:5] == (running_id, "failed", 0, None, None)
        assert rows[1][5] is not None
        assert rows[1][6] == "migration_interrupted: legacy running claim was not durable"
