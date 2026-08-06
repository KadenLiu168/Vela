from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    case,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vela_core.models.base import Base

if TYPE_CHECKING:
    from vela_core.models.strategy_signal import StrategySignal


class BacktestRun(Base):
    __tablename__ = "backtest_run"
    __table_args__ = (
        Index("ix_backtest_run_strategy_config", "strategy_id", "config_version"),
        Index("ix_backtest_run_status_started_at", "status", "started_at"),
        Index("ix_backtest_run_date_range", "start_date", "end_date"),
    )

    STATUSES: ClassVar[tuple[str, ...]] = ("running", "success", "failed", "partial")

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)
    data_snapshot_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    total_return: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    annualized_return: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volatility: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    sortino_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    calmar_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    longest_drawdown_duration_sessions: Mapped[int | None] = mapped_column()
    longest_drawdown_peak_date: Mapped[date | None] = mapped_column(Date)
    longest_drawdown_trough_date: Mapped[date | None] = mapped_column(Date)
    longest_drawdown_recovery_date: Mapped[date | None] = mapped_column(Date)
    historical_var_95: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    historical_cvar_95: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    return_skewness: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    return_excess_kurtosis: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    distribution_observation_count: Mapped[int | None] = mapped_column()
    tail_observation_count: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    equity_curve: Mapped[list["BacktestEquityCurve"]] = relationship(
        back_populates="backtest_run",
        order_by=lambda: (BacktestEquityCurve.trade_date, BacktestEquityCurve.id),
    )
    signals: Mapped[list["StrategySignal"]] = relationship(
        back_populates="backtest_run",
        order_by="(StrategySignal.signal_date, StrategySignal.id)",
    )
    benchmarks: Mapped[list["BacktestBenchmark"]] = relationship(
        back_populates="backtest_run",
        order_by=lambda: (
            case(
                {"equal_weight_monthly": 0, "csi_300_buy_hold": 1},
                value=BacktestBenchmark.benchmark_key,
                else_=2,
            ),
            BacktestBenchmark.id,
        ),
    )


class BacktestEquityCurve(Base):
    __tablename__ = "backtest_equity_curve"
    __table_args__ = (
        UniqueConstraint(
            "backtest_run_id",
            "trade_date",
            name="uq_backtest_equity_curve_run_trade_date",
        ),
        Index("ix_backtest_equity_curve_run_trade_date", "backtest_run_id", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_run.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    net_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    positions_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    backtest_run: Mapped[BacktestRun] = relationship(back_populates="equity_curve")


class BacktestBenchmark(Base):
    __tablename__ = "backtest_benchmark"
    __table_args__ = (
        UniqueConstraint("backtest_run_id", "benchmark_key", name="uq_backtest_benchmark_run_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_run.id"), nullable=False)
    benchmark_key: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    total_return: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    annualized_return: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volatility: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    sortino_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    calmar_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    longest_drawdown_duration_sessions: Mapped[int | None] = mapped_column()
    longest_drawdown_peak_date: Mapped[date | None] = mapped_column(Date)
    longest_drawdown_trough_date: Mapped[date | None] = mapped_column(Date)
    longest_drawdown_recovery_date: Mapped[date | None] = mapped_column(Date)
    tracking_error: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    information_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    capm_alpha: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    capm_beta: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    capm_r_squared: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    capm_observation_count: Mapped[int | None] = mapped_column()
    up_capture_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    up_capture_observation_count: Mapped[int | None] = mapped_column()
    down_capture_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    down_capture_observation_count: Mapped[int | None] = mapped_column()
    historical_var_95: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    historical_cvar_95: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    return_skewness: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    return_excess_kurtosis: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    distribution_observation_count: Mapped[int | None] = mapped_column()
    tail_observation_count: Mapped[int | None] = mapped_column()
    backtest_run: Mapped[BacktestRun] = relationship(back_populates="benchmarks")
    equity_curve: Mapped[list["BacktestBenchmarkEquityCurve"]] = relationship(
        back_populates="benchmark",
        order_by=lambda: (BacktestBenchmarkEquityCurve.trade_date, BacktestBenchmarkEquityCurve.id),
    )


class BacktestBenchmarkEquityCurve(Base):
    __tablename__ = "backtest_benchmark_equity_curve"
    __table_args__ = (
        UniqueConstraint("benchmark_id", "trade_date", name="uq_backtest_benchmark_curve_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    benchmark_id: Mapped[int] = mapped_column(ForeignKey("backtest_benchmark.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    net_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    benchmark: Mapped[BacktestBenchmark] = relationship(back_populates="equity_curve")
