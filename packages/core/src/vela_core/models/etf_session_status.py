from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from vela_core.models.base import Base


class ETFSessionStatus(Base):
    __tablename__ = "etf_session_status"
    __table_args__ = (
        UniqueConstraint("etf_id", "trade_date", name="uq_etf_session_status_etf_trade_date"),
        CheckConstraint(
            "status IN ('full_day_suspension', 'corporate_action_halt')",
            name="ck_etf_session_status_status",
        ),
        CheckConstraint(
            "share_ratio IS NULL OR share_ratio > 0",
            name="ck_etf_session_status_share_ratio_positive",
        ),
        CheckConstraint("length(reason) BETWEEN 1 AND 128", name="ck_etf_session_status_reason"),
        CheckConstraint(
            "length(source_uri) BETWEEN 1 AND 2048",
            name="ck_etf_session_status_source_uri",
        ),
        Index("ix_etf_session_status_etf_trade_date", "etf_id", "trade_date"),
        Index("ix_etf_session_status_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    etf_id: Mapped[int] = mapped_column(ForeignKey("etf_info.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(128), nullable=False)
    source_uri: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_published_date: Mapped[date] = mapped_column(Date, nullable=False)
    share_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
