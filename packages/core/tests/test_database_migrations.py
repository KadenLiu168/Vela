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
