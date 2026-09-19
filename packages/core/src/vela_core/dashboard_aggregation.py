from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, distinct, func, select
from sqlalchemy.orm import Session, selectinload

from vela_core.errors import PersistedDataContractError
from vela_core.models import (
    BacktestBenchmark,
    BacktestRun,
    DataFetchLog,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    WalkForwardRun,
)
from vela_core.walk_forward.evidence import (
    WalkForwardEvidenceV1,
    WalkForwardMetricSummaryModel,
    WalkForwardRateSummaryModel,
    validate_wf_evidence,
)
from vela_core.walk_forward.query import walk_forward_run_ordering

RECENT_FETCH_LOG_LIMIT = 5


@dataclass(frozen=True)
class EtfBrief:
    etf_id: int
    exchange: str
    symbol: str
    name: str
    category: str | None
    earliest_trade_date: date | None = None

    def to_dict(self) -> dict[str, str | None | int]:
        return {
            "etf_id": self.etf_id,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "name": self.name,
            "category": self.category,
            "earliest_trade_date": _format_date(self.earliest_trade_date),
        }


@dataclass(frozen=True)
class DashboardMarketDataStatus:
    price_rows: int
    covered_etfs: int
    earliest_trade_date: date | None
    latest_trade_date: date | None
    etf_list: tuple[EtfBrief, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "price_rows": self.price_rows,
            "covered_etfs": self.covered_etfs,
            "earliest_trade_date": _format_date(self.earliest_trade_date),
            "latest_trade_date": _format_date(self.latest_trade_date),
            "etf_list": [etf.to_dict() for etf in self.etf_list],
        }


@dataclass(frozen=True)
class DashboardSignalPosition:
    exchange: str
    symbol: str
    name: str
    target_weight: Decimal
    rank: int | None
    score: Decimal | None
    is_fallback: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "name": self.name,
            "target_weight": _format_decimal(self.target_weight),
            "rank": self.rank,
            "score": _format_decimal(self.score),
            "is_fallback": self.is_fallback,
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
    source: str = "manual"
    backtest_run_id: int | None = None
    positions: tuple[DashboardSignalPosition, ...] = ()

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
            "source": self.source,
            "backtest_run_id": self.backtest_run_id,
            "positions": [position.to_dict() for position in self.positions],
        }


@dataclass(frozen=True)
class DashboardBenchmark:
    key: str
    name: str
    total_return: Decimal | None
    total_return_difference: Decimal | None
    annualized_return_difference: Decimal | None
    sharpe_ratio: Decimal | None
    max_drawdown: Decimal | None

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "total_return": _format_decimal(self.total_return),
            "total_return_difference": _format_decimal(self.total_return_difference),
            "annualized_return_difference": _format_decimal(self.annualized_return_difference),
            "sharpe_ratio": _format_decimal(self.sharpe_ratio),
            "max_drawdown": _format_decimal(self.max_drawdown),
        }


@dataclass(frozen=True)
class DashboardBacktestSummary:
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    total_return: Decimal | None
    max_drawdown: Decimal | None
    sharpe_ratio: Decimal | None
    started_at: datetime
    annualized_return: Decimal | None = None
    benchmarks: tuple[DashboardBenchmark, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "config_version": self.config_version,
            "start_date": _format_date(self.start_date),
            "end_date": _format_date(self.end_date),
            "status": self.status,
            "total_return": _format_decimal(self.total_return),
            "annualized_return": _format_decimal(self.annualized_return),
            "max_drawdown": _format_decimal(self.max_drawdown),
            "sharpe_ratio": _format_decimal(self.sharpe_ratio),
            "started_at": _format_datetime(self.started_at),
            "benchmarks": [benchmark.to_dict() for benchmark in self.benchmarks],
        }


@dataclass(frozen=True)
class DashboardWalkForwardSummary:
    run_id: int
    strategy_id: str
    status: str
    start_date: date
    end_date: date
    window_count: int
    finished_at: datetime | None
    error_message: str | None
    oos: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "status": self.status,
            "start_date": _format_date(self.start_date),
            "end_date": _format_date(self.end_date),
            "window_count": self.window_count,
            "finished_at": _format_optional_datetime(self.finished_at),
            "error_message": self.error_message,
            "oos": self.oos,
        }


@dataclass(frozen=True)
class DashboardFetchLogSummary:
    fetch_log_id: int
    fetch_time: datetime
    mode: str
    status: str
    rows_fetched: int | None
    rows_inserted: int | None
    rows_updated: int | None
    error_summary: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "fetch_log_id": self.fetch_log_id,
            "fetch_time": _format_datetime(self.fetch_time),
            "mode": self.mode,
            "status": self.status,
            "rows_fetched": self.rows_fetched,
            "rows_inserted": self.rows_inserted,
            "rows_updated": self.rows_updated,
            "error_summary": self.error_summary,
        }


def get_dashboard_summary(
    session: Session,
    *,
    strategy_summary: Mapping[str, Any],
) -> dict[str, object]:
    strategy_id = strategy_summary["strategy_id"]
    config_version = strategy_summary["version"]
    return {
        "strategy": dict(strategy_summary),
        "market_data": _get_market_data_status(session).to_dict(),
        "latest_signal": _get_latest_signal_summary(
            session,
            strategy_id=strategy_id,
            config_version=config_version,
        ),
        "recent_backtest": _get_recent_backtest_summary(session, strategy_id=strategy_id),
        "latest_walk_forward": _get_latest_walk_forward_summary(
            session,
            strategy_id=strategy_id,
        ),
        "recent_fetch_logs": _get_recent_fetch_logs(session),
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
    etf_rows = session.execute(
        select(
            ETFInfo.id.label("etf_id"),
            ETFInfo.exchange,
            ETFInfo.symbol,
            ETFInfo.name,
            ETFInfo.category,
            func.min(MarketPrice.trade_date).label("earliest_trade_date"),
        )
        .join(MarketPrice, MarketPrice.etf_id == ETFInfo.id)
        .group_by(ETFInfo.id, ETFInfo.exchange, ETFInfo.symbol, ETFInfo.name, ETFInfo.category)
        .order_by(ETFInfo.exchange, ETFInfo.symbol)
    ).all()
    return DashboardMarketDataStatus(
        price_rows=price_rows,
        covered_etfs=covered_etfs,
        earliest_trade_date=earliest_trade_date,
        latest_trade_date=latest_trade_date,
        etf_list=tuple(
            EtfBrief(
                etf_id=row.etf_id,
                exchange=row.exchange,
                symbol=row.symbol,
                name=row.name,
                category=row.category,
                earliest_trade_date=row.earliest_trade_date,
            )
            for row in etf_rows
        ),
    )


def _get_latest_signal_summary(
    session: Session,
    *,
    strategy_id: str,
    config_version: str,
) -> dict[str, object] | None:
    signal = session.scalar(
        select(StrategySignal)
        .options(selectinload(StrategySignal.positions))
        .where(StrategySignal.strategy_id == strategy_id)
        .where(StrategySignal.config_version == config_version)
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
        source=signal.source,
        backtest_run_id=signal.backtest_run_id,
        positions=_signal_positions(session, signal),
    ).to_dict()


def _signal_positions(
    session: Session, signal: StrategySignal
) -> tuple[DashboardSignalPosition, ...]:
    if not signal.positions:
        return ()

    etfs_by_id = {
        etf.id: etf
        for etf in session.scalars(
            select(ETFInfo).where(ETFInfo.id.in_(position.etf_id for position in signal.positions))
        )
    }
    return tuple(
        DashboardSignalPosition(
            exchange=etfs_by_id[position.etf_id].exchange,
            symbol=etfs_by_id[position.etf_id].symbol,
            name=etfs_by_id[position.etf_id].name,
            target_weight=position.target_weight,
            rank=position.rank,
            score=position.score,
            is_fallback=position.rank is None and position.score is None,
        )
        for position in sorted(
            signal.positions,
            key=lambda item: (
                item.rank is None,
                item.rank or 0,
                etfs_by_id[item.etf_id].exchange,
                etfs_by_id[item.etf_id].symbol,
            ),
        )
    )


def _get_recent_backtest_summary(session: Session, *, strategy_id: str) -> dict[str, object] | None:
    """Most recent run for the current strategy.

    Scoped by strategy id, unlike the unscoped pre-decision-first behaviour: the
    summary is now paired with the current strategy's signal on a decision
    surface, so returning another strategy's run there would state that run's
    performance as this strategy's. Config versions are deliberately not
    filtered: runs of the same strategy are comparable evidence, and each run's
    version is reported so a stale-version run is visible as one.
    """
    run = session.scalar(
        select(BacktestRun)
        .options(selectinload(BacktestRun.benchmarks))
        .where(BacktestRun.strategy_id == strategy_id)
        .order_by(BacktestRun.started_at.desc(), BacktestRun.id.desc())
        .limit(1)
    )
    if run is None:
        return None

    return DashboardBacktestSummary(
        run_id=run.id,
        strategy_id=run.strategy_id,
        config_version=run.config_version,
        start_date=run.start_date,
        end_date=run.end_date,
        status=run.status,
        total_return=run.total_return,
        max_drawdown=run.max_drawdown,
        sharpe_ratio=run.sharpe_ratio,
        started_at=run.started_at,
        annualized_return=run.annualized_return,
        benchmarks=tuple(_dashboard_benchmark(benchmark, run) for benchmark in run.benchmarks),
    ).to_dict()


def _dashboard_benchmark(benchmark: BacktestBenchmark, run: BacktestRun) -> DashboardBenchmark:
    return DashboardBenchmark(
        key=benchmark.benchmark_key,
        name=benchmark.display_name,
        total_return=benchmark.total_return,
        total_return_difference=_difference(run.total_return, benchmark.total_return),
        annualized_return_difference=_difference(
            run.annualized_return, benchmark.annualized_return
        ),
        sharpe_ratio=benchmark.sharpe_ratio,
        max_drawdown=benchmark.max_drawdown,
    )


def _get_latest_walk_forward_summary(
    session: Session, *, strategy_id: str
) -> dict[str, object] | None:
    run = session.scalar(
        select(WalkForwardRun)
        .where(WalkForwardRun.strategy_id == strategy_id)
        .order_by(*walk_forward_run_ordering())
        .limit(1)
    )
    if run is None:
        return None

    return DashboardWalkForwardSummary(
        run_id=run.id,
        strategy_id=run.strategy_id,
        status=run.status,
        start_date=run.start_date,
        end_date=run.end_date,
        window_count=run.window_count,
        finished_at=run.finished_at,
        error_message=run.error_message,
        oos=_project_oos_evidence(run),
    ).to_dict()


def _project_oos_evidence(run: WalkForwardRun) -> dict[str, object] | None:
    """Narrow cross-window OOS projection for the Dashboard decision layer.

    Only the run row and its persisted evidence document are read; the run's
    window children and their out-of-sample backtests are deliberately not
    loaded, so the cross-child ownership checks performed by the dedicated
    Walk-forward read path do not run here. Every returned number is a
    persisted evidence value.
    """
    if run.status != "success":
        return None

    evidence = validate_wf_evidence(run.evidence_version, run.evidence_json)
    if not isinstance(evidence, WalkForwardEvidenceV1):
        raise PersistedDataContractError(
            "unsupported Walk-forward evidence document for the dashboard projection"
        )

    return {
        "metrics": {
            "total_return": _metric_summary(evidence.metrics.total_return),
            "sharpe_ratio": _metric_summary(evidence.metrics.sharpe_ratio),
            "max_drawdown": _metric_summary(evidence.metrics.max_drawdown),
        },
        "positive_window_rate": _rate_summary(evidence.positive_window_rate),
        "generalization_gap": _metric_summary(evidence.generalization_gap),
        "benchmarks": {
            key: {"outperformance_rate": _rate_summary(item.outperformance_rate)}
            for key, item in evidence.benchmarks.items()
        },
    }


def _metric_summary(summary: WalkForwardMetricSummaryModel) -> dict[str, object]:
    return {
        "median": summary.median,
        "mean": summary.mean,
        "window_count": summary.window_count,
        "valid_count": summary.valid_count,
        "evidence_status": summary.evidence_status,
    }


def _rate_summary(summary: WalkForwardRateSummaryModel) -> dict[str, object]:
    return {
        "value": summary.value,
        "numerator": summary.numerator,
        "denominator": summary.denominator,
        "window_count": summary.window_count,
        "valid_count": summary.valid_count,
        "evidence_status": summary.evidence_status,
    }


def _get_recent_fetch_logs(session: Session) -> list[dict[str, object]]:
    logs = session.scalars(
        select(DataFetchLog)
        .where(DataFetchLog.target_type == "market_price")
        .order_by(
            desc(func.coalesce(DataFetchLog.finished_at, DataFetchLog.started_at)),
            DataFetchLog.id.desc(),
        )
        .limit(RECENT_FETCH_LOG_LIMIT)
    ).all()

    return [
        DashboardFetchLogSummary(
            fetch_log_id=log.id,
            fetch_time=log.finished_at or log.started_at,
            mode=log.fetch_mode,
            status=log.status,
            rows_fetched=log.rows_fetched,
            rows_inserted=log.rows_inserted,
            rows_updated=log.rows_updated,
            error_summary=log.error_message,
        ).to_dict()
        for log in logs
    ]


def _format_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _format_datetime(value: datetime) -> str:
    return value.replace(tzinfo=None).isoformat()


def _format_optional_datetime(value: datetime | None) -> str | None:
    return None if value is None else _format_datetime(value)


def _format_decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _difference(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    return None if left is None or right is None else left - right
