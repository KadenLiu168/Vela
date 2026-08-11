from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from vela_core.database import create_engine_from_url, create_session_factory
from vela_core.models import WalkForwardRun
from vela_core.walk_forward.persistence import (
    HEARTBEAT_INTERVAL_SECONDS,
    MAX_ATTEMPTS,
    WalkForwardClaim,
    claim_walk_forward_run,
    heartbeat_walk_forward_run,
    mark_expired_walk_forward_runs_failed,
    transition_walk_forward_run,
)
from vela_core.walk_forward.runner import LostWalkForwardClaim, WalkForwardRunner

logger = logging.getLogger(__name__)


class WalkForwardWorker:
    def __init__(
        self,
        database_url: str,
        *,
        worker_id: str | None = None,
        poll_interval_seconds: float = 1.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if make_url(database_url).get_backend_name() != "sqlite":
            raise ValueError("walk-forward-worker only supports SQLite database URLs")
        self.database_url = database_url
        self.worker_id = worker_id or f"walk-forward-worker:{uuid4().hex}"
        self.poll_interval_seconds = max(0.1, min(poll_interval_seconds, 30.0))
        self._clock = clock or (lambda: datetime.now(UTC))

    def run_once(self) -> bool:
        engine = create_engine_from_url(self.database_url)
        factory = create_session_factory(engine)
        try:
            try:
                with factory() as session:
                    now = self._clock()
                    mark_expired_walk_forward_runs_failed(
                        session,
                        now=now,
                        max_attempts=MAX_ATTEMPTS,
                    )
                    claim = claim_walk_forward_run(
                        session,
                        worker_id=self.worker_id,
                        now=now,
                    )
            except OperationalError as exc:
                if _is_sqlite_lock(exc):
                    logger.warning("walk-forward worker deferred on SQLite lock")
                    return False
                raise

            if claim is None:
                return False
            self._execute_claim(factory, claim)
            return True
        finally:
            engine.dispose()

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval_seconds)

    def _execute_claim(self, factory, claim: WalkForwardClaim) -> None:
        stop_heartbeat = threading.Event()
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(factory, claim, stop_heartbeat),
            name=f"wf-heartbeat-{claim.run_id}",
            daemon=True,
        )
        heartbeat_thread.start()
        try:
            with factory() as session:
                parent = session.get(WalkForwardRun, claim.run_id)
                if parent is None:
                    return
                try:
                    WalkForwardRunner.from_persisted(parent).complete(
                        session, claim.run_id, claim.claim_token
                    )
                except LostWalkForwardClaim:
                    logger.info("walk-forward claim lost run_id=%s", claim.run_id)
                except Exception as exc:
                    session.rollback()
                    if not transition_walk_forward_run(
                        session,
                        run_id=claim.run_id,
                        claim_token=claim.claim_token,
                        status="failed",
                        error_message=str(exc),
                        finished_at=self._clock(),
                    ):
                        session.rollback()
        finally:
            stop_heartbeat.set()
            heartbeat_thread.join(timeout=HEARTBEAT_INTERVAL_SECONDS)

    def _heartbeat_loop(self, factory, claim: WalkForwardClaim, stop: threading.Event) -> None:
        while not stop.wait(HEARTBEAT_INTERVAL_SECONDS):
            try:
                with factory() as session:
                    if not heartbeat_walk_forward_run(
                        session,
                        run_id=claim.run_id,
                        claim_token=claim.claim_token,
                        now=self._clock(),
                    ):
                        return
            except OperationalError as exc:
                if _is_sqlite_lock(exc):
                    continue
                logger.warning("walk-forward heartbeat failed run_id=%s", claim.run_id)
                return


def _is_sqlite_lock(exc: OperationalError) -> bool:
    return "database is locked" in str(exc).lower() or "database is busy" in str(exc).lower()
