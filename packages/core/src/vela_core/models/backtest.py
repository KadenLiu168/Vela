from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vela_core.models.base import Base


class BacktestRun(Base):
    __tablename__ = "backtest_run"
    __table_args__ = (
        Index("ix_backtest_run_strategy_config", "strategy_name", "config_version"),
        Index("ix_backtest_run_status_started_at", "status", "started_at"),
        Index("ix_backtest_run_date_range", "start_date", "end_date"),
    )

    STATUSES: ClassVar[tuple[str, ...]] = ("running", "success", "failed", "partial")

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)
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
    equity_points: Mapped[list["BacktestEquityPoint"]] = relationship(
        back_populates="backtest_run",
    )


class BacktestEquityPoint(Base):
    __tablename__ = "backtest_equity_point"
    __table_args__ = (
        UniqueConstraint(
            "backtest_run_id",
            "trade_date",
            name="uq_backtest_equity_point_run_trade_date",
        ),
        Index("ix_backtest_equity_point_run_trade_date", "backtest_run_id", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_run.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    net_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    backtest_run: Mapped[BacktestRun] = relationship(back_populates="equity_points")
