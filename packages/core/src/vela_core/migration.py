from pathlib import Path

from alembic.config import Config

from alembic import command


def build_alembic_config(database_url: str, script_location: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def run_alembic_upgrade(database_url: str, script_location: Path) -> None:
    command.upgrade(build_alembic_config(database_url, script_location), "head")
