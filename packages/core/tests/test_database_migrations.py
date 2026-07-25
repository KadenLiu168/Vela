import importlib.util
from pathlib import Path
from typing import Any

import alembic.command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from vela_core.models import Base

ROOT = Path(__file__).parents[3]
CURRENT_TABLES = set(Base.metadata.tables)
OBSOLETE_TABLES = {"backtest_equity_point"}


def test_alembic_target_metadata_includes_all_persisted_model_tables() -> None:
    alembic_env = _load_alembic_env()

    assert set(alembic_env.target_metadata.tables) == CURRENT_TABLES


def test_sqlite_upgrade_head_creates_current_schema(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert _database_revision(engine) == _current_head(config)
        assert CURRENT_TABLES <= tables
        assert OBSOLETE_TABLES.isdisjoint(tables)
    finally:
        engine.dispose()


def test_sqlite_migration_head_matches_orm_metadata(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
    finally:
        engine.dispose()


def test_strategy_signal_provenance_migration_backfills_and_round_trips(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260709_0010"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO strategy_signal "
                    "(signal_date, strategy_id, config_version, generated_at, status, result) "
                    "VALUES ('2026-06-22', 'Dual_momentum', 'v1', "
                    "'2026-06-22 09:30:00', 'success', 'hold')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, finished_at, status) "
                    "VALUES ('Dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', '2026-02-01 09:05:00', 'success')"
                )
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        columns = {column["name"]: column for column in inspector.get_columns("strategy_signal")}
        checks = {
            constraint["name"] for constraint in inspector.get_check_constraints("strategy_signal")
        }
        foreign_keys = inspector.get_foreign_keys("strategy_signal")
        indexes = {index["name"] for index in inspector.get_indexes("strategy_signal")}

        assert columns["source"]["nullable"] is False
        assert columns["source"]["type"].length == 16
        assert columns["backtest_run_id"]["nullable"] is True
        assert checks >= {"ck_strategy_signal_source", "ck_strategy_signal_backtest_link"}
        assert any(
            foreign_key["constrained_columns"] == ["backtest_run_id"]
            and foreign_key["referred_table"] == "backtest_run"
            for foreign_key in foreign_keys
        )
        assert "ix_strategy_signal_backtest_run_id" in indexes

        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT source, backtest_run_id FROM strategy_signal")
            ).one() == ("legacy", None)
            assert connection.execute(text("SELECT COUNT(*) FROM backtest_run")).scalar_one() == 1
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        downgraded_columns = {
            column["name"] for column in inspect(engine).get_columns("strategy_signal")
        }
        assert "source" not in downgraded_columns
        assert "backtest_run_id" not in downgraded_columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
            assert connection.execute(
                text("SELECT source, backtest_run_id FROM strategy_signal")
            ).one() == ("legacy", None)
    finally:
        engine.dispose()


def test_data_snapshot_migration_round_trips_and_matches_metadata(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260719_0011"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("backtest_run")}
        assert "data_snapshot_json" not in columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        column = next(
            candidate
            for candidate in inspect(engine).get_columns("backtest_run")
            if candidate["name"] == "data_snapshot_json"
        )
        assert column["nullable"] is True
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, status, data_snapshot_json) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', 'success', :snapshot)"
                ),
                {"snapshot": '{"data_checksum":"abc"}'},
            )
            assert (
                connection.execute(text("SELECT data_snapshot_json FROM backtest_run")).scalar_one()
                == '{"data_checksum":"abc"}'
            )
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("backtest_run")}
        assert "data_snapshot_json" not in columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
    finally:
        engine.dispose()


def test_migration_adds_strategy_id_and_renames_backtest_strategy_column(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "20260618_0006")

    engine = _create_engine(config)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO strategy_signal "
                    "(signal_date, config_version, generated_at, status, result) "
                    "VALUES ('2026-06-22', 'v1', '2026-06-22 09:30:00', 'success', 'hold')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_name, config_version, start_date, end_date, parameters_json, "
                    "started_at, finished_at, status, total_return, annualized_return, "
                    "max_drawdown, sharpe_ratio, volatility) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', '2026-02-01 09:05:00', 'success', "
                    "0.12, 0.18, -0.05, 1.10, 0.20)"
                )
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        signal_columns = {col["name"] for col in inspector.get_columns("strategy_signal")}
        assert "strategy_id" in signal_columns

        backtest_columns = {col["name"] for col in inspector.get_columns("backtest_run")}
        assert "strategy_id" in backtest_columns
        assert "strategy_name" not in backtest_columns

        backtest_indexes = {idx["name"] for idx in inspector.get_indexes("backtest_run")}
        assert "ix_backtest_run_strategy_config" in backtest_indexes

        signal_indexes = {idx["name"] for idx in inspector.get_indexes("strategy_signal")}
        assert "ix_strategy_signal_strategy_config" in signal_indexes

        with engine.connect() as conn:
            signal_strategy_ids = conn.execute(
                text("SELECT strategy_id FROM strategy_signal ORDER BY id")
            ).fetchall()
            assert signal_strategy_ids == [("Dual_momentum",)]

            backtest_strategy_ids = conn.execute(
                text("SELECT strategy_id FROM backtest_run ORDER BY id")
            ).fetchall()
            assert backtest_strategy_ids == [("Dual_momentum",)]
    finally:
        engine.dispose()


def test_migration_adds_quality_warnings_column_to_data_fetch_log(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "20260708_0007")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("data_fetch_log")}
        assert "quality_warnings" not in columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        column = next(
            col
            for col in inspector.get_columns("data_fetch_log")
            if col["name"] == "quality_warnings"
        )
        assert column["nullable"] is True
    finally:
        engine.dispose()


def _load_alembic_env() -> Any:
    env_path = ROOT / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)

    assert spec is not None
    assert spec.loader is not None

    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)
    return alembic_env


def _alembic_config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{database_path}")
    return config


def _create_engine(config: Config) -> Engine:
    database_url = config.get_main_option("sqlalchemy.url")
    assert database_url is not None
    return create_engine(database_url)


def _current_head(config: Config) -> str:
    head = ScriptDirectory.from_config(config).get_current_head()
    assert head is not None
    return head


def _database_revision(engine: Engine) -> str:
    with engine.connect() as connection:
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one()

    return str(revision)
