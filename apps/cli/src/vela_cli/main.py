from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import func, select
from vela_core import (
    BacktestGapDetectionConfig,
    BacktestReportNotFoundError,
    BacktestRunResult,
    ETFPoolSyncResult,
    GenerateStrategySignalResult,
    LatestStrategySignalReportNotFoundError,
    MarketDataFetchResult,
    TencentMarketDataProvider,
    TradingCalendarSyncResult,
    export_latest_strategy_signal_report,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
    generate_strategy_signal,
    load_app_config,
    load_price_panel,
    run_alembic_upgrade,
    sync_etf_pool_to_db,
    sync_trading_calendar_to_db,
)
from vela_core import (
    export_backtest_report as export_core_backtest_report,
)
from vela_core import (
    run_backtest as run_core_backtest,
)
from vela_core.database import (
    DEFAULT_DATABASE_URL,
    create_engine_from_url,
    create_session_factory,
    managed_session,
)
from vela_core.models import ETFInfo, MarketPrice
from vela_core.strategy_config import load_strategy_config
from vela_core.strategy_signal_generation import PersistStrategySignalPosition
from vela_core.strategy_signal_persistence import (
    StrategySignalPositionInput,
    persist_strategy_signal,
)

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"
DEFAULT_STRATEGY_CONFIG_PATH = ROOT / "config" / "strategy_v1.yaml"


def init_db(
    database_url: str,
    script_location: Path = DEFAULT_ALEMBIC_SCRIPT_LOCATION,
) -> None:
    run_alembic_upgrade(database_url, script_location)


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

    sync_etf_pool_parser = subparsers.add_parser(
        "sync-etf-pool",
        help="Sync the configured ETF pool into the local database",
    )
    sync_etf_pool_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to write ETF metadata into",
    )
    sync_etf_pool_parser.add_argument(
        "--strategy-config",
        default=str(DEFAULT_STRATEGY_CONFIG_PATH),
        help="Strategy configuration YAML path",
    )

    sync_trading_calendar_parser = subparsers.add_parser(
        "sync-trading-calendar",
        help="Sync the A-share trading-day calendar from akshare into the local database",
    )
    sync_trading_calendar_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to write the trading calendar into",
    )

    generate_signal_parser = subparsers.add_parser(
        "generate-signal",
        help="Generate and persist the latest strategy signal",
    )
    generate_signal_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to read market data from and write the signal into",
    )
    generate_signal_parser.add_argument(
        "--strategy-config",
        default=str(DEFAULT_STRATEGY_CONFIG_PATH),
        help="Strategy configuration YAML path",
    )
    generate_signal_parser.add_argument(
        "--signal-date",
        type=_parse_signal_date,
        default=None,
        help="Signal date in YYYY-MM-DD format; defaults to latest local market price date",
    )

    export_signal_report_parser = subparsers.add_parser(
        "export-signal-report",
        help="Export the latest persisted strategy signal report",
    )
    export_signal_report_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to read the persisted signal from",
    )
    export_signal_report_parser.add_argument(
        "--strategy-config",
        default=str(DEFAULT_STRATEGY_CONFIG_PATH),
        help="Strategy configuration YAML path",
    )
    export_signal_report_parser.add_argument(
        "--signal-date",
        type=_parse_signal_date,
        default=None,
        help="Signal date in YYYY-MM-DD format; defaults to the latest successful signal date",
    )
    export_signal_report_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the report",
    )

    run_backtest_parser = subparsers.add_parser(
        "run-backtest",
        help="Run and persist a historical backtest",
    )
    run_backtest_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to read market data from and write the backtest into",
    )
    run_backtest_parser.add_argument(
        "--strategy-config",
        default=str(DEFAULT_STRATEGY_CONFIG_PATH),
        help="Strategy configuration YAML path",
    )
    run_backtest_parser.add_argument(
        "--start-date",
        type=_parse_iso_date,
        required=True,
        help="Backtest start date in YYYY-MM-DD format",
    )
    run_backtest_parser.add_argument(
        "--end-date",
        type=_parse_iso_date,
        required=True,
        help="Backtest end date in YYYY-MM-DD format",
    )
    run_backtest_parser.add_argument(
        "--strict-data-quality",
        action="store_true",
        help="Fail the backtest when systematic trading-day gaps exceed --max-gap-days",
    )
    run_backtest_parser.add_argument(
        "--max-gap-days",
        type=int,
        default=5,
        help="Maximum tolerated systematic trading-day gaps in strict mode (default: 5)",
    )

    export_backtest_report_parser = subparsers.add_parser(
        "export-backtest-report",
        help="Export a persisted backtest report",
    )
    export_backtest_report_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Database URL to read the persisted backtest from",
    )
    export_backtest_report_parser.add_argument(
        "--run-id",
        type=int,
        required=True,
        help="Persisted backtest run id",
    )
    export_backtest_report_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the report",
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
            fetch_result = (
                fetch_incremental_market_data(args.database_url)
                if args.incremental
                else fetch_full_market_data(args.database_url)
            )
        except Exception as exc:
            print(f"Failed to fetch market data into {args.database_url}: {exc}", file=sys.stderr)
            return 1

        _print_fetch_summary(fetch_result)
        return 1 if fetch_result.status == "failed" else 0

    if args.command == "sync-etf-pool":
        try:
            sync_result = sync_etf_pool(
                args.database_url,
                strategy_config_path=Path(args.strategy_config),
            )
        except Exception as exc:
            print(f"Failed to sync ETF pool into {args.database_url}: {exc}", file=sys.stderr)
            return 1

        _print_etf_pool_sync_summary(sync_result)
        return 0

    if args.command == "sync-trading-calendar":
        try:
            calendar_result = sync_trading_calendar(args.database_url)
        except Exception as exc:
            print(
                f"Failed to sync trading calendar into {args.database_url}: {exc}",
                file=sys.stderr,
            )
            return 1

        _print_trading_calendar_sync_summary(calendar_result)
        return 1 if calendar_result.status == "failed" else 0

    if args.command == "generate-signal":
        try:
            signal_result = generate_signal(
                args.database_url,
                strategy_config_path=Path(args.strategy_config),
                signal_date=args.signal_date,
            )
        except Exception as exc:
            print(f"Failed to generate signal in {args.database_url}: {exc}", file=sys.stderr)
            return 1

        _print_signal_summary(signal_result)
        return 1 if signal_result.status == "failed" else 0

    if args.command == "export-signal-report":
        try:
            report = export_signal_report(
                args.database_url,
                strategy_config_path=Path(args.strategy_config),
                signal_date=args.signal_date,
            )
        except LatestStrategySignalReportNotFoundError as exc:
            print(f"Failed to export signal report: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(
                f"Failed to export signal report from {args.database_url}: {exc}",
                file=sys.stderr,
            )
            return 1

        if args.output is None:
            print(report, end="")
        else:
            args.output.write_text(report)
            print(f"Exported signal report to {args.output}")
        return 0

    if args.command == "run-backtest":
        gap_detection = BacktestGapDetectionConfig(
            strict=args.strict_data_quality,
            max_systematic_gaps=args.max_gap_days,
        )
        try:
            result = run_backtest(
                args.database_url,
                strategy_config_path=Path(args.strategy_config),
                start_date=args.start_date,
                end_date=args.end_date,
                gap_detection=gap_detection,
            )
        except Exception as exc:
            print(f"Failed to run backtest in {args.database_url}: {exc}", file=sys.stderr)
            return 1

        _print_backtest_summary(result)
        return 0

    if args.command == "export-backtest-report":
        try:
            report = export_backtest_report(args.database_url, run_id=args.run_id)
        except BacktestReportNotFoundError as exc:
            print(f"Failed to export backtest report: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(
                f"Failed to export backtest report from {args.database_url}: {exc}",
                file=sys.stderr,
            )
            return 1

        if args.output is None:
            print(report, end="")
        else:
            args.output.write_text(report)
            print(f"Exported backtest report to {args.output}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def fetch_full_market_data(database_url: str) -> MarketDataFetchResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    with managed_session(session_factory) as session:
        return fetch_full_market_prices(session, provider=TencentMarketDataProvider())


def fetch_incremental_market_data(database_url: str) -> MarketDataFetchResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    with managed_session(session_factory) as session:
        return fetch_incremental_market_prices(session, provider=TencentMarketDataProvider())


def sync_etf_pool(
    database_url: str,
    *,
    strategy_config_path: Path,
) -> ETFPoolSyncResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    config = load_app_config(strategy_config_path)
    with managed_session(session_factory) as session:
        return sync_etf_pool_to_db(session, config.etf_pool)


def sync_trading_calendar(database_url: str) -> TradingCalendarSyncResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    with managed_session(session_factory) as session:
        return sync_trading_calendar_to_db(session)


def generate_signal(
    database_url: str,
    *,
    strategy_config_path: Path,
    signal_date: date | None,
) -> GenerateStrategySignalResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    config = load_strategy_config(strategy_config_path)
    with managed_session(session_factory) as session:
        resolved_signal_date = signal_date or session.scalar(
            select(func.max(MarketPrice.trade_date))
        )
        if resolved_signal_date is None:
            raise ValueError("No local market prices found")

        active_etfs = list(
            session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.id))
        )
        price_panel = load_price_panel(
            session,
            etf_ids=[etf.id for etf in active_etfs],
            start_date=None,
            end_date=resolved_signal_date,
        )
        defense_lookup = {(etf.exchange, etf.symbol): etf for etf in active_etfs}

        def _persist(
            *,
            signal_date: date,
            generated_at: datetime,
            status: str,
            result: str | None,
            positions: list[PersistStrategySignalPosition],
            error_message: str | None,
        ) -> int:
            persistence_result = persist_strategy_signal(
                session,
                strategy_id=config.strategy_id,
                signal_date=signal_date,
                config_version=config.version,
                generated_at=generated_at,
                status=status,
                result=result,
                positions=[
                    StrategySignalPositionInput(
                        etf_id=position["etf_id"],
                        rank=position["rank"],
                        score=position["score"],
                        target_weight=position["target_weight"],
                    )
                    for position in positions
                ],
                error_message=error_message,
            )
            session.commit()
            return persistence_result.strategy_signal.id

        return generate_strategy_signal(
            signal_date=resolved_signal_date,
            config=config,
            price_panel=price_panel,
            active_etfs=active_etfs,
            defense_lookup=defense_lookup,
            persist=_persist,
        )


def export_signal_report(
    database_url: str,
    *,
    strategy_config_path: Path,
    signal_date: date | None,
) -> str:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    config = load_strategy_config(strategy_config_path)
    with managed_session(session_factory) as session:
        return export_latest_strategy_signal_report(
            session,
            config_version=config.version,
            signal_date=signal_date,
        )


def run_backtest(
    database_url: str,
    *,
    strategy_config_path: Path,
    start_date: date,
    end_date: date,
    gap_detection: BacktestGapDetectionConfig | None = None,
) -> BacktestRunResult:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    config = load_strategy_config(strategy_config_path)
    with managed_session(session_factory) as session:
        return run_core_backtest(
            session,
            config=config,
            start_date=start_date,
            end_date=end_date,
            gap_detection=gap_detection,
        )


def export_backtest_report(database_url: str, *, run_id: int) -> str:
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    with managed_session(session_factory) as session:
        return export_core_backtest_report(session, run_id=run_id)


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


def _print_etf_pool_sync_summary(result: ETFPoolSyncResult) -> None:
    print("ETF pool sync status: success")
    print(f"Pool: {result.pool_id}")
    print(f"Total ETFs: {result.total_etfs}")
    print(f"Inserted: {result.inserted_count}")
    print(f"Updated: {result.updated_count}")
    print(f"Unchanged: {result.unchanged_count}")


def _print_trading_calendar_sync_summary(result: TradingCalendarSyncResult) -> None:
    print(f"Trading calendar sync status: {result.status}")
    print(f"Total synced: {result.synced_count}")
    print(f"Inserted: {result.inserted_count}")
    print(f"Updated: {result.updated_count}")
    if result.error_message:
        print(f"Error: {result.error_message}")


def _print_signal_summary(result: GenerateStrategySignalResult) -> None:
    print(f"Strategy signal status: {result.status}")
    print(f"Result: {result.result}")
    print(f"Signal date: {result.signal_date.isoformat()}")
    print(f"Config version: {result.config_version}")
    print(f"Signal id: {result.strategy_signal_id}")
    if result.positions:
        print("Positions:")
        for position in result.positions:
            rank = "" if position.rank is None else f" rank={position.rank}"
            score = "" if position.score is None else f" score={position.score}"
            print(
                f"- {position.exchange} {position.symbol} weight={position.target_weight}"
                f"{rank}{score}"
            )
    if result.error_message:
        print(f"Error: {result.error_message}")


def _print_backtest_summary(result: BacktestRunResult) -> None:
    print(f"Backtest status: {result.status}")
    print(f"Backtest run id: {result.backtest_run_id}")
    print(f"Date range: {result.start_date.isoformat()} to {result.end_date.isoformat()}")
    print(f"Trading days: {result.trading_day_count}")
    print(f"Signals generated: {result.signal_count}")
    print(f"Total return: {_format_optional_decimal(result.total_return)}")
    print(f"Annualized return: {_format_optional_decimal(result.annualized_return)}")
    print(f"Max drawdown: {result.max_drawdown}")
    print(f"Volatility: {_format_optional_decimal(result.volatility)}")
    print(f"Sharpe ratio: {_format_optional_decimal(result.sharpe_ratio)}")


def _format_optional_decimal(value: object | None) -> str:
    return "n/a" if value is None else str(value)


def _parse_signal_date(value: str) -> date:
    return _parse_iso_date(value, "signal date")


def _parse_iso_date(value: str, label: str = "date") -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must use YYYY-MM-DD format") from exc


if __name__ == "__main__":
    raise SystemExit(main())
