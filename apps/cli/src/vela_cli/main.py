from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from alembic.config import Config

from alembic import command

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"


def _build_alembic_config(
    database_url: str,
    script_location: Path = DEFAULT_ALEMBIC_SCRIPT_LOCATION,
) -> Config:
    config = Config()
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def init_db(
    database_url: str,
    script_location: Path = DEFAULT_ALEMBIC_SCRIPT_LOCATION,
) -> None:
    command.upgrade(_build_alembic_config(database_url, script_location), "head")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vela")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db_parser = subparsers.add_parser("init-db", help="Initialize the local database")
    init_db_parser.add_argument(
        "--database-url",
        default="sqlite+pysqlite:///vela.db",
        help="Database URL to initialize",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        try:
            init_db(args.database_url)
        except Exception as exc:
            print(f"Failed to initialize database at {args.database_url}: {exc}", file=sys.stderr)
            return 1

        print(f"Initialized database at {args.database_url}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
