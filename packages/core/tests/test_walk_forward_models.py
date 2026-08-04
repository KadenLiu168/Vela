from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, WalkForwardRun, WalkForwardRunWindow


def _parent() -> WalkForwardRun:
    return WalkForwardRun(
        strategy_id="demo",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=1,
        walk_forward_config_json={"window": {"start_date": "2026-01-01"}},
        base_strategy_config_json={"strategy_id": "demo"},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={"version": "wf_provenance_v1"},
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v1",
        evidence_json={},
        started_at=datetime(2026, 1, 1),
        finished_at=datetime(2026, 1, 2),
    )


def _window(*, ordinal: int = 0, oos_backtest_run_id: int = 7) -> WalkForwardRunWindow:
    return WalkForwardRunWindow(
        ordinal=ordinal,
        train_start=date(2025, 1, 1),
        train_end=date(2025, 12, 31),
        test_start=date(2026, 1, 1),
        test_end=date(2026, 12, 31),
        oos_version="wf-000000000000",
        selected_parameters_json={"parameters.selection.top_n": 1},
        candidate_count=2,
        eligible_count=1,
        skipped_count=1,
        skip_reason_counts_json={"training_error": 1},
        train_sharpe=Decimal("1.2"),
        oos_backtest_run_id=oos_backtest_run_id,
    )


def test_walk_forward_models_round_trip_typed_parent_and_ordered_children(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'models.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    with factory() as session:
        parent = _parent()
        parent.windows.extend([_window(ordinal=0, oos_backtest_run_id=7)])
        session.add(parent)
        session.commit()

    with factory() as session:
        loaded = session.scalar(select(WalkForwardRun).where(WalkForwardRun.strategy_id == "demo"))
        assert loaded is not None
        assert loaded.start_date == date(2026, 1, 1)
        assert loaded.windows[0].ordinal == 0
        assert loaded.windows[0].train_sharpe == Decimal("1.200000")
        assert not hasattr(loaded, "equity_curve")


@pytest.mark.parametrize(
    "mutator",
    [
        lambda row: setattr(row, "candidate_count", -1),
        lambda row: setattr(row, "eligible_count", 2),
        lambda row: setattr(row, "skipped_count", 2),
    ],
)
def test_walk_forward_window_database_checks_reject_invalid_counts(tmp_path, mutator) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'checks.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        parent = _parent()
        child = _window()
        mutator(child)
        parent.windows.append(child)
        session.add(parent)
        with pytest.raises(IntegrityError):
            session.commit()


def test_walk_forward_window_ordinal_and_oos_ownership_are_unique(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'unique.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        parent = _parent()
        parent.window_count = 2
        parent.windows.extend([_window(ordinal=0), _window(ordinal=0, oos_backtest_run_id=8)])
        session.add(parent)
        with pytest.raises(IntegrityError):
            session.commit()
