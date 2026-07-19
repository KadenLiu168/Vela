from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vela_core.models.base import Base

if TYPE_CHECKING:
    from vela_core.models.backtest import BacktestRun


class StrategySignal(Base):
    __tablename__ = "strategy_signal"
    __table_args__ = (
        CheckConstraint(
            "source IN ('manual', 'scheduled', 'backtest', 'legacy')",
            name="ck_strategy_signal_source",
        ),
        CheckConstraint(
            "source = 'backtest' OR backtest_run_id IS NULL",
            name="ck_strategy_signal_backtest_link",
        ),
        Index("ix_strategy_signal_backtest_run_id", "backtest_run_id"),
        Index("ix_strategy_signal_date_config", "signal_date", "config_version"),
        Index("ix_strategy_signal_status_generated_at", "status", "generated_at"),
        Index("ix_strategy_signal_strategy_config", "strategy_id", "config_version"),
    )

    STATUSES: ClassVar[tuple[str, ...]] = ("running", "success", "failed", "partial")
    RESULTS: ClassVar[tuple[str, ...]] = ("buy", "hold", "rebalance", "empty")
    SOURCES: ClassVar[tuple[str, ...]] = ("manual", "scheduled", "backtest", "legacy")
    RUNTIME_SOURCES: ClassVar[tuple[str, ...]] = ("manual", "scheduled", "backtest")
    LIVE_SOURCES: ClassVar[tuple[str, ...]] = ("manual", "scheduled")

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    backtest_run_id: Mapped[int | None] = mapped_column(ForeignKey("backtest_run.id"))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(Text)
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
    positions: Mapped[list["StrategySignalPosition"]] = relationship(
        back_populates="strategy_signal",
    )
    backtest_run: Mapped["BacktestRun | None"] = relationship(back_populates="signals")


class StrategySignalPosition(Base):
    __tablename__ = "strategy_signal_position"
    __table_args__ = (
        UniqueConstraint(
            "strategy_signal_id",
            "etf_id",
            name="uq_strategy_signal_position_signal_etf",
        ),
        Index("ix_strategy_signal_position_signal", "strategy_signal_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_signal_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_signal.id"),
        nullable=False,
    )
    etf_id: Mapped[int] = mapped_column(ForeignKey("etf_info.id"), nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    target_weight: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    strategy_signal: Mapped[StrategySignal] = relationship(back_populates="positions")
