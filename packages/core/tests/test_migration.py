from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text
from vela_core.migration import build_alembic_config, run_alembic_upgrade

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_SCRIPT_LOCATION = REPO_ROOT / "alembic"


# 1.1 build_alembic_config sets script_location and sqlalchemy.url
def test_build_alembic_config_sets_script_location_and_database_url(tmp_path) -> None:
    script_location = tmp_path / "alembic"
    config = build_alembic_config(
        database_url="sqlite:///test.db",
        script_location=script_location,
    )
    assert isinstance(config, Config)
    assert config.get_main_option("script_location") == str(script_location)
    assert config.get_main_option("sqlalchemy.url") == "sqlite:///test.db"


# 1.2 run_alembic_upgrade upgrades an empty database to head
def test_run_alembic_upgrade_empty_database_to_head(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'migration.db'}"
    run_alembic_upgrade(database_url, ALEMBIC_SCRIPT_LOCATION)

    engine = create_engine(database_url)
    with engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert revision is not None
    assert revision != ""


# 1.3 run_alembic_upgrade is a no-op on an already-current database
def test_run_alembic_upgrade_already_current_is_noop(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'migration_noop.db'}"

    # First upgrade creates the schema
    run_alembic_upgrade(database_url, ALEMBIC_SCRIPT_LOCATION)

    engine = create_engine(database_url)
    with engine.connect() as connection:
        first_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    # Second upgrade should be a no-op (same revision, no error)
    run_alembic_upgrade(database_url, ALEMBIC_SCRIPT_LOCATION)

    with engine.connect() as connection:
        second_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    assert first_revision == second_revision
