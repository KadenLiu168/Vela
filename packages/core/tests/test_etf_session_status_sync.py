from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core.etf_session_status_sync import (
    ETFSessionStatusDocument,
    sync_etf_session_status_to_db,
    validate_etf_session_status_document,
)
from vela_core.models import Base, ETFInfo, ETFSessionStatus, MarketPrice


def _entry(
    *,
    symbol: str = "510300",
    trade_date: str = "2024-01-03",
    status: str = "full_day_suspension",
    reason: str = "holder_meeting",
    source_uri: str = "https://example.test/announcement",
    source_published_date: str = "2024-01-02",
    share_ratio: str | None = None,
) -> dict[str, object]:
    return {
        "exchange": "SSE",
        "symbol": symbol,
        "trade_date": trade_date,
        "status": status,
        "reason": reason,
        "source_uri": source_uri,
        "source_published_date": source_published_date,
        "share_ratio": share_ratio,
    }


def _document(*entries: dict[str, object]) -> ETFSessionStatusDocument:
    return ETFSessionStatusDocument(version="etf_session_status_v1", entries=list(entries))


def test_status_document_rejects_unsupported_status() -> None:
    with pytest.raises(ValidationError, match="status"):
        validate_etf_session_status_document(_document(_entry(status="partial_halt")))


def test_status_document_requires_source_evidence() -> None:
    with pytest.raises(ValidationError):
        validate_etf_session_status_document(_document(_entry(reason="", source_uri="")))


def test_status_document_rejects_non_positive_optional_share_ratio() -> None:
    with pytest.raises(ValidationError, match="share_ratio"):
        validate_etf_session_status_document(_document(_entry(share_ratio="0")))


def test_status_document_rejects_duplicate_identity() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        validate_etf_session_status_document(_document(_entry(), _entry()))


def test_sync_rejects_missing_listed_etf_before_writing() -> None:
    factory = _create_session_factory()
    with factory() as session:
        session.add(
            ETFInfo(
                exchange="SSE",
                symbol="510300",
                name="CSI 300 ETF",
                currency="CNY",
                listing_date=None,
                is_active=True,
            )
        )
        session.commit()

        with pytest.raises(ValueError, match="listing_date"):
            sync_etf_session_status_to_db(session, _document(_entry()))
        assert session.query(ETFSessionStatus).count() == 0


def test_sync_rejects_raw_status_conflict_before_writing() -> None:
    factory = _create_session_factory()
    with factory() as session:
        etf = ETFInfo(
            exchange="SSE",
            symbol="510300",
            name="CSI 300 ETF",
            currency="CNY",
            listing_date=date(2012, 5, 28),
            is_active=True,
        )
        session.add(etf)
        session.flush()
        session.add(
            MarketPrice(
                etf_id=etf.id,
                trade_date=date(2024, 1, 3),
                open_price=Decimal("1"),
                high_price=Decimal("1"),
                low_price=Decimal("1"),
                close_price=Decimal("1"),
                factor_hfq=Decimal("1"),
            )
        )
        session.commit()

        with pytest.raises(ValueError, match="raw market price"):
            sync_etf_session_status_to_db(session, _document(_entry()))
        assert session.query(ETFSessionStatus).count() == 0


def test_sync_is_idempotent_and_updates_only_document_owned_fields() -> None:
    factory = _create_session_factory()
    with factory() as session:
        session.add(
            ETFInfo(
                exchange="SSE",
                symbol="510300",
                name="CSI 300 ETF",
                currency="CNY",
                listing_date=date(2012, 5, 28),
                is_active=True,
            )
        )
        session.commit()
        document = _document(_entry(share_ratio="2"))

        first = sync_etf_session_status_to_db(session, document)
        session.commit()
        second = sync_etf_session_status_to_db(session, document)
        session.commit()

        assert (first.inserted_count, first.updated_count, first.unchanged_count) == (1, 0, 0)
        assert (second.inserted_count, second.updated_count, second.unchanged_count) == (0, 0, 1)
        assert session.query(ETFSessionStatus).count() == 1
        assert session.query(ETFSessionStatus).one().share_ratio == Decimal("2.0000000000")


def test_sync_leaves_commit_to_caller_and_preserves_unrelated_rows() -> None:
    factory = _create_session_factory()
    with factory() as session:
        session.add_all(
            [
                ETFInfo(
                    exchange="SSE",
                    symbol="510300",
                    name="CSI 300 ETF",
                    currency="CNY",
                    listing_date=date(2012, 5, 28),
                    is_active=True,
                ),
                ETFInfo(
                    exchange="SSE",
                    symbol="510500",
                    name="CSI 500 ETF",
                    currency="CNY",
                    listing_date=date(2013, 1, 1),
                    is_active=True,
                ),
            ]
        )
        session.flush()
        unrelated_etf = session.query(ETFInfo).filter_by(symbol="510500").one()
        session.add(
            ETFSessionStatus(
                etf_id=unrelated_etf.id,
                trade_date=date(2024, 1, 4),
                status="full_day_suspension",
                reason="unrelated",
                source_uri="https://example.test/unrelated",
                source_published_date=date(2024, 1, 3),
            )
        )
        session.commit()

        result = sync_etf_session_status_to_db(session, _document(_entry()))
        assert result.inserted_count == 1
        assert session.query(ETFSessionStatus).count() == 2
        session.rollback()

        assert session.query(ETFSessionStatus).count() == 1
        assert session.query(ETFSessionStatus).one().reason == "unrelated"


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
