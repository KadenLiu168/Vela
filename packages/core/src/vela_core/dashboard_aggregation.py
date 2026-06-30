from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import BacktestRun, MarketPrice, StrategySignal


@dataclass(frozen=True)
class DashboardMarketDataStatus:
    price_rows: int
    covered_etfs: int
    earliest_trade_date: date | None
    latest_trade_date: date | None

    def to_dict(self) -> dict[str, object]:
        return {
            "price_rows": self.price_rows,
            "covered_etfs": self.covered_etfs,
            "earliest_trade_date": _format_date(self.earliest_trade_date),
            "latest_trade_date": _format_date(self.latest_trade_date),
        }


@dataclass(frozen=True)
class DashboardSignalSummary:
    signal_id: int
    signal_date: date
    config_version: str
    status: str
    result: str | None
    generated_at: datetime
    is_fallback: bool
    position_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "signal_date": _format_date(self.signal_date),
            "config_version": self.config_version,
            "status": self.status,
            "result": self.result,
            "generated_at": _format_datetime(self.generated_at),
            "is_fallback": self.is_fallback,
            "position_count": self.position_count,
        }


@dataclass(frozen=True)
class DashboardBacktestSummary:
    run_id: int
    strategy_name: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    total_return: Decimal | None
    max_drawdown: Decimal | None
    sharpe_ratio: Decimal | None
    started_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "strategy_name": self.strategy_name,
            "config_version": self.config_version,
            "start_date": _format_date(self.start_date),
            "end_date": _format_date(self.end_date),
            "status": self.status,
            "total_return": _format_decimal(self.total_return),
            "max_drawdown": _format_decimal(self.max_drawdown),
            "sharpe_ratio": _format_decimal(self.sharpe_ratio),
            "started_at": _format_datetime(self.started_at),
        }


def get_dashboard_summary(
    session: Session,
    *,
    strategy_summary: Mapping[str, Any],
) -> dict[str, object]:
    return {
        "strategy": dict(strategy_summary),
        "market_data": _get_market_data_status(session).to_dict(),
        "latest_signal": _get_latest_signal_summary(session),
        "recent_backtest": _get_recent_backtest_summary(session),
    }


def _get_market_data_status(session: Session) -> DashboardMarketDataStatus:
    price_rows, covered_etfs, earliest_trade_date, latest_trade_date = session.execute(
        select(
            func.count(MarketPrice.id),
            func.count(distinct(MarketPrice.etf_id)),
            func.min(MarketPrice.trade_date),
            func.max(MarketPrice.trade_date),
        )
    ).one()
    return DashboardMarketDataStatus(
        price_rows=price_rows,
        covered_etfs=covered_etfs,
        earliest_trade_date=earliest_trade_date,
        latest_trade_date=latest_trade_date,
    )


def _get_latest_signal_summary(session: Session) -> dict[str, object] | None:
    signal = session.scalar(
        select(StrategySignal)
        .options(selectinload(StrategySignal.positions))
        .where(StrategySignal.status == "success")
        .order_by(StrategySignal.generated_at.desc(), StrategySignal.id.desc())
        .limit(1)
    )
    if signal is None:
        return None

    return DashboardSignalSummary(
        signal_id=signal.id,
        signal_date=signal.signal_date,
        config_version=signal.config_version,
        status=signal.status,
        result=signal.result,
        generated_at=signal.generated_at,
        is_fallback=any(
            position.rank is None and position.score is None for position in signal.positions
        ),
        position_count=len(signal.positions),
    ).to_dict()


def _get_recent_backtest_summary(session: Session) -> dict[str, object] | None:
    run = session.scalar(
        select(BacktestRun).order_by(BacktestRun.started_at.desc(), BacktestRun.id.desc()).limit(1)
    )
    if run is None:
        return None

    return DashboardBacktestSummary(
        run_id=run.id,
        strategy_name=run.strategy_name,
        config_version=run.config_version,
        start_date=run.start_date,
        end_date=run.end_date,
        status=run.status,
        total_return=run.total_return,
        max_drawdown=run.max_drawdown,
        sharpe_ratio=run.sharpe_ratio,
        started_at=run.started_at,
    ).to_dict()


def _format_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _format_datetime(value: datetime) -> str:
    return value.replace(tzinfo=None).isoformat()


def _format_decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)
