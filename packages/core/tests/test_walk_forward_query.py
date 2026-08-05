# ruff: noqa: E501

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vela_core.models import (
    BacktestBenchmark,
    BacktestEquityCurve,
    BacktestRun,
    Base,
    WalkForwardRun,
    WalkForwardRunWindow,
)
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


def _add_parent(
    session, *, strategy_id: str, finished_at: datetime, official_sessions: list[str] | None = None
) -> WalkForwardRun:
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
            "earliest_required_session": (official_sessions or ["2026-01-01"])[0],
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": official_sessions or ["2026-01-01"],
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


def _add_oos_window(
    session,
    *,
    parent: WalkForwardRun,
    ordinal: int,
    test_start: date,
    test_end: date,
    values: list[tuple[date, str]],
) -> None:
    oos = BacktestRun(
        strategy_id=parent.strategy_id,
        config_version=f"wf-{ordinal:012d}",
        start_date=test_start,
        end_date=test_end,
        parameters_json="{}",
        started_at=parent.started_at,
        finished_at=parent.finished_at,
        status="success",
    )
    session.add(oos)
    session.flush()
    session.add_all(
        BacktestEquityCurve(
            backtest_run_id=oos.id,
            trade_date=trade_date,
            net_value=Decimal(net_value),
            cash=Decimal("0"),
            market_value=Decimal("1"),
            total_assets=Decimal("1"),
            positions_json="[]",
        )
        for trade_date, net_value in values
    )
    session.add_all(
        BacktestBenchmark(backtest_run_id=oos.id, benchmark_key=key, display_name=key)
        for key in ("equal_weight_monthly", "csi_300_buy_hold")
    )
    parent.windows.append(
        WalkForwardRunWindow(
            ordinal=ordinal,
            train_start=date(2025, 1, 1),
            train_end=date(2025, 12, 31),
            test_start=test_start,
            test_end=test_end,
            oos_version=oos.config_version,
            selected_parameters_json={},
            candidate_count=1,
            eligible_count=1,
            skipped_count=0,
            skip_reason_counts_json={},
            train_sharpe=Decimal("1"),
            oos_backtest_run_id=oos.id,
        )
    )


def test_walk_forward_detail_loads_curves_and_derives_stitched_oos(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'detail.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        parent = _add_parent(
            session,
            strategy_id="demo",
            finished_at=datetime(2026, 1, 7),
            official_sessions=["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"],
        )
        _add_oos_window(
            session,
            parent=parent,
            ordinal=0,
            test_start=date(2026, 1, 2),
            test_end=date(2026, 1, 5),
            values=[(date(2026, 1, 2), "1"), (date(2026, 1, 5), "1.1")],
        )
        _add_oos_window(
            session,
            parent=parent,
            ordinal=1,
            test_start=date(2026, 1, 6),
            test_end=date(2026, 1, 7),
            values=[(date(2026, 1, 6), "1"), (date(2026, 1, 7), "0.9")],
        )
        parent.window_count = 2
        session.commit()

    with sessionmaker(bind=engine)() as session:
        row = get_walk_forward_run(session, run_id=1, strategy_id="demo")
        assert row is not None
        assert row.stitched_oos.ending_net_value == Decimal("0.990000")
        assert [
            (point.window_ordinal, point.is_window_start) for point in row.stitched_oos.points
        ] == [
            (0, True),
            (0, False),
            (1, True),
            (1, False),
        ]


def test_walk_forward_list_does_not_load_or_derive_equity_curves(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'list.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _add_parent(session, strategy_id="demo", finished_at=datetime(2026, 1, 1))
        session.commit()

    with sessionmaker(bind=engine)() as session:
        rows, _ = list_walk_forward_runs(session, strategy_id="demo", limit=10)
        assert not hasattr(rows[0], "stitched_oos")


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
