from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import BacktestEquityCurve, BacktestRun


@dataclass(frozen=True)
class BacktestResultRunInput:
    strategy_name: str
    config_version: str
    start_date: date
    end_date: date
    parameters_json: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    error_message: str | None = None
    total_return: Decimal | None = None
    annualized_return: Decimal | None = None
    max_drawdown: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    volatility: Decimal | None = None


@dataclass(frozen=True)
class BacktestEquityCurveInput:
    trade_date: date
    net_value: Decimal
    cash: Decimal
    market_value: Decimal
    total_assets: Decimal
    positions_json: str


@dataclass(frozen=True)
class BacktestResultPersistenceResult:
    backtest_run: BacktestRun
    equity_curve: list[BacktestEquityCurve]


def persist_backtest_result(
    session: Session,
    *,
    run: BacktestResultRunInput,
    equity_curve: Sequence[BacktestEquityCurveInput],
) -> BacktestResultPersistenceResult:
    backtest_run = BacktestRun(
        strategy_name=run.strategy_name,
        config_version=run.config_version,
        start_date=run.start_date,
        end_date=run.end_date,
        parameters_json=run.parameters_json,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        error_message=run.error_message,
        total_return=run.total_return,
        annualized_return=run.annualized_return,
        max_drawdown=run.max_drawdown,
        sharpe_ratio=run.sharpe_ratio,
        volatility=run.volatility,
    )
    session.add(backtest_run)
    session.flush()

    curve_rows = [
        BacktestEquityCurve(
            backtest_run_id=backtest_run.id,
            trade_date=row.trade_date,
            net_value=row.net_value,
            cash=row.cash,
            market_value=row.market_value,
            total_assets=row.total_assets,
            positions_json=row.positions_json,
        )
        for row in equity_curve
    ]
    session.add_all(curve_rows)
    session.flush()

    return BacktestResultPersistenceResult(
        backtest_run=backtest_run,
        equity_curve=curve_rows,
    )


def get_backtest_result(session: Session, *, run_id: int) -> BacktestRun | None:
    return session.scalar(
        select(BacktestRun)
        .options(selectinload(BacktestRun.equity_curve))
        .where(BacktestRun.id == run_id)
    )
