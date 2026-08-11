from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, WalkForwardRun
from vela_core.walk_forward.persistence import enqueue_walk_forward_run, transition_walk_forward_run
from vela_core.walk_forward.worker import WalkForwardWorker


def _manifest() -> dict[str, object]:
    return {
        "version": "wf_provenance_v1",
        "earliest_required_session": "2026-01-01",
        "configured_end_date": "2026-01-01",
        "following_session": None,
        "official_sessions": ["2026-01-01"],
        "active_etfs": [],
        "loaded_price_row_count": 0,
        "first_loaded_price_date": None,
        "last_loaded_price_date": None,
    }


def _enqueue(factory: sessionmaker, *, strategy_id: str) -> int:
    with factory() as session:
        return enqueue_walk_forward_run(
            session,
            strategy_id=strategy_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            walk_forward_config={"window": {}},
            base_strategy_config={"strategy_id": strategy_id},
            config_checksum="a" * 64,
            input_data_snapshot=_manifest(),
            input_data_checksum="b" * 64,
            started_at=datetime(2026, 1, 1),
        )


def test_worker_once_claims_and_executes_only_one_record(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'worker-once.db'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    first_id = _enqueue(factory, strategy_id="first")
    second_id = _enqueue(factory, strategy_id="second")
    completed: list[int] = []

    class FakeRunner:
        def complete(self, session, run_id: int, claim_token: str) -> None:
            completed.append(run_id)
            assert transition_walk_forward_run(
                session,
                run_id=run_id,
                claim_token=claim_token,
                status="success",
                finished_at=datetime(2026, 1, 1),
            )

    monkeypatch.setattr(
        "vela_core.walk_forward.worker.WalkForwardRunner.from_persisted",
        lambda _parent: FakeRunner(),
    )
    worker = WalkForwardWorker(database_url, worker_id="worker-once")

    assert worker.run_once() is True
    assert completed == [first_id]
    with factory() as session:
        assert session.get(WalkForwardRun, first_id).status == "success"
        assert session.get(WalkForwardRun, second_id).status == "queued"


def test_worker_rejects_non_sqlite_database_url() -> None:
    with pytest.raises(ValueError, match="SQLite"):
        WalkForwardWorker("postgresql+psycopg://user:pass@localhost/vela")
