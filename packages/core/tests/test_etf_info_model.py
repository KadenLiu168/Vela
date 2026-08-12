import importlib.util
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import Table, UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from vela_core.models import Base, ETFInfo


def test_etf_info_table_has_required_columns() -> None:
    table = cast(Table, ETFInfo.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "exchange",
        "symbol",
        "name",
        "currency",
        "issuer",
        "category",
        "inception_date",
        "listing_date",
        "expense_ratio",
        "is_active",
        "created_at",
        "updated_at",
    } <= columns


def test_etf_info_has_exchange_symbol_unique_constraint() -> None:
    table = cast(Table, ETFInfo.__table__)
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        {column.name for column in constraint.columns} == {"exchange", "symbol"}
        for constraint in unique_constraints
    )


def test_etf_info_allows_same_symbol_on_different_exchanges() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                ETFInfo(exchange="NYSEARCA", symbol="SPY", name="SPDR S&P 500 ETF", currency="USD"),
                ETFInfo(exchange="TSE", symbol="SPY", name="Sample Japan ETF", currency="JPY"),
            ]
        )
        session.commit()

        assert session.query(ETFInfo).filter_by(symbol="SPY").count() == 2


def test_etf_info_rejects_duplicate_exchange_symbol() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            ETFInfo(exchange="NYSEARCA", symbol="SPY", name="SPDR S&P 500 ETF", currency="USD")
        )
        session.commit()

        session.add(
            ETFInfo(exchange="NYSEARCA", symbol="SPY", name="Duplicate SPY", currency="USD")
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_etf_info_has_lookup_indexes() -> None:
    table = cast(Table, ETFInfo.__table__)
    indexed_columns = {column.name for index in table.indexes for column in index.columns}

    assert {"symbol", "exchange", "is_active"} <= indexed_columns


def test_alembic_target_metadata_includes_etf_info_table() -> None:
    env_path = Path(__file__).parents[3] / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)

    assert spec is not None
    assert spec.loader is not None

    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)

    assert "etf_info" in alembic_env.target_metadata.tables


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
