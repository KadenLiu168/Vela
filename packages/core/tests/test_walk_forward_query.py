from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, WalkForwardRun
from vela_core.walk_forward.evidence import PersistedDataContractError
from vela_core.walk_forward.query import (
    get_walk_forward_run,
    list_walk_forward_runs,
)


def _valid_evidence() -> dict[str, object]:
    summary = {
        "mean": 0.1,
        "median": 0.1,
        "min": 0.1,
        "max": 0.1,
        "std": 0.0,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    rate = {
        "numerator": 3,
        "denominator": 3,
        "value": 1.0,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    benchmark = {
        "total_return_difference": summary,
        "annualized_return_difference": summary,
        "tracking_error": summary,
        "information_ratio": summary,
        "outperformance_rate": rate,
    }
    return {
        "metrics": {
            name: summary
            for name in (
                "total_return",
                "annualized_return",
                "sharpe_ratio",
                "max_drawdown",
                "volatility",
                "sortino_ratio",
                "calmar_ratio",
                "longest_drawdown_duration_sessions",
            )
        },
        "positive_window_rate": rate,
        "generalization_gap": summary,
        "benchmarks": {"equal_weight_monthly": benchmark, "csi_300_buy_hold": benchmark},
        "parameter_stability": {},
    }


def _add_parent(session, *, strategy_id: str, finished_at: datetime) -> WalkForwardRun:
    row = WalkForwardRun(
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
        evidence_version="wf_evidence_v1",
        evidence_json=_valid_evidence(),
        started_at=finished_at,
        finished_at=finished_at,
    )
    session.add(row)
    session.flush()
    return row


def test_walk_forward_queries_filter_order_count_and_pagination(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'query.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _add_parent(session, strategy_id="demo", finished_at=datetime(2026, 1, 1))
        _add_parent(session, strategy_id="demo", finished_at=datetime(2026, 1, 2))
        _add_parent(session, strategy_id="other", finished_at=datetime(2026, 1, 3))
        session.commit()

    with sessionmaker(bind=engine)() as session:
        rows, total = list_walk_forward_runs(session, strategy_id="demo", limit=1, offset=0)
        assert total == 2
        assert [row.finished_at for row in rows] == [datetime(2026, 1, 2)]
        assert get_walk_forward_run(session, run_id=3, strategy_id="demo") is None
        with pytest.raises(ValueError):
            list_walk_forward_runs(session, strategy_id="demo", limit=0, offset=0)


def test_walk_forward_queries_fail_closed_on_corrupt_evidence(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'corrupt.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        row = _add_parent(session, strategy_id="demo", finished_at=datetime(2026, 1, 1))
        row.evidence_version = "wf_evidence_v0"
        session.commit()

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


@pytest.mark.parametrize("corruption", ["provenance", "manifest", "children"])
def test_walk_forward_queries_fail_closed_on_contract_drift(tmp_path, corruption: str) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / f'{corruption}.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        row = _add_parent(session, strategy_id="demo", finished_at=datetime(2026, 1, 1))
        if corruption == "provenance":
            row.provenance_version = "wf_provenance_v0"
        elif corruption == "manifest":
            row.input_data_snapshot_json = {"version": "wf_provenance_v1"}
        else:
            row.window_count = 1
        session.commit()

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")
