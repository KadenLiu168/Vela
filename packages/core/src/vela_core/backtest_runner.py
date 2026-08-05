import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.backtest_benchmarks import (
    BacktestBenchmarkResult,
    calculate_backtest_benchmark_active_risk_metrics,
    calculate_backtest_benchmark_regime_metrics,
    calculate_backtest_benchmarks,
)
from vela_core.backtest_result_persistence import (
    BacktestBenchmarkInput,
    BacktestEquityCurveInput,
    BacktestResultRunInput,
    persist_backtest_result,
)
from vela_core.errors import BacktestDataError, InvalidDateRangeError
from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, MarketPrice, TradingCalendar
from vela_core.rebalance_dates import generate_rebalance_dates
from vela_core.strategies.registry import resolve_strategy
from vela_core.strategy_config import StrategyConfig
from vela_core.strategy_equity_curve import (
    StrategyAnnualizedReturn,
    StrategyCalmarRatio,
    StrategyEquityCurvePoint,
    StrategyLongestDrawdownDuration,
    StrategyMaximumDrawdown,
    StrategySharpeRatio,
    StrategySortinoRatio,
    StrategyVolatility,
    calculate_strategy_annualized_return,
    calculate_strategy_calmar_ratio,
    calculate_strategy_equity_curve,
    calculate_strategy_longest_drawdown_duration,
    calculate_strategy_maximum_drawdown,
    calculate_strategy_sharpe_ratio,
    calculate_strategy_sortino_ratio,
    calculate_strategy_volatility,
)
from vela_core.strategy_signal_generation import (
    PersistStrategySignalPosition,
    generate_historical_strategy_signals,
)
from vela_core.strategy_signal_persistence import (
    StrategySignalPositionInput,
    link_signals_to_backtest_run,
    persist_strategy_signal,
)

_SIX_PLACES = Decimal("0.000001")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BacktestRunResult:
    backtest_run_id: int
    status: str
    start_date: date
    end_date: date
    trading_day_count: int
    signal_count: int
    total_return: Decimal | None
    annualized_return: Decimal | None
    max_drawdown: Decimal
    sharpe_ratio: Decimal | None
    volatility: Decimal | None
    benchmarks: tuple[BacktestBenchmarkResult, ...] = ()
    sortino_ratio: Decimal | None = None
    calmar_ratio: Decimal | None = None
    longest_drawdown_duration_sessions: int | None = None
    longest_drawdown_peak_date: date | None = None
    longest_drawdown_trough_date: date | None = None
    longest_drawdown_recovery_date: date | None = None


def run_backtest(
    session: Session,
    *,
    config: StrategyConfig,
    start_date: date,
    end_date: date,
    started_at: datetime | None = None,
    calculate_benchmarks: bool = True,
) -> BacktestRunResult:
    started = time.perf_counter()
    logger.info(
        "backtest.started strategy_id=%s start_date=%s end_date=%s",
        config.strategy_id,
        start_date.isoformat(),
        end_date.isoformat(),
    )
    if start_date > end_date:
        raise InvalidDateRangeError("start_date must be on or before end_date")

    trading_dates = _load_trading_dates(session, start_date=start_date, end_date=end_date)
    if not trading_dates:
        raise BacktestDataError(
            "Trading calendar has no official sessions in requested backtest range"
        )

    active_etfs = _list_active_etfs(session)
    strategy = resolve_strategy(config)
    lookback_days = strategy.lookback_days()
    if lookback_days < 0:
        raise ValueError("Strategy lookback_days must be non-negative")
    required_dates = _load_required_trading_dates(
        session,
        trading_dates=trading_dates,
        first_rebalance_date=generate_rebalance_dates(
            trading_dates,
            frequency=config.rebalance.frequency,
        )[0],
        lookback_days=lookback_days,
    )

    started_at = started_at or datetime.now(UTC)
    price_panel = load_price_panel(
        session,
        etf_ids=[etf.id for etf in active_etfs],
        start_date=required_dates[0],
        end_date=end_date,
    )
    benchmarks = (
        calculate_backtest_benchmarks(
            trading_dates=trading_dates,
            active_etfs=active_etfs,
            price_panel=price_panel,
            transaction_cost_bps=config.costs.transaction_cost_bps,
            risk_free_rate=Decimal(str(config.performance.risk_free_rate)),
            following_trading_date=_load_following_trading_date(session, end_date=end_date),
        )
        if calculate_benchmarks
        else []
    )
    _validate_required_prices(
        active_etfs=active_etfs,
        required_dates=required_dates,
        price_panel=price_panel,
    )
    data_snapshot_json = build_data_snapshot(price_panel)

    def _persist_signal(
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
            source="backtest",
            backtest_run_id=None,
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
        return persistence_result.strategy_signal.id

    signal_results = generate_historical_strategy_signals(
        historical_trading_dates=trading_dates,
        config=config,
        price_panel=price_panel,
        active_etfs=active_etfs,
        generated_at=started_at,
        persist=_persist_signal,
    )
    signal_ids: list[int] = []
    for result in signal_results:
        if result.strategy_signal_id is None:
            raise ValueError("Backtest signal generation did not persist every signal")
        signal_ids.append(result.strategy_signal_id)

    points = calculate_strategy_equity_curve(
        session,
        trading_dates=trading_dates,
        strategy_config=config,
        signal_ids=signal_ids,
        price_panel=price_panel,
    )
    risk_free_rate = Decimal(str(config.performance.risk_free_rate))
    annualized_return = calculate_strategy_annualized_return(points)
    maximum_drawdown = calculate_strategy_maximum_drawdown(points)
    volatility = calculate_strategy_volatility(points)
    sharpe_ratio = calculate_strategy_sharpe_ratio(
        points,
        risk_free_rate=risk_free_rate,
    )
    sortino_ratio = calculate_strategy_sortino_ratio(points, risk_free_rate=risk_free_rate)
    calmar_ratio = calculate_strategy_calmar_ratio(
        annualized_return.annualized_return,
        maximum_drawdown.max_drawdown,
    )
    longest_drawdown_duration = calculate_strategy_longest_drawdown_duration(points)
    benchmarks = [
        calculate_backtest_benchmark_active_risk_metrics(points, benchmark)
        for benchmark in benchmarks
    ]
    if calculate_benchmarks:
        benchmarks = [
            calculate_backtest_benchmark_regime_metrics(
                points,
                benchmark,
                risk_free_rate=risk_free_rate,
            )
            for benchmark in benchmarks
        ]
    status = (
        "success" if all(result.status == "success" for result in signal_results) else "partial"
    )

    persistence_result = persist_backtest_result(
        session,
        run=BacktestResultRunInput(
            strategy_id=config.strategy_id,
            config_version=config.version,
            start_date=start_date,
            end_date=end_date,
            parameters_json=_parameters_json(
                config,
                start_date=start_date,
                end_date=end_date,
                calculate_benchmarks=calculate_benchmarks,
            ),
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=status,
            total_return=annualized_return.total_return,
            annualized_return=annualized_return.annualized_return,
            max_drawdown=maximum_drawdown.max_drawdown,
            sharpe_ratio=sharpe_ratio.sharpe_ratio,
            volatility=volatility.volatility,
            sortino_ratio=sortino_ratio.sortino_ratio,
            calmar_ratio=calmar_ratio.calmar_ratio,
            longest_drawdown_duration_sessions=(
                longest_drawdown_duration.longest_drawdown_duration_sessions
            ),
            longest_drawdown_peak_date=longest_drawdown_duration.peak_date,
            longest_drawdown_trough_date=longest_drawdown_duration.trough_date,
            longest_drawdown_recovery_date=longest_drawdown_duration.recovery_date,
            data_snapshot_json=data_snapshot_json,
        ),
        equity_curve=_to_curve_inputs(points),
        benchmarks=_to_benchmark_inputs(benchmarks),
    )
    link_signals_to_backtest_run(
        session,
        run_id=persistence_result.backtest_run.id,
        signal_ids=signal_ids,
    )

    backtest_result = _to_result(
        backtest_run_id=persistence_result.backtest_run.id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        trading_day_count=len(trading_dates),
        signal_count=len(signal_results),
        annualized_return=annualized_return,
        maximum_drawdown=maximum_drawdown,
        volatility=volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        longest_drawdown_duration=longest_drawdown_duration,
        benchmarks=benchmarks,
    )
    logger.info(
        "backtest.completed strategy_id=%s run_id=%s trading_day_count=%s signal_count=%s "
        "duration_ms=%.3f",
        config.strategy_id,
        backtest_result.backtest_run_id,
        backtest_result.trading_day_count,
        backtest_result.signal_count,
        (time.perf_counter() - started) * 1000,
    )
    return backtest_result


def build_data_snapshot(price_panel: dict[int, list[MarketPrice]]) -> dict[str, object]:
    rows = sorted(
        (price for prices in price_panel.values() for price in prices),
        key=lambda price: (price.etf_id, price.trade_date),
    )
    checksum = hashlib.sha256()
    per_etf_row_counts: dict[str, int] = {}

    for price in rows:
        etf_id = str(price.etf_id)
        per_etf_row_counts[etf_id] = per_etf_row_counts.get(etf_id, 0) + 1
        checksum.update(
            json.dumps(
                [
                    price.etf_id,
                    price.trade_date.isoformat(),
                    str(price.close_price),
                    str(price.factor_hfq),
                ],
                separators=(",", ":"),
            ).encode("utf-8")
        )
        checksum.update(b"\n")

    return {
        "min_trade_date": min(price.trade_date for price in rows).isoformat() if rows else None,
        "max_trade_date": max(price.trade_date for price in rows).isoformat() if rows else None,
        "trading_day_count": len({price.trade_date for price in rows}),
        "active_etf_count": len(per_etf_row_counts),
        "per_etf_row_counts": per_etf_row_counts,
        "data_checksum": checksum.hexdigest(),
    }


def _load_trading_dates(session: Session, *, start_date: date, end_date: date) -> list[date]:
    return list(
        session.scalars(
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date >= start_date)
            .where(TradingCalendar.trade_date <= end_date)
            .order_by(TradingCalendar.trade_date)
        )
    )


def _load_following_trading_date(session: Session, *, end_date: date) -> date | None:
    return session.scalar(
        select(TradingCalendar.trade_date)
        .where(TradingCalendar.trade_date > end_date)
        .order_by(TradingCalendar.trade_date)
        .limit(1)
    )


def _list_active_etfs(session: Session) -> list[ETFInfo]:
    return list(
        session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.id))
    )


def _load_required_trading_dates(
    session: Session,
    *,
    trading_dates: list[date],
    first_rebalance_date: date,
    lookback_days: int,
) -> list[date]:
    if lookback_days == 0:
        return trading_dates

    preceding_dates = list(
        session.scalars(
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date < first_rebalance_date)
            .order_by(TradingCalendar.trade_date.desc())
            .limit(lookback_days)
        )
    )
    if len(preceding_dates) != lookback_days:
        raise BacktestDataError(
            f"Strategy requires {lookback_days} preceding official session(s), "
            f"but trading calendar has {len(preceding_dates)} before "
            f"{first_rebalance_date.isoformat()}"
        )
    return sorted(set(preceding_dates) | set(trading_dates))


def _validate_required_prices(
    *,
    active_etfs: list[ETFInfo],
    required_dates: list[date],
    price_panel: dict[int, list[MarketPrice]],
) -> None:
    available_keys = {
        (price.etf_id, price.trade_date) for prices in price_panel.values() for price in prices
    }
    gaps = [
        (etf.id, trade_date)
        for etf in active_etfs
        for trade_date in required_dates
        if (etf.inception_date is None or trade_date >= etf.inception_date)
        and (etf.id, trade_date) not in available_keys
    ]
    if not gaps:
        return

    sample = ", ".join(
        f"ETF {etf_id} on {trade_date.isoformat()}" for etf_id, trade_date in gaps[:10]
    )
    suffix = "" if len(gaps) <= 10 else ", ..."
    raise BacktestDataError(
        f"Backtest input has {len(gaps)} missing active-universe price row(s): {sample}{suffix}"
    )


def _to_curve_inputs(points: list[StrategyEquityCurvePoint]) -> list[BacktestEquityCurveInput]:
    curve_inputs: list[BacktestEquityCurveInput] = []

    for point in points:
        state = point.portfolio_state
        if state is None:
            raise ValueError("Equity curve point is missing calculated portfolio state")
        curve_inputs.append(
            BacktestEquityCurveInput(
                trade_date=point.trade_date,
                net_value=point.net_value,
                cash=state.cash,
                market_value=state.market_value,
                total_assets=state.total_assets,
                positions_json=json.dumps(
                    [
                        {
                            "etf_id": position.etf_id,
                            "target_weight": str(position.target_weight),
                            "actual_weight": str(position.actual_weight),
                        }
                        for position in state.positions
                    ],
                    sort_keys=True,
                ),
            )
        )

    return curve_inputs


def _to_benchmark_inputs(
    benchmarks: list[BacktestBenchmarkResult],
) -> list[BacktestBenchmarkInput]:
    return [
        BacktestBenchmarkInput(
            key=benchmark.key,
            name=benchmark.name,
            total_return=benchmark.annualized_return.total_return,
            annualized_return=benchmark.annualized_return.annualized_return,
            max_drawdown=benchmark.maximum_drawdown.max_drawdown,
            sharpe_ratio=benchmark.sharpe_ratio.sharpe_ratio,
            volatility=benchmark.volatility.volatility,
            sortino_ratio=benchmark.sortino_ratio.sortino_ratio,
            calmar_ratio=benchmark.calmar_ratio.calmar_ratio,
            longest_drawdown_duration_sessions=(
                benchmark.longest_drawdown_duration.longest_drawdown_duration_sessions
            ),
            longest_drawdown_peak_date=benchmark.longest_drawdown_duration.peak_date,
            longest_drawdown_trough_date=benchmark.longest_drawdown_duration.trough_date,
            longest_drawdown_recovery_date=benchmark.longest_drawdown_duration.recovery_date,
            tracking_error=benchmark.tracking_error,
            information_ratio=benchmark.information_ratio,
            capm_alpha=benchmark.capm_alpha,
            capm_beta=benchmark.capm_beta,
            capm_r_squared=benchmark.capm_r_squared,
            capm_observation_count=benchmark.capm_observation_count,
            up_capture_ratio=benchmark.up_capture_ratio,
            up_capture_observation_count=benchmark.up_capture_observation_count,
            down_capture_ratio=benchmark.down_capture_ratio,
            down_capture_observation_count=benchmark.down_capture_observation_count,
            equity_curve=[(point.trade_date, point.net_value) for point in benchmark.points],
        )
        for benchmark in benchmarks
    ]


def _parameters_json(
    config: StrategyConfig,
    *,
    start_date: date,
    end_date: date,
    calculate_benchmarks: bool = False,
) -> str:
    parameters = {
        "strategy_id": config.strategy_id,
        "config_version": config.version,
        "type": config.type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "risk_free_rate": config.performance.risk_free_rate,
        "performance_metric_version": "performance_metrics_v1",
        "equity_model_version": "drift_v1",
    }
    if calculate_benchmarks:
        parameters["benchmark_regime_metric_version"] = "benchmark_regime_metrics_v1"
    return json.dumps(parameters, sort_keys=True)


def _to_result(
    *,
    backtest_run_id: int,
    status: str,
    start_date: date,
    end_date: date,
    trading_day_count: int,
    signal_count: int,
    annualized_return: StrategyAnnualizedReturn,
    maximum_drawdown: StrategyMaximumDrawdown,
    volatility: StrategyVolatility,
    sharpe_ratio: StrategySharpeRatio,
    sortino_ratio: StrategySortinoRatio,
    calmar_ratio: StrategyCalmarRatio,
    longest_drawdown_duration: StrategyLongestDrawdownDuration,
    benchmarks: list[BacktestBenchmarkResult],
) -> BacktestRunResult:
    return BacktestRunResult(
        backtest_run_id=backtest_run_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        trading_day_count=trading_day_count,
        signal_count=signal_count,
        total_return=annualized_return.total_return,
        annualized_return=annualized_return.annualized_return,
        max_drawdown=maximum_drawdown.max_drawdown,
        sharpe_ratio=sharpe_ratio.sharpe_ratio,
        volatility=volatility.volatility,
        sortino_ratio=sortino_ratio.sortino_ratio,
        calmar_ratio=calmar_ratio.calmar_ratio,
        longest_drawdown_duration_sessions=(
            longest_drawdown_duration.longest_drawdown_duration_sessions
        ),
        longest_drawdown_peak_date=longest_drawdown_duration.peak_date,
        longest_drawdown_trough_date=longest_drawdown_duration.trough_date,
        longest_drawdown_recovery_date=longest_drawdown_duration.recovery_date,
        benchmarks=tuple(benchmarks),
    )
