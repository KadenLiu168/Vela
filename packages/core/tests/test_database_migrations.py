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
