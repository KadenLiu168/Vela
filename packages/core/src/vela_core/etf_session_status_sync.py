from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.config import load_yaml_config
from vela_core.models import ETFInfo, ETFSessionStatus, MarketPrice

ETF_SESSION_STATUS_VERSION = "etf_session_status_v1"
ETFSessionStatusName = Literal["full_day_suspension", "corporate_action_halt"]


class ETFSessionStatusEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exchange: str = Field(min_length=1, max_length=32)
    symbol: str = Field(min_length=1, max_length=32)
    trade_date: date
    status: ETFSessionStatusName
    reason: str = Field(min_length=1, max_length=128)
    source_uri: str = Field(min_length=1, max_length=2048)
    source_published_date: date
    share_ratio: Decimal | None = Field(default=None, gt=0)


class ETFSessionStatusDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["etf_session_status_v1"]
    entries: list[ETFSessionStatusEntry]

    @model_validator(mode="after")
    def validate_unique_identities(self) -> ETFSessionStatusDocument:
        seen: set[tuple[str, str, date]] = set()
        for entry in self.entries:
            identity = (entry.exchange, entry.symbol, entry.trade_date)
            if identity in seen:
                raise ValueError(
                    "duplicate ETF session status identity: "
                    f"{entry.exchange}:{entry.symbol} on {entry.trade_date.isoformat()}"
                )
            seen.add(identity)
        return self


@dataclass(frozen=True)
class ETFSessionStatusSyncResult:
    total_entries: int
    inserted_count: int
    updated_count: int
    unchanged_count: int


def load_etf_session_status_document(
    path: str | Path,
) -> ETFSessionStatusDocument:
    return load_yaml_config(path, ETFSessionStatusDocument)


def validate_etf_session_status_document(document: object) -> ETFSessionStatusDocument:
    return ETFSessionStatusDocument.model_validate(document)


def sync_etf_session_status_to_db(
    session: Session, document: ETFSessionStatusDocument | object
) -> ETFSessionStatusSyncResult:
    validated = validate_etf_session_status_document(document)
    resolved: list[tuple[ETFSessionStatusEntry, ETFInfo, ETFSessionStatus | None]] = []

    for entry in validated.entries:
        etf = session.scalar(
            select(ETFInfo).where(
                ETFInfo.exchange == entry.exchange,
                ETFInfo.symbol == entry.symbol,
            )
        )
        if etf is None:
            raise ValueError(
                f"session status references missing ETF {entry.exchange}:{entry.symbol}"
            )
        if etf.listing_date is None:
            raise ValueError(
                "session status references ETF without listing_date "
                f"{entry.exchange}:{entry.symbol}"
            )
        if entry.trade_date < etf.listing_date:
            raise ValueError(
                "session status precedes ETF listing_date "
                f"for {entry.exchange}:{entry.symbol} on {entry.trade_date.isoformat()}"
            )
        if (
            session.scalar(
                select(MarketPrice.id).where(
                    MarketPrice.etf_id == etf.id,
                    MarketPrice.trade_date == entry.trade_date,
                )
            )
            is not None
        ):
            raise ValueError(
                "raw market price conflicts with session status for "
                f"{entry.exchange}:{entry.symbol} on {entry.trade_date.isoformat()}"
            )
        existing = session.scalar(
            select(ETFSessionStatus).where(
                ETFSessionStatus.etf_id == etf.id,
                ETFSessionStatus.trade_date == entry.trade_date,
            )
        )
        resolved.append((entry, etf, existing))

    inserted_count = 0
    updated_count = 0
    unchanged_count = 0
    for entry, etf, existing in resolved:
        if existing is None:
            session.add(
                ETFSessionStatus(
                    etf_id=etf.id,
                    trade_date=entry.trade_date,
                    status=entry.status,
                    reason=entry.reason,
                    source_uri=entry.source_uri,
                    source_published_date=entry.source_published_date,
                    share_ratio=entry.share_ratio,
                )
            )
            inserted_count += 1
            continue

        values = {
            "status": entry.status,
            "reason": entry.reason,
            "source_uri": entry.source_uri,
            "source_published_date": entry.source_published_date,
            "share_ratio": entry.share_ratio,
        }
        changed = any(getattr(existing, field) != value for field, value in values.items())
        if changed:
            for field, value in values.items():
                setattr(existing, field, value)
            updated_count += 1
        else:
            unchanged_count += 1

    session.flush()
    return ETFSessionStatusSyncResult(
        total_entries=len(validated.entries),
        inserted_count=inserted_count,
        updated_count=updated_count,
        unchanged_count=unchanged_count,
    )
