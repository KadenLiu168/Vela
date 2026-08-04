from __future__ import annotations

from pathlib import Path

import alembic.command
import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from vela_core.migration import run_alembic_upgrade

ROOT = Path(__file__).parents[3]


def _alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _evidence_owner_snapshot(engine: Engine) -> dict[str, list[tuple[object, ...]]]:
    statements = {
        "backtest_run": text("SELECT * FROM backtest_run ORDER BY id"),
        "strategy_signal": text("SELECT * FROM strategy_signal ORDER BY id"),
        "backtest_equity_curve": text("SELECT * FROM backtest_equity_curve ORDER BY id"),
        "backtest_benchmark": text("SELECT * FROM backtest_benchmark ORDER BY id"),
        "backtest_benchmark_equity_curve": text(
            "SELECT * FROM backtest_benchmark_equity_curve ORDER BY id"
        ),
    }
    with engine.connect() as connection:
        return {
            table: [tuple(row) for row in connection.execute(statement)]
            for table, statement in statements.items()
        }


def test_walk_forward_migration_round_trip_preserves_backtest_rows(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'migration.db'}"
    alembic.command.upgrade(_alembic_config(database_url), "20260804_0014")
    engine = create_engine(database_url)

    with engine.begin() as connection:
        backtest_id = connection.execute(
            text(
                "INSERT INTO backtest_run "
                "(strategy_id, config_version, start_date, end_date, parameters_json, "
                "started_at, finished_at, status, total_return) "
                "VALUES ('demo', 'wf-test', '2026-01-01', '2026-01-02', '{}', "
                "'2026-01-02 00:00:00', '2026-01-03 00:00:00', 'success', 0.1) "
                "RETURNING id"
            )
        ).scalar_one()
        second_backtest_id = connection.execute(
            text(
                "INSERT INTO backtest_run "
                "(strategy_id, config_version, start_date, end_date, parameters_json, "
                "started_at, finished_at, status) VALUES "
                "('demo', 'legacy-v1', '2026-02-01', '2026-02-02', '{}', "
                "'2026-02-02 00:00:00', '2026-02-03 00:00:00', 'success') RETURNING id"
            )
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO backtest_equity_curve "
                "(backtest_run_id, trade_date, net_value, cash, market_value, total_assets, "
                "positions_json) VALUES (:backtest_id, '2026-01-02', 1.1, 10, 90, 100, '{}')"
            ),
            {"backtest_id": backtest_id},
        )
        connection.execute(
            text(
                "INSERT INTO strategy_signal "
                "(signal_date, strategy_id, config_version, source, backtest_run_id, "
                "generated_at, status, result) VALUES "
                "('2026-01-02', 'demo', 'wf-test', 'backtest', :backtest_id, "
                "'2026-01-02 00:00:00', 'success', 'hold')"
            ),
            {"backtest_id": backtest_id},
        )
        benchmark_id = connection.execute(
            text(
                "INSERT INTO backtest_benchmark "
                "(backtest_run_id, benchmark_key, display_name, total_return) VALUES "
                "(:backtest_id, 'equal_weight_monthly', 'Equal Weight', 0.08) RETURNING id"
            ),
            {"backtest_id": backtest_id},
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO backtest_benchmark_equity_curve "
                "(benchmark_id, trade_date, net_value) VALUES "
                "(:benchmark_id, '2026-01-02', 1.08)"
            ),
            {"benchmark_id": benchmark_id},
        )

    evidence_owner_snapshot = _evidence_owner_snapshot(engine)
    run_alembic_upgrade(database_url, ROOT / "alembic")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM walk_forward_run")).scalar_one() == 0
        assert connection.execute(text("SELECT COUNT(*) FROM backtest_run")).scalar_one() == 2
        assert connection.execute(text("SELECT COUNT(*) FROM strategy_signal")).scalar_one() == 1
        assert (
            connection.execute(text("SELECT COUNT(*) FROM backtest_equity_curve")).scalar_one() == 1
        )
        assert connection.execute(text("SELECT COUNT(*) FROM backtest_benchmark")).scalar_one() == 1
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM backtest_benchmark_equity_curve")
            ).scalar_one()
            == 1
        )

    with engine.begin() as connection:
        parent_id = connection.execute(
            text(
                "INSERT INTO walk_forward_run "
                "(strategy_id, start_date, end_date, window_count, walk_forward_config_json, "
                "base_strategy_config_json, provenance_version, config_checksum, "
                "input_data_snapshot_json, input_data_checksum, evidence_version, evidence_json, "
                "started_at, finished_at) VALUES "
                "('demo', '2026-01-01', '2026-12-31', 1, '{}', '{}', 'wf_provenance_v1', "
                "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', '{}', "
                "'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', "
                "'wf_evidence_v1', '{}', '2026-01-01 00:00:00', '2026-01-02 00:00:00') "
                "RETURNING id"
            )
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO walk_forward_run_window "
                "(walk_forward_run_id, ordinal, train_start, train_end, test_start, test_end, "
                "oos_version, selected_parameters_json, candidate_count, eligible_count, "
                "skipped_count, skip_reason_counts_json, train_sharpe, oos_backtest_run_id) "
                "VALUES (:parent_id, 0, '2025-01-01', '2025-12-31', '2026-01-01', '2026-12-31', "
                "'wf-test', '{}', 1, 1, 0, '{}', 1.2, :backtest_id)"
            ),
            {"parent_id": parent_id, "backtest_id": backtest_id},
        )

    invalid_windows = (
        (1, 1, 0, 999),
        (0, 1, 0, second_backtest_id),
        (1, 1, 0, backtest_id),
        (1, -1, 2, second_backtest_id),
        (1, 1, 1, second_backtest_id),
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()
        for ordinal, eligible_count, skipped_count, oos_id in invalid_windows:
            with pytest.raises(IntegrityError):
                connection.execute(
                    text(
                        "INSERT INTO walk_forward_run_window "
                        "(walk_forward_run_id, ordinal, train_start, train_end, test_start, "
                        "test_end, oos_version, selected_parameters_json, candidate_count, "
                        "eligible_count, skipped_count, skip_reason_counts_json, "
                        "oos_backtest_run_id) VALUES "
                        "(:parent_id, :ordinal, '2025-01-01', '2025-12-31', '2026-01-01', "
                        "'2026-12-31', 'wf-test-2', '{}', 1, :eligible_count, "
                        ":skipped_count, '{}', :oos_id)"
                    ),
                    {
                        "parent_id": parent_id,
                        "ordinal": ordinal,
                        "eligible_count": eligible_count,
                        "skipped_count": skipped_count,
                        "oos_id": oos_id,
                    },
                )
                connection.commit()
            connection.rollback()

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO walk_forward_run "
                    "(strategy_id, start_date, end_date, window_count, "
                    "walk_forward_config_json, base_strategy_config_json, provenance_version, "
                    "config_checksum, input_data_snapshot_json, input_data_checksum, "
                    "evidence_version, evidence_json, started_at, finished_at) VALUES "
                    "('demo', '2026-01-01', '2026-12-31', -1, '{}', '{}', "
                    "'wf_provenance_v1', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    "aaaaaaaaaaaaaaaa', '{}', 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                    "bbbbbbbbbbbbbbbb', 'wf_evidence_v1', '{}', '2026-01-01 00:00:00', "
                    "'2026-01-02 00:00:00')"
                )
            )
            connection.commit()
        connection.rollback()

    alembic.command.downgrade(_alembic_config(database_url), "20260804_0014")
    tables = set(inspect(engine).get_table_names())
    assert "walk_forward_run" not in tables
    assert "walk_forward_run_window" not in tables
    assert _evidence_owner_snapshot(engine) == evidence_owner_snapshot
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM backtest_run")).scalar_one() == 2
        assert connection.execute(
            text("SELECT id FROM backtest_run ORDER BY id")
        ).scalars().all() == [backtest_id, second_backtest_id]
        assert connection.execute(text("SELECT COUNT(*) FROM strategy_signal")).scalar_one() == 1
        assert (
            connection.execute(text("SELECT COUNT(*) FROM backtest_equity_curve")).scalar_one() == 1
        )
        assert connection.execute(text("SELECT COUNT(*) FROM backtest_benchmark")).scalar_one() == 1
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM backtest_benchmark_equity_curve")
            ).scalar_one()
            == 1
        )
