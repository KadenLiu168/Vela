import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.backtest_result_persistence import (
    BacktestEquityCurveInput,
    BacktestResultRunInput,
    persist_backtest_result,
)
from vela_core.data_quality import (
    detect_etf_trading_day_gaps,
    detect_systematic_trading_day_gaps,
)
from vela_core.market_price_query import load_price_panel
from vela_core.models import ETFInfo, MarketPrice, TradingCalendar
from vela_core.portfolio_holdings import PortfolioHoldingSnapshot, calculate_portfolio_holdings
from vela_core.rebalance_dates import generate_rebalance_dates
from vela_core.strategy_config import StrategyConfig
from vela_core.strategy_equity_curve import (
    StrategyAnnualizedReturn,
    StrategyMaximumDrawdown,
    StrategySharpeRatio,
    StrategyVolatility,
    calculate_strategy_annualized_return,
    calculate_strategy_equity_curve,
    calculate_strategy_maximum_drawdown,
    calculate_strategy_sharpe_ratio,
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


@dataclass(frozen=True)
class BacktestGapDetectionConfig:
    """Controls backtest trading-day gap detection strictness.

    When ``strict`` is false (the default when this config is supplied),
    detected gaps are printed as warnings and the backtest proceeds. When
    ``strict`` is true, the backtest raises without persisting when the number
    of systematic gaps exceeds ``max_systematic_gaps``. Per-ETF gaps never
    trigger strict failure (they are usually suspensions, not corruption).
    """

    strict: bool = False
    max_systematic_gaps: int = 5


def run_backtest(
    session: Session,
    *,
    config: StrategyConfig,
    start_date: date,
    end_date: date,
    started_at: datetime | None = None,
    gap_detection: BacktestGapDetectionConfig | None = None,
) -> BacktestRunResult:
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    trading_dates = _load_trading_dates(session, start_date=start_date, end_date=end_date)
    if not trading_dates:
        raise ValueError("No local market prices found in requested backtest date range")

    active_etfs = _list_active_etfs(session)
    _check_trading_day_gaps(
        session,
        trading_dates=trading_dates,
        active_etfs=active_etfs,
        start_date=start_date,
        end_date=end_date,
        gap_detection=gap_detection,
    )

    started_at = started_at or datetime.now(UTC)
    rebalance_dates = generate_rebalance_dates(
        trading_dates,
        frequency=config.rebalance.frequency,
    )
    defense_lookup = {(etf.exchange, etf.symbol): etf for etf in active_etfs}

    # Convert the longest trading-day window to a safe calendar-day buffer:
    # ~252 trading days per ~365 calendar days gives a ratio of ~0.69, so
    # ``max_window / 0.69`` calendar days is the minimum; ``* 2 + 10`` adds a
    # comfortable margin for weekends, holidays, and suspended-trading gaps so
    # the first rebalance date always sees enough history for trend + momentum.
    max_window = max(
        config.momentum.long_window_days,
        config.trend_filter.moving_average_days,
    )
    panel_window_start = rebalance_dates[0] - timedelta(days=max_window * 2 + 10)
    price_panel = load_price_panel(
        session,
        etf_ids=[etf.id for etf in active_etfs],
        start_date=panel_window_start,
        end_date=rebalance_dates[-1] if rebalance_dates else end_date,
    )

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
        defense_lookup=defense_lookup,
        generated_at=started_at,
        persist=_persist_signal,
    )

    points = calculate_strategy_equity_curve(
        session,
        trading_dates=trading_dates,
        strategy_config=config,
    )
    holdings = calculate_portfolio_holdings(
        session,
        trading_dates=trading_dates,
        config_version=config.version,
    )
    annualized_return = calculate_strategy_annualized_return(points)
    maximum_drawdown = calculate_strategy_maximum_drawdown(points)
    volatility = calculate_strategy_volatility(points)
    sharpe_ratio = calculate_strategy_sharpe_ratio(
        annualized_return,
        volatility,
        risk_free_rate=Decimal(str(config.performance.risk_free_rate)),
    )
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
            parameters_json=_parameters_json(config, start_date=start_date, end_date=end_date),
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=status,
            total_return=annualized_return.total_return,
            annualized_return=annualized_return.annualized_return,
            max_drawdown=maximum_drawdown.max_drawdown,
            sharpe_ratio=sharpe_ratio.sharpe_ratio,
            volatility=volatility.volatility,
        ),
        equity_curve=_to_curve_inputs(points, holdings),
    )
    signal_ids: list[int] = []
    for result in signal_results:
        if result.strategy_signal_id is None:
            raise ValueError("Backtest signal generation did not persist every signal")
        signal_ids.append(result.strategy_signal_id)
    link_signals_to_backtest_run(
        session,
        run_id=persistence_result.backtest_run.id,
        signal_ids=signal_ids,
    )

    return _to_result(
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
    )


def _load_trading_dates(session: Session, *, start_date: date, end_date: date) -> list[date]:
    return list(
        session.scalars(
            select(MarketPrice.trade_date)
            .where(MarketPrice.trade_date >= start_date)
            .where(MarketPrice.trade_date <= end_date)
            .distinct()
            .order_by(MarketPrice.trade_date)
        )
    )


def _list_active_etfs(session: Session) -> list[ETFInfo]:
    return list(
        session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.id))
    )


def _check_trading_day_gaps(
    session: Session,
    *,
    trading_dates: list[date],
    active_etfs: list[ETFInfo],
    start_date: date,
    end_date: date,
    gap_detection: BacktestGapDetectionConfig | None,
) -> None:
    """Warn about (and optionally block on) trading-day gaps before a backtest.

    Default mode (``gap_detection is None`` or ``strict=False``) prints detected
    gaps and returns. Strict mode raises without persisting when systematic gaps
    exceed the configured threshold, or when the trading calendar is empty (a
    strict check has no reference to check against). Per-ETF gaps never trigger
    strict failure.
    """
    expected_dates = list(
        session.scalars(
            select(TradingCalendar.trade_date)
            .where(TradingCalendar.trade_date >= start_date)
            .where(TradingCalendar.trade_date <= end_date)
            .order_by(TradingCalendar.trade_date)
        )
    )
    if not expected_dates:
        message = (
            "Trading calendar has no rows covering the requested backtest range; "
            "run `vela sync-trading-calendar` to enable gap detection"
        )
        if gap_detection is not None and gap_detection.strict:
            raise ValueError(
                f"Strict data-quality mode requires a synced trading calendar: {message}"
            )
        print(f"Warning: {message}; skipping gap detection")
        return

    etf_rows = session.execute(
        select(MarketPrice.etf_id, MarketPrice.trade_date)
        .where(MarketPrice.trade_date >= start_date)
        .where(MarketPrice.trade_date <= end_date)
    ).all()
    per_etf: dict[int, list[date]] = defaultdict(list)
    for etf_id, trade_date in etf_rows:
        per_etf[etf_id].append(trade_date)

    inception_boundaries: dict[int, date] = {}
    for etf in active_etfs:
        stored = per_etf.get(etf.id)
        if not stored:
            continue
        first_stored = min(stored)
        boundary = first_stored
        if etf.inception_date is not None and etf.inception_date > boundary:
            boundary = etf.inception_date
        inception_boundaries[etf.id] = boundary

    systematic_gaps = detect_systematic_trading_day_gaps(trading_dates, expected_dates)
    etf_gaps = detect_etf_trading_day_gaps(per_etf, expected_dates, inception_boundaries)

    if systematic_gaps:
        missing = ", ".join(gap.trade_date.isoformat() for gap in systematic_gaps)
        print(
            f"Warning: {len(systematic_gaps)} systematic trading-day gap(s) detected "
            f"(missing from all ETFs): {missing}"
        )
    if etf_gaps:
        print(
            f"Warning: {len(etf_gaps)} per-ETF trading-day gap(s) detected "
            "(may be suspensions, not corruption)"
        )

    if gap_detection is not None and gap_detection.strict and systematic_gaps:
        threshold = gap_detection.max_systematic_gaps
        if len(systematic_gaps) > threshold:
            missing = ", ".join(gap.trade_date.isoformat() for gap in systematic_gaps)
            raise ValueError(
                f"Strict data-quality check failed: {len(systematic_gaps)} systematic "
                f"trading-day gap(s) exceed threshold {threshold}: {missing}"
            )


def _to_curve_inputs(
    points: list,
    holdings: list[PortfolioHoldingSnapshot],
) -> list[BacktestEquityCurveInput]:
    holdings_by_date = {snapshot.trade_date: snapshot for snapshot in holdings}
    curve_inputs: list[BacktestEquityCurveInput] = []

    for point in points:
        snapshot = holdings_by_date.get(point.trade_date)
        positions = [] if snapshot is None else snapshot.holdings
        has_holdings = bool(positions)
        curve_inputs.append(
            BacktestEquityCurveInput(
                trade_date=point.trade_date,
                net_value=point.net_value,
                cash=Decimal("0.000000") if has_holdings else point.net_value,
                market_value=point.net_value if has_holdings else Decimal("0.000000"),
                total_assets=point.net_value,
                positions_json=json.dumps(
                    [
                        {
                            "etf_id": holding.etf_id,
                            "target_weight": str(holding.target_weight.quantize(_SIX_PLACES)),
                        }
                        for holding in positions
                    ],
                    sort_keys=True,
                ),
            )
        )

    return curve_inputs


def _parameters_json(config: StrategyConfig, *, start_date: date, end_date: date) -> str:
    return json.dumps(
        {
            "strategy_id": config.strategy_id,
            "config_version": config.version,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "risk_free_rate": config.performance.risk_free_rate,
        },
        sort_keys=True,
    )


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
    )
