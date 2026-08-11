from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, WalkForwardRun
from vela_core.walk_forward.persistence import (
    LEASE_DURATION_SECONDS,
    claim_walk_forward_run,
    enqueue_walk_forward_run,
    heartbeat_walk_forward_run,
    mark_expired_walk_forward_runs_failed,
    transition_walk_forward_run,
)
from vela_core.walk_forward.runner import WalkForwardRunner


def _row(*, strategy_id: str, status: str, started_at: datetime) -> WalkForwardRun:
    return WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=0,
        walk_forward_config_json={"window": {}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2026-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2026-01-01"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v3",
        evidence_json={},
        status=status,
        started_at=started_at,
        finished_at=None if status in {"queued", "running"} else started_at,
    )


def test_walk_forward_run_supports_durable_lifecycle_and_active_indexes(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'durable-model.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    now = datetime(2026, 1, 1)

    with factory() as session:
        queued = _row(strategy_id="demo", status="queued", started_at=now)
        queued.attempt_count = 0
        session.add(queued)
        session.commit()

        assert queued.claimed_at is None
        assert queued.heartbeat_at is None
        assert queued.lease_expires_at is None
        assert queued.worker_id is None
        assert queued.claim_token is None

        session.add(_row(strategy_id="demo", status="queued", started_at=now))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_walk_forward_run_allows_one_active_strategy_per_terminal_history(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'durable-terminal.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    now = datetime(2026, 1, 1)

    with factory() as session:
        session.add_all(
            [
                _row(strategy_id="demo", status="success", started_at=now),
                _row(strategy_id="demo", status="failed", started_at=now),
            ]
        )
        session.commit()

        session.add_all(
            [
                _row(strategy_id="demo", status="running", started_at=now),
                _row(strategy_id="other", status="running", started_at=now),
            ]
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_durable_lifecycle_helpers_enqueue_claim_recover_and_fence(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'durable-lifecycle.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    now = datetime(2026, 1, 1)

    with factory() as session:
        run_id = enqueue_walk_forward_run(
            session,
            strategy_id="demo",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            walk_forward_config={"window": {}},
            base_strategy_config={"strategy_id": "demo"},
            config_checksum="a" * 64,
            input_data_snapshot=_row(
                strategy_id="demo", status="success", started_at=now
            ).input_data_snapshot_json,
            input_data_checksum="b" * 64,
            started_at=now,
        )

    with factory() as first_session, factory() as second_session:
        first_claim = claim_walk_forward_run(first_session, worker_id="worker-1", now=now)
        second_claim = claim_walk_forward_run(second_session, worker_id="worker-2", now=now)

    assert first_claim is not None
    assert second_claim is None
    assert first_claim.attempt_count == 1
    assert first_claim.lease_expires_at == now + timedelta(seconds=LEASE_DURATION_SECONDS)

    with factory() as session:
        assert not heartbeat_walk_forward_run(
            session,
            run_id=run_id,
            claim_token="stale-token",
            now=now + timedelta(seconds=1),
        )
        session.execute(
            WalkForwardRun.__table__.update()
            .where(WalkForwardRun.id == run_id)
            .values(lease_expires_at=now - timedelta(seconds=1))
        )
        session.commit()

    with factory() as recovery_session:
        recovered = claim_walk_forward_run(
            recovery_session,
            worker_id="worker-2",
            now=now + timedelta(seconds=2),
        )
    assert recovered is not None
    assert recovered.claim_token != first_claim.claim_token
    assert recovered.attempt_count == 2

    with factory() as stale_session:
        assert not transition_walk_forward_run(
            stale_session,
            run_id=run_id,
            claim_token=first_claim.claim_token,
            status="success",
            finished_at=now + timedelta(seconds=3),
        )

    with factory() as owner_session:
        assert transition_walk_forward_run(
            owner_session,
            run_id=run_id,
            claim_token=recovered.claim_token,
            status="failed",
            finished_at=now + timedelta(seconds=4),
            error_message="worker_lost",
        )

    with factory() as session:
        row = session.get(WalkForwardRun, run_id)
        assert row is not None
        assert row.status == "failed"
        assert row.error_message == "worker_lost"


def test_expired_claim_reaches_terminal_failure_at_attempt_limit(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'durable-exhaustion.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    now = datetime(2026, 1, 1)

    with factory() as session:
        run_id = enqueue_walk_forward_run(
            session,
            strategy_id="demo",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            walk_forward_config={"window": {}},
            base_strategy_config={"strategy_id": "demo"},
            config_checksum="a" * 64,
            input_data_snapshot=_row(
                strategy_id="demo", status="success", started_at=now
            ).input_data_snapshot_json,
            input_data_checksum="b" * 64,
            started_at=now,
        )

    for attempt in range(3):
        with factory() as session:
            claim = claim_walk_forward_run(
                session,
                worker_id=f"worker-{attempt}",
                now=now + timedelta(seconds=attempt * 200),
            )
            assert claim is not None
            session.execute(
                WalkForwardRun.__table__.update()
                .where(WalkForwardRun.id == run_id)
                .values(lease_expires_at=now - timedelta(seconds=1))
            )
            session.commit()

    with factory() as session:
        assert mark_expired_walk_forward_runs_failed(session, now=now) == 1

    with factory() as session:
        row = session.get(WalkForwardRun, run_id)
        assert row is not None
        assert row.status == "failed"
        assert row.error_message == "worker_lost: maximum durable attempts exhausted"


def test_synchronous_runner_claims_the_exact_run_it_enqueued(tmp_path, monkeypatch) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'durable-exact-claim.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    now = datetime(2026, 1, 1)

    with factory() as session:
        first = _row(strategy_id="first", status="queued", started_at=now)
        target = _row(
            strategy_id="target",
            status="queued",
            started_at=now + timedelta(seconds=1),
        )
        session.add_all([first, target])
        session.commit()
        first_id = first.id
        target_id = target.id

    runner = object.__new__(WalkForwardRunner)
    observed: dict[str, object] = {}
    monkeypatch.setattr(runner, "enqueue", lambda _session: target_id)

    def complete(_session, run_id: int, claim_token: str) -> str:
        observed.update(run_id=run_id, claim_token=claim_token)
        return "report"

    monkeypatch.setattr(runner, "complete", complete)

    with factory() as session:
        assert runner.run(session) == "report"

    with factory() as session:
        first = session.get(WalkForwardRun, first_id)
        target = session.get(WalkForwardRun, target_id)
        assert first is not None
        assert target is not None
        assert first.status == "queued"
        assert target.status == "running"
        assert observed == {"run_id": target_id, "claim_token": target.claim_token}
