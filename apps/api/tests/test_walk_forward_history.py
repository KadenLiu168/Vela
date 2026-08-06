# ruff: noqa: E501

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import (
    BacktestBenchmark,
    BacktestEquityCurve,
    BacktestRun,
    WalkForwardRun,
    WalkForwardRunWindow,
)

from tests.integration_data import prepare_sqlite_database


def _summary(value: float = 0.1) -> dict[str, object]:
    return {
        "mean": value,
        "median": value,
        "min": value,
        "max": value,
        "std": 0.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }


def _empty_summary() -> dict[str, object]:
    return {
        "mean": None,
        "median": None,
        "min": None,
        "max": None,
        "std": None,
        "window_count": 1,
        "valid_count": 0,
        "evidence_status": "insufficient_evidence",
    }


def _v2_evidence() -> dict[str, object]:
    summary = _summary()
    rate = {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }
    csi_benchmark = {
        "total_return_difference": summary,
        "annualized_return_difference": summary,
        "tracking_error": summary,
        "information_ratio": summary,
        "outperformance_rate": rate,
        "capm_alpha": _summary(0.5),
        "capm_beta": _summary(1.1),
        "capm_r_squared": _summary(0.8),
        "up_capture_ratio": _summary(1.2),
        "down_capture_ratio": _summary(0.7),
    }
    equal_weight_benchmark = {
        **csi_benchmark,
        "capm_alpha": _empty_summary(),
        "capm_beta": _empty_summary(),
        "capm_r_squared": _empty_summary(),
    }
    return {
        "metrics": {
            key: summary
            for key in (
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
        "benchmarks": {
            "equal_weight_monthly": equal_weight_benchmark,
            "csi_300_buy_hold": csi_benchmark,
        },
        "parameter_stability": {},
    }


def _evidence() -> dict[str, object]:
    summary = _summary()
    rate = {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
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
            key: summary
            for key in (
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
        "benchmarks": {
            "equal_weight_monthly": benchmark,
            "csi_300_buy_hold": benchmark,
        },
        "parameter_stability": {},
    }


def _add_history(session, *, strategy_id: str, finished_at: datetime) -> WalkForwardRun:
    oos = BacktestRun(
        strategy_id=strategy_id,
        config_version="wf-000000000001",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        parameters_json="{}",
        started_at=finished_at,
        finished_at=finished_at,
        status="success",
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.100000"),
        max_drawdown=Decimal("-0.050000"),
        volatility=Decimal("0.100000"),
        sharpe_ratio=Decimal("1.000000"),
        sortino_ratio=Decimal("1.200000"),
        calmar_ratio=Decimal("2.000000"),
        longest_drawdown_duration_sessions=3,
        longest_drawdown_peak_date=date(2026, 2, 2),
        longest_drawdown_trough_date=date(2026, 2, 3),
    )
    oos.benchmarks.extend(
        [
            BacktestBenchmark(
                benchmark_key=key,
                display_name=key,
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
                sortino_ratio=Decimal("1.100000"),
                calmar_ratio=Decimal("1.900000"),
                longest_drawdown_duration_sessions=2,
                longest_drawdown_peak_date=date(2026, 2, 2),
                longest_drawdown_trough_date=date(2026, 2, 3),
                longest_drawdown_recovery_date=date(2026, 2, 4),
                tracking_error=Decimal("0.020000"),
                information_ratio=Decimal("0.300000"),
            )
            for key in ("equal_weight_monthly", "csi_300_buy_hold")
        ]
    )
    oos.equity_curve.extend(
        BacktestEquityCurve(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            cash=Decimal("0"),
            market_value=Decimal("1"),
            total_assets=Decimal("1"),
            positions_json="[]",
        )
        for trade_date in (date(2026, 1, 1), date(2026, 12, 31))
    )
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=1,
        walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2025-01-01", "2026-01-01", "2026-12-31"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v1",
        evidence_json=_evidence(),
        started_at=finished_at,
        finished_at=finished_at,
    )
    parent.windows.append(
        WalkForwardRunWindow(
            ordinal=0,
            train_start=date(2025, 1, 1),
            train_end=date(2025, 12, 31),
            test_start=date(2026, 1, 1),
            test_end=date(2026, 12, 31),
            oos_version="wf-000000000001",
            selected_parameters_json={"parameters.selection.top_n": 1},
            candidate_count=1,
            eligible_count=1,
            skipped_count=0,
            skip_reason_counts_json={},
            train_sharpe=Decimal("1.100000"),
            oos_backtest_run=oos,
        )
    )
    session.add(parent)
    session.flush()
    return parent


def _add_v2_history(session, *, strategy_id: str, finished_at: datetime) -> WalkForwardRun:
    oos = BacktestRun(
        strategy_id=strategy_id,
        config_version="wf-000000000001",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        parameters_json='{"benchmark_regime_metric_version":"benchmark_regime_metrics_v1"}',
        started_at=finished_at,
        finished_at=finished_at,
        status="success",
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.100000"),
        max_drawdown=Decimal("-0.050000"),
        volatility=Decimal("0.100000"),
        sharpe_ratio=Decimal("1.000000"),
    )
    oos.benchmarks.extend(
        [
            BacktestBenchmark(
                benchmark_key="equal_weight_monthly",
                display_name="Equal-weight monthly rebalanced portfolio",
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
                tracking_error=Decimal("0.020000"),
                information_ratio=Decimal("0.300000"),
                up_capture_ratio=Decimal("1.200000"),
                up_capture_observation_count=8,
                down_capture_ratio=Decimal("0.700000"),
                down_capture_observation_count=3,
            ),
            BacktestBenchmark(
                benchmark_key="csi_300_buy_hold",
                display_name="CSI 300 buy-and-hold",
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
                tracking_error=Decimal("0.020000"),
                information_ratio=Decimal("0.300000"),
                capm_alpha=Decimal("0.500000"),
                capm_beta=Decimal("1.100000"),
                capm_r_squared=Decimal("0.800000"),
                capm_observation_count=240,
                up_capture_ratio=Decimal("1.200000"),
                up_capture_observation_count=8,
                down_capture_ratio=Decimal("0.700000"),
                down_capture_observation_count=3,
            ),
        ]
    )
    oos.equity_curve.extend(
        BacktestEquityCurve(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            cash=Decimal("0"),
            market_value=Decimal("1"),
            total_assets=Decimal("1"),
            positions_json="[]",
        )
        for trade_date in (date(2026, 1, 1), date(2026, 12, 31))
    )
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=1,
        walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2025-01-01", "2026-01-01", "2026-12-31"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v2",
        evidence_json=_v2_evidence(),
        started_at=finished_at,
        finished_at=finished_at,
    )
    parent.windows.append(
        WalkForwardRunWindow(
            ordinal=0,
            train_start=date(2025, 1, 1),
            train_end=date(2025, 12, 31),
            test_start=date(2026, 1, 1),
            test_end=date(2026, 12, 31),
            oos_version="wf-000000000001",
            selected_parameters_json={"parameters.selection.top_n": 1},
            candidate_count=1,
            eligible_count=1,
            skipped_count=0,
            skip_reason_counts_json={},
            train_sharpe=Decimal("1.100000"),
            oos_backtest_run=oos,
        )
    )
    session.add(parent)
    session.flush()
    return parent


def _add_v3_history(session, *, strategy_id: str, finished_at: datetime) -> WalkForwardRun:
    oos = BacktestRun(
        strategy_id=strategy_id,
        config_version="wf-000000000001",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        parameters_json=(
            '{"benchmark_regime_metric_version":"benchmark_regime_metrics_v1",'
            '"tail_distribution_metric_version":"tail_distribution_metrics_v1"}'
        ),
        started_at=finished_at,
        finished_at=finished_at,
        status="success",
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.100000"),
        max_drawdown=Decimal("-0.050000"),
        volatility=Decimal("0.100000"),
        sharpe_ratio=Decimal("1.000000"),
        historical_var_95=Decimal("0.020000"),
        historical_cvar_95=Decimal("0.060000"),
        return_skewness=Decimal("0.100000"),
        return_excess_kurtosis=Decimal("0.200000"),
        distribution_observation_count=100,
        tail_observation_count=5,
    )
    oos.benchmarks.extend(
        [
            BacktestBenchmark(
                benchmark_key="equal_weight_monthly",
                display_name="Equal-weight monthly rebalanced portfolio",
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
                tracking_error=Decimal("0.020000"),
                information_ratio=Decimal("0.300000"),
                up_capture_ratio=Decimal("1.200000"),
                up_capture_observation_count=8,
                down_capture_ratio=Decimal("0.700000"),
                down_capture_observation_count=3,
                historical_var_95=Decimal("0.010000"),
                historical_cvar_95=Decimal("0.030000"),
                return_skewness=Decimal("-0.100000"),
                return_excess_kurtosis=Decimal("0.100000"),
                distribution_observation_count=100,
                tail_observation_count=5,
            ),
            BacktestBenchmark(
                benchmark_key="csi_300_buy_hold",
                display_name="CSI 300 buy-and-hold",
                total_return=Decimal("0.080000"),
                annualized_return=Decimal("0.080000"),
                max_drawdown=Decimal("-0.040000"),
                volatility=Decimal("0.090000"),
                sharpe_ratio=Decimal("0.900000"),
                tracking_error=Decimal("0.020000"),
                information_ratio=Decimal("0.300000"),
                capm_alpha=Decimal("0.500000"),
                capm_beta=Decimal("1.100000"),
                capm_r_squared=Decimal("0.800000"),
                capm_observation_count=240,
                up_capture_ratio=Decimal("1.200000"),
                up_capture_observation_count=8,
                down_capture_ratio=Decimal("0.700000"),
                down_capture_observation_count=3,
                historical_var_95=Decimal("0.040000"),
                historical_cvar_95=Decimal("0.080000"),
                return_skewness=Decimal("0.200000"),
                return_excess_kurtosis=Decimal("-0.300000"),
                distribution_observation_count=100,
                tail_observation_count=5,
            ),
        ]
    )
    oos.equity_curve.extend(
        BacktestEquityCurve(
            trade_date=trade_date,
            net_value=Decimal("1.000000"),
            cash=Decimal("0"),
            market_value=Decimal("1"),
            total_assets=Decimal("1"),
            positions_json="[]",
        )
        for trade_date in (date(2026, 1, 1), date(2026, 12, 31))
    )
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=1,
        walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2025-01-01", "2026-01-01", "2026-12-31"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v3",
        evidence_json=_v3_evidence(),
        started_at=finished_at,
        finished_at=finished_at,
    )
    parent.windows.append(
        WalkForwardRunWindow(
            ordinal=0,
            train_start=date(2025, 1, 1),
            train_end=date(2025, 12, 31),
            test_start=date(2026, 1, 1),
            test_end=date(2026, 12, 31),
            oos_version="wf-000000000001",
            selected_parameters_json={"parameters.selection.top_n": 1},
            candidate_count=1,
            eligible_count=1,
            skipped_count=0,
            skip_reason_counts_json={},
            train_sharpe=Decimal("1.100000"),
            oos_backtest_run=oos,
        )
    )
    session.add(parent)
    session.flush()
    return parent


def _tail_owner(*, var: float, cvar: float, skew: float, kurt: float) -> dict[str, object]:
    return {
        "historical_var_95": var,
        "historical_cvar_95": cvar,
        "return_skewness": skew,
        "return_excess_kurtosis": kurt,
        "observation_count": 100,
        "tail_observation_count": 5,
        "evidence_status": "sufficient",
    }


def _tail_agg(value: float) -> dict[str, object]:
    return {
        "mean": value,
        "median": value,
        "min": value,
        "max": value,
        "std": 0.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }


def _v3_evidence() -> dict[str, object]:
    document = _v2_evidence()
    owners = {
        "strategy": _tail_owner(var=0.02, cvar=0.06, skew=0.1, kurt=0.2),
        "equal_weight_monthly": _tail_owner(var=0.01, cvar=0.03, skew=-0.1, kurt=0.1),
        "csi_300_buy_hold": _tail_owner(var=0.04, cvar=0.08, skew=0.2, kurt=-0.3),
    }
    metrics = (
        "historical_var_95",
        "historical_cvar_95",
        "return_skewness",
        "return_excess_kurtosis",
    )
    document["tail_distribution"] = {
        "per_window": [{"ordinal": 0, "owners": deepcopy(owners)}],
        "aggregates": {
            owner: {metric: _tail_agg(values[metric]) for metric in metrics}
            for owner, values in owners.items()
        },
    }
    return document


def _add_history_windows(
    session,
    *,
    strategy_id: str,
    finished_at: datetime,
    official_sessions: list[str],
    windows: list[tuple[int, date, date, date, list[tuple[date, Decimal]]]],
) -> WalkForwardRun:
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=len(windows),
        walk_forward_config_json={"strategy": {"base_config": "strategy.yaml"}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": official_sessions,
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v1",
        evidence_json=_evidence(),
        started_at=finished_at,
        finished_at=finished_at,
    )
    for ordinal, train_start, test_start, test_end, curve in windows:
        oos = BacktestRun(
            strategy_id=strategy_id,
            config_version="wf-000000000001",
            start_date=test_start,
            end_date=test_end,
            parameters_json="{}",
            started_at=finished_at,
            finished_at=finished_at,
            status="success",
            total_return=Decimal("0.100000"),
            annualized_return=Decimal("0.100000"),
            max_drawdown=Decimal("-0.050000"),
            volatility=Decimal("0.100000"),
            sharpe_ratio=Decimal("1.000000"),
            sortino_ratio=Decimal("1.200000"),
            calmar_ratio=Decimal("2.000000"),
            longest_drawdown_duration_sessions=3,
            longest_drawdown_peak_date=date(2026, 2, 2),
            longest_drawdown_trough_date=date(2026, 2, 3),
        )
        oos.benchmarks.extend(
            [
                BacktestBenchmark(
                    benchmark_key=key,
                    display_name=key,
                    total_return=Decimal("0.080000"),
                    annualized_return=Decimal("0.080000"),
                    max_drawdown=Decimal("-0.040000"),
                    volatility=Decimal("0.090000"),
                    sharpe_ratio=Decimal("0.900000"),
                    sortino_ratio=Decimal("1.100000"),
                    calmar_ratio=Decimal("1.900000"),
                    longest_drawdown_duration_sessions=2,
                    longest_drawdown_peak_date=date(2026, 2, 2),
                    longest_drawdown_trough_date=date(2026, 2, 3),
                    longest_drawdown_recovery_date=date(2026, 2, 4),
                    tracking_error=Decimal("0.020000"),
                    information_ratio=Decimal("0.300000"),
                )
                for key in ("equal_weight_monthly", "csi_300_buy_hold")
            ]
        )
        oos.equity_curve.extend(
            BacktestEquityCurve(
                trade_date=trade_date,
                net_value=net_value,
                cash=Decimal("0"),
                market_value=Decimal("1"),
                total_assets=Decimal("1"),
                positions_json="[]",
            )
            for trade_date, net_value in curve
        )
        parent.windows.append(
            WalkForwardRunWindow(
                ordinal=ordinal,
                train_start=train_start,
                train_end=train_start,
                test_start=test_start,
                test_end=test_end,
                oos_version="wf-000000000001",
                selected_parameters_json={"parameters.selection.top_n": 1},
                candidate_count=1,
                eligible_count=1,
                skipped_count=0,
                skip_reason_counts_json={},
                train_sharpe=Decimal("1.100000"),
                oos_backtest_run=oos,
            )
        )
    session.add(parent)
    session.flush()
    return parent


def test_walk_forward_history_api_returns_typed_current_strategy_page_and_detail(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-api.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        current = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        older = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 1, tzinfo=UTC),
        )
        foreign = _add_history(
            session,
            strategy_id="other",
            finished_at=datetime(2026, 2, 3, tzinfo=UTC),
        )
        session.commit()
        current_id, older_id, foreign_id = current.id, older.id, foreign.id

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        page = client.get("/api/walk-forwards?limit=10&offset=0")
        offset_page = client.get("/api/walk-forwards?limit=1&offset=1")
        detail = client.get(f"/api/walk-forwards/{current_id}")
        foreign_detail = client.get(f"/api/walk-forwards/{foreign_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert [item["run_id"] for item in page.json()["runs"]] == [current_id, older_id]
    assert offset_page.status_code == 200
    assert offset_page.json()["total"] == 2
    assert offset_page.json()["limit"] == 1
    assert offset_page.json()["offset"] == 1
    assert [item["run_id"] for item in offset_page.json()["runs"]] == [older_id]
    assert b"strategyId" not in page.request.url.query
    assert detail.status_code == 200
    body = detail.json()
    assert body["run"]["provenance_version"] == "wf_provenance_v1"
    assert body["evidence_version"] == "wf_evidence_v1"
    assert body["configuration"]["config_checksum"] == "a" * 64
    assert body["input_provenance"]["manifest"]["following_session"] is None
    assert set(body["evidence"]["metrics"]) == {
        "total_return",
        "annualized_return",
        "sharpe_ratio",
        "max_drawdown",
        "volatility",
        "sortino_ratio",
        "calmar_ratio",
        "longest_drawdown_duration_sessions",
    }
    assert set(body["evidence"]["benchmarks"]) == {
        "equal_weight_monthly",
        "csi_300_buy_hold",
    }
    assert body["windows"][0]["train_sharpe"] == "1.100000"
    assert body["windows"][0]["oos_backtest"]["sortino_ratio"] == "1.200000"
    assert [item["key"] for item in body["windows"][0]["oos_backtest"]["benchmarks"]] == [
        "equal_weight_monthly",
        "csi_300_buy_hold",
    ]
    assert body["stitched_oos"] == {
        "status": "available",
        "initial_net_value": "1.000000",
        "ending_net_value": "1.000000",
        "total_return": "0.000000",
        "points": [
            {
                "trade_date": "2026-01-01",
                "net_value": "1.000000",
                "window_ordinal": 0,
                "is_window_start": True,
            },
            {
                "trade_date": "2026-12-31",
                "net_value": "1.000000",
                "window_ordinal": 0,
                "is_window_start": False,
            },
        ],
    }
    openapi = client.get("/openapi.json").json()
    assert (
        "stitched_oos"
        in openapi["components"]["schemas"]["WalkForwardDetailResponse"]["properties"]
    )
    stitched_schema = openapi["components"]["schemas"]["StitchedOosResponse"]
    assert set(stitched_schema["properties"]) == {
        "status",
        "initial_net_value",
        "ending_net_value",
        "total_return",
        "points",
    }
    assert set(stitched_schema["properties"]["status"]["enum"]) == {
        "available",
        "unavailable_non_contiguous_windows",
    }
    point_schema = openapi["components"]["schemas"]["StitchedOosPointResponse"]
    assert set(point_schema["properties"]) == {
        "trade_date",
        "net_value",
        "window_ordinal",
        "is_window_start",
    }
    assert point_schema["properties"]["window_ordinal"]["type"] == "integer"
    assert point_schema["properties"]["is_window_start"]["type"] == "boolean"
    assert "equity_curve" not in str(body)
    assert foreign_detail.status_code == 404
    assert foreign_detail.json()["error"]["category"] == "not_found"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_walk_forward_history_api_rejects_invalid_pagination(tmp_path, query: str) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-pagination.db'}"
    prepare_sqlite_database(database_url)
    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards?{query}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert response.json()["error"]["category"] == "validation"


def test_walk_forward_detail_fails_closed_on_foreign_oos_ownership(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        parent.windows[0].oos_backtest_run.strategy_id = "other"
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app, raise_server_exceptions=False).get(
            f"/api/walk-forwards/{run_id}"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "unexpected_error",
            "category": "unexpected",
            "message": "Unexpected API error",
        }
    }


def test_walk_forward_detail_fails_closed_on_corrupt_eligible_curve(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-curve-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        for point in parent.windows[0].oos_backtest_run.equity_curve:
            session.delete(point)
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app, raise_server_exceptions=False).get(
            f"/api/walk-forwards/{run_id}"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 500
    assert response.json()["error"]["category"] == "unexpected"


def test_walk_forward_detail_returns_v2_regime_evidence_and_per_window_values(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-v2.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_v2_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_version"] == "wf_evidence_v2"
    csi_evidence = body["evidence"]["benchmarks"]["csi_300_buy_hold"]
    assert csi_evidence["capm_alpha"]["valid_count"] == 1
    assert csi_evidence["capm_beta"]["valid_count"] == 1
    assert csi_evidence["capm_r_squared"]["valid_count"] == 1
    assert csi_evidence["up_capture_ratio"]["valid_count"] == 1
    assert csi_evidence["down_capture_ratio"]["valid_count"] == 1
    equal_weight_evidence = body["evidence"]["benchmarks"]["equal_weight_monthly"]
    assert equal_weight_evidence["capm_alpha"]["valid_count"] == 0
    assert equal_weight_evidence["up_capture_ratio"]["valid_count"] == 1
    window_benchmarks = body["windows"][0]["oos_backtest"]["benchmarks"]
    by_key = {benchmark["key"]: benchmark for benchmark in window_benchmarks}
    assert by_key["csi_300_buy_hold"]["capm_alpha"] == "0.500000"
    assert by_key["csi_300_buy_hold"]["capm_beta"] == "1.100000"
    assert by_key["csi_300_buy_hold"]["capm_r_squared"] == "0.800000"
    assert by_key["csi_300_buy_hold"]["capm_observation_count"] == 240
    assert by_key["csi_300_buy_hold"]["up_capture_ratio"] == "1.200000"
    assert by_key["csi_300_buy_hold"]["up_capture_observation_count"] == 8
    assert by_key["csi_300_buy_hold"]["down_capture_ratio"] == "0.700000"
    assert by_key["csi_300_buy_hold"]["down_capture_observation_count"] == 3
    assert by_key["equal_weight_monthly"]["capm_alpha"] is None
    assert by_key["equal_weight_monthly"]["up_capture_ratio"] == "1.200000"


def test_walk_forward_detail_keeps_legacy_v1_evidence_without_fabricated_regime(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-v1-legacy.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_version"] == "wf_evidence_v1"
    assert "capm_alpha" not in body["evidence"]["benchmarks"]["csi_300_buy_hold"]
    assert body["evidence"]["benchmarks"]["csi_300_buy_hold"]["tracking_error"]["valid_count"] == 1


def test_walk_forward_detail_fails_closed_on_corrupt_v2_evidence(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-v2-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_v2_history(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
        )
        # Break the source-row ownership contract: the v2 document claims one
        # valid CAPM window while the OOS benchmark row no longer carries it.
        for benchmark in parent.windows[0].oos_backtest_run.benchmarks:
            if benchmark.benchmark_key == "csi_300_buy_hold":
                benchmark.capm_alpha = None
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app, raise_server_exceptions=False).get(
            f"/api/walk-forwards/{run_id}"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 500
    assert response.json()["error"]["category"] == "unexpected"
    assert "windows" not in response.json()


def test_walk_forward_detail_stitches_adjacent_windows_with_compounding(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-stitched.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history_windows(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            official_sessions=[
                "2025-01-01",
                "2026-01-01",
                "2026-06-30",
                "2026-07-01",
                "2026-12-31",
            ],
            windows=[
                (
                    0,
                    date(2025, 1, 1),
                    date(2026, 1, 1),
                    date(2026, 6, 30),
                    [
                        (date(2026, 1, 1), Decimal("1.000000")),
                        (date(2026, 6, 30), Decimal("1.100000")),
                    ],
                ),
                (
                    1,
                    date(2026, 1, 1),
                    date(2026, 7, 1),
                    date(2026, 12, 31),
                    [
                        (date(2026, 7, 1), Decimal("1.000000")),
                        (date(2026, 12, 31), Decimal("0.900000")),
                    ],
                ),
            ],
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["stitched_oos"] == {
        "status": "available",
        "initial_net_value": "1.000000",
        "ending_net_value": "0.990000",
        "total_return": "-0.010000",
        "points": [
            {
                "trade_date": "2026-01-01",
                "net_value": "1.000000",
                "window_ordinal": 0,
                "is_window_start": True,
            },
            {
                "trade_date": "2026-06-30",
                "net_value": "1.100000",
                "window_ordinal": 0,
                "is_window_start": False,
            },
            {
                "trade_date": "2026-07-01",
                "net_value": "1.100000",
                "window_ordinal": 1,
                "is_window_start": True,
            },
            {
                "trade_date": "2026-12-31",
                "net_value": "0.990000",
                "window_ordinal": 1,
                "is_window_start": False,
            },
        ],
    }


def test_walk_forward_detail_reports_unavailable_for_non_contiguous_windows(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-gap.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history_windows(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            official_sessions=[
                "2025-01-01",
                "2026-01-01",
                "2026-06-30",
                "2026-07-15",
                "2026-09-01",
                "2026-12-31",
            ],
            windows=[
                (
                    0,
                    date(2025, 1, 1),
                    date(2026, 1, 1),
                    date(2026, 6, 30),
                    [
                        (date(2026, 1, 1), Decimal("1.000000")),
                        (date(2026, 6, 30), Decimal("1.100000")),
                    ],
                ),
                (
                    1,
                    date(2026, 1, 1),
                    date(2026, 9, 1),
                    date(2026, 12, 31),
                    [
                        (date(2026, 9, 1), Decimal("1.000000")),
                        (date(2026, 12, 31), Decimal("0.900000")),
                    ],
                ),
            ],
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["stitched_oos"] == {
        "status": "unavailable_non_contiguous_windows",
        "initial_net_value": None,
        "ending_net_value": None,
        "total_return": None,
        "points": [],
    }
    assert len(body["windows"]) == 2
    assert [window["ordinal"] for window in body["windows"]] == [0, 1]
    assert body["windows"][1]["oos_backtest"]["total_return"] == "0.100000"
    assert [item["key"] for item in body["windows"][0]["oos_backtest"]["benchmarks"]] == [
        "equal_weight_monthly",
        "csi_300_buy_hold",
    ]


def test_walk_forward_detail_fails_closed_on_missing_session_bound(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-session-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        parent = _add_history_windows(
            session,
            strategy_id="Dual_momentum",
            finished_at=datetime(2026, 2, 2, tzinfo=UTC),
            official_sessions=["2025-01-01", "2026-01-01"],
            windows=[
                (
                    0,
                    date(2025, 1, 1),
                    date(2026, 1, 1),
                    date(2026, 12, 31),
                    [
                        (date(2026, 1, 1), Decimal("1.000000")),
                        (date(2026, 12, 31), Decimal("1.100000")),
                    ],
                ),
            ],
        )
        session.commit()
        run_id = parent.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app, raise_server_exceptions=False).get(
            f"/api/walk-forwards/{run_id}"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "unexpected_error",
            "category": "unexpected",
            "message": "Unexpected API error",
        }
    }


def test_walk_forward_detail_returns_v3_tail_distribution_evidence(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'wf-detail-v3.db'}"
    session_factory = prepare_sqlite_database(database_url)
    finished_at = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
    with session_factory() as session:
        row = _add_v3_history(session, strategy_id="Dual_momentum", finished_at=finished_at)
        session.commit()
        run_id = row.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get(f"/api/walk-forwards/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_version"] == "wf_evidence_v3"
    evidence = body["evidence"]
    tail = evidence["tail_distribution"]
    assert len(tail["per_window"]) == 1
    owners = tail["per_window"][0]["owners"]
    assert set(owners) == {"strategy", "equal_weight_monthly", "csi_300_buy_hold"}
    assert owners["strategy"]["historical_var_95"] == 0.02
    assert owners["strategy"]["historical_cvar_95"] == 0.06
    assert owners["strategy"]["return_skewness"] == 0.1
    assert owners["strategy"]["return_excess_kurtosis"] == 0.2
    assert owners["strategy"]["observation_count"] == 100
    assert owners["strategy"]["tail_observation_count"] == 5
    assert owners["strategy"]["evidence_status"] == "sufficient"
    assert owners["equal_weight_monthly"]["historical_var_95"] == 0.01
    assert owners["csi_300_buy_hold"]["historical_var_95"] == 0.04
    aggregates = tail["aggregates"]
    assert aggregates["strategy"]["historical_var_95"]["mean"] == 0.02
    assert aggregates["strategy"]["historical_var_95"]["valid_count"] == 1
    assert aggregates["csi_300_buy_hold"]["return_excess_kurtosis"]["max"] == -0.3
    # Stored per-window OOS benchmark evidence remains on the owning window.
    oos_benchmarks = body["windows"][0]["oos_backtest"]["benchmarks"]
    by_key = {benchmark["key"]: benchmark for benchmark in oos_benchmarks}
    assert by_key["equal_weight_monthly"]["historical_var_95"] == "0.010000"
    assert by_key["equal_weight_monthly"]["distribution_evidence_status"] == "sufficient"
    assert by_key["csi_300_buy_hold"]["historical_cvar_95"] == "0.080000"


def test_walk_forward_detail_returns_no_partial_v3_response_on_corrupt_evidence(
    tmp_path,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'wf-detail-v3-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    finished_at = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
    with session_factory() as session:
        row = _add_v3_history(session, strategy_id="Dual_momentum", finished_at=finished_at)
        evidence = deepcopy(row.evidence_json)
        evidence["tail_distribution"]["per_window"][0]["owners"]["strategy"][
            "historical_var_95"
        ] = 0.99
        row.evidence_json = evidence
        session.commit()
        run_id = row.id

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app, raise_server_exceptions=False).get(
            f"/api/walk-forwards/{run_id}"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    # Corrupt v3 fails closed with the standard error envelope and no partial detail.
    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "unexpected_error",
            "category": "unexpected",
            "message": "Unexpected API error",
        }
    }
