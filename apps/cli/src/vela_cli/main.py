from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from alembic.config import Config
from vela_core import (
    AkShareMarketDataProvider,
    MarketDataFetchResult,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
)
from vela_core.database import create_engine_from_url, create_session_factory, managed_session

from alembic import command

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"
DEFAULT_DATABASE_URL = "sqlite+pysqlite:///vela.db"


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
        default=DEFAULT_DATABASE_URL,
        help="Database URL to initialize",
    )

    fetch_market_data_parser = subparsers.add_parser(
        "fetch-market-data",
        help="Fetch full daily market data for active ETFs",
    )
    fetch_market_data_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to write market data into",
    )
    fetch_market_data_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Fetch only market data newer than the latest local market price date",
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

    if args.command == "fetch-market-data":
        try:
            result = (
                fetch_incremental_market_data(args.database_url)
                if args.incremental
                else fetch_full_market_data(args.database_url)
            )
        except Exception as exc:
            print(f"Failed to fetch market data into {args.database_url}: {exc}", file=sys.stderr)
            return 1

        _print_fetch_summary(result)
        return 1 if result.status == "failed" else 0

    parser.error(f"unknown command: {args.command}")
    return 2


def fetch_full_market_data(database_url: str) -> MarketDataFetchResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    with managed_session(session_factory) as session:
        return fetch_full_market_prices(session, provider=AkShareMarketDataProvider())


def fetch_incremental_market_data(database_url: str) -> MarketDataFetchResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    with managed_session(session_factory) as session:
        return fetch_incremental_market_prices(session, provider=AkShareMarketDataProvider())


def _print_fetch_summary(result: MarketDataFetchResult) -> None:
    print(f"Market data fetch status: {result.status}")
    print(f"Requested symbols: {result.requested_symbol_count}")
    print(f"Rows fetched: {result.rows_fetched}")
    print(f"Rows inserted: {result.rows_inserted}")
    print(f"Rows updated: {result.rows_updated}")
    if result.failed_symbols:
        print(f"Failed symbols: {', '.join(result.failed_symbols)}")
    if result.error_message:
        print(f"Error: {result.error_message}")


if __name__ == "__main__":
    raise SystemExit(main())
