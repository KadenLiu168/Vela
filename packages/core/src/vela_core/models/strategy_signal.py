from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar

from sqlalchemy import (
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
from sqlalchemy.orm import Mapped, mapped_column

from vela_core.models.base import Base


class StrategySignal(Base):
    __tablename__ = "strategy_signal"
    __table_args__ = (
        Index("ix_strategy_signal_date_config", "signal_date", "config_version"),
        Index("ix_strategy_signal_status_generated_at", "status", "generated_at"),
    )

    STATUSES: ClassVar[tuple[str, ...]] = ("running", "success", "failed", "partial")
    RESULTS: ClassVar[tuple[str, ...]] = ("buy", "hold", "rebalance", "empty")

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
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
