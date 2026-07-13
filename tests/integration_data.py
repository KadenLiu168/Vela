from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from vela_core import DailyPrice
from vela_core.database import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory
from vela_core.models import (
    BacktestEquityCurve,
    BacktestRun,
    Base,
    DataFetchLog,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    StrategySignalPosition,
)


@dataclass(frozen=True)
class WorkflowDataset:
    first_etf_id: int
    second_etf_id: int
    defensive_etf_id: int
    latest_trade_date: date
    signal_id: int
    backtest_run_id: int


class ControlledMarketDataProvider:
    name = "controlled"

    def __init__(self, prices_by_symbol: dict[str, Sequence[DailyPrice]]) -> None:
        self._prices_by_symbol = prices_by_symbol
        self.requests: list[tuple[str, date | None]] = []

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        self.requests.append((symbol, start_date))
        return self._prices_by_symbol.get(symbol, ())


def prepare_sqlite_database(database_url: str, *, reset: bool = True) -> sessionmaker[Session]:
    _ensure_sqlite(database_url)
    engine = create_engine_from_url(database_url)
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return create_session_factory(engine, expire_on_commit=False)


def prepare_workflow_database(database_url: str, *, reset: bool = True) -> WorkflowDataset:
    session_factory = prepare_sqlite_database(database_url, reset=reset)
    with session_factory() as session:
        dataset = seed_minimal_workflow_data(session)
        session.commit()
        return dataset


def seed_minimal_workflow_data(session: Session) -> WorkflowDataset:
    latest_trade_date = date(2026, 6, 23)
    first = add_etf(session, exchange="SSE", symbol="510300", currency="CNY")
    second = add_etf(session, exchange="SZSE", symbol="159915", currency="CNY")
    defensive = add_etf(session, exchange="SSE", symbol="511010", currency="CNY")
    add_price_history(session, etf_id=first.id, end_date=latest_trade_date)
    add_price_history(
        session,
        etf_id=second.id,
        end_date=latest_trade_date,
        current_price=Decimal("170.000000"),
    )
    add_price_history(
        session,
        etf_id=defensive.id,
        end_date=latest_trade_date,
        current_price=Decimal("101.000000"),
    )

    signal = StrategySignal(
        signal_date=latest_trade_date,
        strategy_id="Dual_momentum",
        config_version="v1",
        generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        status="success",
        result="rebalance",
        error_message=None,
        positions=[
            StrategySignalPosition(
                etf_id=first.id,
                rank=1,
                score=Decimal("1.200000"),
                target_weight=Decimal("0.500000"),
            ),
            StrategySignalPosition(
                etf_id=second.id,
                rank=2,
                score=Decimal("1.100000"),
                target_weight=Decimal("0.500000"),
            ),
        ],
    )
    run = backtest_run(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
        started_at=datetime(2026, 1, 11, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 1, 11, 9, 5, tzinfo=UTC),
    )
    fetch_log = data_fetch_log(
        fetch_mode="incremental",
        status="success",
        started_at=datetime(2026, 6, 23, 7, 0, tzinfo=UTC),
        finished_at=datetime(2026, 6, 23, 7, 1, tzinfo=UTC),
        rows_fetched=3,
        rows_inserted=3,
        rows_updated=0,
        error_message=None,
    )
    session.add_all([signal, run, fetch_log])
    session.flush()
    session.add_all(
        [
            equity_curve_row(
                run_id=run.id,
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.010000"),
            ),
            equity_curve_row(
                run_id=run.id,
                trade_date=date(2026, 1, 3),
                net_value=Decimal("1.030000"),
            ),
        ]
    )
    session.flush()
    return WorkflowDataset(
        first_etf_id=first.id,
        second_etf_id=second.id,
        defensive_etf_id=defensive.id,
        latest_trade_date=latest_trade_date,
        signal_id=signal.id,
        backtest_run_id=run.id,
    )


def add_etf(
    session: Session,
    *,
    symbol: str,
    exchange: str = "NYSEARCA",
    currency: str = "USD",
    category: str | None = None,
) -> ETFInfo:
    etf = ETFInfo(
        exchange=exchange,
        symbol=symbol,
        name=f"{symbol} ETF",
        currency=currency,
        category=category,
    )
    session.add(etf)
    session.flush()
    return etf


def add_market_price(
    session: Session,
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal = Decimal("100.000000"),
) -> None:
    session.add(market_price(etf_id=etf_id, trade_date=trade_date, close_price=close_price))


def add_price_history(
    session: Session,
    *,
    etf_id: int,
    end_date: date,
    current_price: Decimal = Decimal("180.000000"),
    days: int = 131,
) -> None:
    start_date = end_date - timedelta(days=days - 1)
    session.add_all(
        market_price(
            etf_id=etf_id,
            trade_date=start_date + timedelta(days=offset),
            close_price=current_price if offset in {days - 2, days - 1} else Decimal("100.000000"),
        )
        for offset in range(days)
    )


def market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal = Decimal("100.000000"),
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        factor_hfq=Decimal("1"),
        volume=1000,
    )


def backtest_run(
    *,
    start_date: date,
    end_date: date,
    started_at: datetime,
    finished_at: datetime | None = None,
    status: str = "success",
    total_return: Decimal | None = Decimal("0.120000"),
) -> BacktestRun:
    return BacktestRun(
        strategy_id="Dual_momentum",
        config_version="v1",
        start_date=start_date,
        end_date=end_date,
        parameters_json='{"top_n": 2}',
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        error_message=None,
        total_return=total_return,
        annualized_return=Decimal("0.180000"),
        max_drawdown=Decimal("-0.050000"),
        volatility=Decimal("0.200000"),
        sharpe_ratio=Decimal("1.100000"),
    )


def equity_curve_row(
    *,
    run_id: int,
    trade_date: date,
    net_value: Decimal,
) -> BacktestEquityCurve:
    return BacktestEquityCurve(
        backtest_run_id=run_id,
        trade_date=trade_date,
        net_value=net_value,
        cash=Decimal("100.000000"),
        market_value=Decimal("9900.000000"),
        total_assets=Decimal("10000.000000"),
        positions_json='[{"symbol": "510300", "weight": 1.0}]',
    )


def data_fetch_log(
    *,
    fetch_mode: str,
    status: str,
    started_at: datetime,
    finished_at: datetime | None,
    rows_fetched: int | None,
    rows_inserted: int | None,
    rows_updated: int | None,
    error_message: str | None,
) -> DataFetchLog:
    return DataFetchLog(
        source="tencent",
        target_type="market_price",
        fetch_mode=fetch_mode,
        range_start=None,
        range_end=None,
        requested_symbols=None,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        error_message=error_message,
    )


def daily_price(symbol: str, *, trade_date: date) -> DailyPrice:
    return DailyPrice(
        symbol=symbol,
        trade_date=trade_date,
        open_price=Decimal("101.000000"),
        high_price=Decimal("102.000000"),
        low_price=Decimal("100.000000"),
        close_price=Decimal("101.500000"),
        factor=Decimal("1"),
        volume=2000,
    )


def _ensure_sqlite(database_url: str) -> None:
    if make_url(database_url).get_backend_name() != "sqlite":
        raise ValueError("Integration data preparation only supports SQLite database URLs")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Vela integration test SQLite data.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--empty", action="store_true", help="Create schema without workflow data.")
    parser.add_argument(
        "--no-reset", action="store_true", help="Keep existing tables before creating schema."
    )
    args = parser.parse_args()

    if args.empty:
        prepare_sqlite_database(args.database_url, reset=not args.no_reset)
    else:
        prepare_workflow_database(args.database_url, reset=not args.no_reset)
    print(f"Prepared SQLite integration data at {args.database_url}")


if __name__ == "__main__":
    main()
