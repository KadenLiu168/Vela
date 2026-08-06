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
from vela_core.walk_forward.evidence import (
    EVIDENCE_VERSION,
    EVIDENCE_VERSION_V2,
    PersistedDataContractError,
    WalkForwardEvidenceV2,
    validate_wf_evidence,
)
from vela_core.walk_forward.query import get_walk_forward_run
from vela_core.walk_forward.report import (
    WalkForwardBenchmarkResult,
    WalkForwardReport,
    WalkForwardWindowResult,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow

CSI = "csi_300_buy_hold"
EQ = "equal_weight_monthly"


def _window(
    ordinal: int, *, csi_alpha: float | None, csi_up: float | None, csi_down: float | None
) -> WalkForwardWindowResult:
    benchmarks = tuple(
        WalkForwardBenchmarkResult(
            key=key,
            name=key,
            total_return=0.1,
            annualized_return=0.1,
            max_drawdown=-0.1,
            volatility=0.1,
            sharpe_ratio=1.0,
            total_return_difference=0.02,
            annualized_return_difference=0.01,
            tracking_error=0.03,
            information_ratio=0.4,
            capm_alpha=csi_alpha if key == CSI else None,
            capm_beta=1.1 if key == CSI else None,
            capm_r_squared=0.8 if key == CSI else None,
            capm_observation_count=240 if key == CSI else None,
            up_capture_ratio=csi_up,
            up_capture_observation_count=9,
            down_capture_ratio=csi_down,
            down_capture_observation_count=4,
        )
        for key in (EQ, CSI)
    )
    return WalkForwardWindowResult(
        window=WalkForwardWindow(
            train_start=date(2020 + ordinal, 1, 1),
            train_end=date(2020 + ordinal, 12, 31),
            test_start=date(2021 + ordinal, 1, 1),
            test_end=date(2021 + ordinal, 12, 31),
        ),
        best_combo={"parameters.selection.top_n": 1},
        oos_version=f"wf-{ordinal:012d}",
        train_sharpe=1.1,
        oos_total_return=0.1,
        oos_annualized_return=0.1,
        oos_sharpe=1.0,
        oos_max_drawdown=-0.1,
        oos_volatility=0.1,
        benchmarks=benchmarks,
        skipped=[],
        oos_backtest_id=ordinal + 1,
        candidate_count=1,
        eligible_count=1,
        skipped_count=0,
        skip_reason_counts={},
    )


def test_wf_regime_report_aggregates_metric_local_values_with_differing_valid_counts() -> None:
    report = WalkForwardReport(
        [
            _window(0, csi_alpha=0.5, csi_up=1.2, csi_down=0.7),
            _window(1, csi_alpha=0.6, csi_up=1.3, csi_down=None),
            _window(2, csi_alpha=0.4, csi_up=0.0, csi_down=0.5),
        ]
    )

    regime = report.benchmark_regime_evidence()

    assert set(regime) == {EQ, CSI}
    csi_alpha = regime[CSI]["capm_alpha"]
    assert csi_alpha["mean"] == pytest.approx(0.5)
    assert csi_alpha["median"] == 0.5
    assert csi_alpha["min"] == 0.4
    assert csi_alpha["max"] == 0.6
    assert csi_alpha["window_count"] == 3
    assert csi_alpha["valid_count"] == 3
    assert csi_alpha["evidence_status"] == "sufficient"
    csi_down = regime[CSI]["down_capture_ratio"]
    assert csi_down["valid_count"] == 2
    assert csi_down["evidence_status"] == "insufficient_evidence"
    assert csi_down["mean"] == pytest.approx(0.6)
    assert csi_down["min"] == 0.5
    csi_up = regime[CSI]["up_capture_ratio"]
    assert csi_up["valid_count"] == 3
    assert csi_up["min"] == 0.0
    assert csi_up["evidence_status"] == "sufficient"
    eq_alpha = regime[EQ]["capm_alpha"]
    assert eq_alpha["valid_count"] == 0
    assert eq_alpha["evidence_status"] == "insufficient_evidence"
    assert eq_alpha["mean"] is None
    assert regime[EQ]["up_capture_ratio"]["valid_count"] == 3


def test_wf_regime_evidence_v2_document_extends_v1_without_verdict() -> None:
    report = WalkForwardReport(
        [
            _window(0, csi_alpha=0.5, csi_up=1.2, csi_down=0.7),
            _window(1, csi_alpha=0.6, csi_up=1.3, csi_down=None),
            _window(2, csi_alpha=0.4, csi_up=0.0, csi_down=0.5),
        ]
    )

    document = report.evidence_document()

    assert isinstance(document, WalkForwardEvidenceV2)
    dumped = document.model_dump(mode="json")
    for key in (EQ, CSI):
        assert set(dumped["benchmarks"][key]) == {
            "total_return_difference",
            "annualized_return_difference",
            "tracking_error",
            "information_ratio",
            "outperformance_rate",
            "capm_alpha",
            "capm_beta",
            "capm_r_squared",
            "up_capture_ratio",
            "down_capture_ratio",
        }
    # Observation counts remain per-window evidence; they are not aggregated.
    assert all("observation_count" not in dumped["benchmarks"][key] for key in (EQ, CSI))
    # No threshold, score, ranking, or verdict is introduced.
    assert "score" not in dumped
    assert "threshold" not in dumped
    assert "verdict" not in dumped
    assert dumped["benchmarks"][CSI]["capm_alpha"]["valid_count"] == 3
    assert dumped["benchmarks"][CSI]["down_capture_ratio"]["valid_count"] == 2
    assert dumped["benchmarks"][EQ]["capm_alpha"]["valid_count"] == 0


def test_wf_regime_terminal_report_shows_per_window_and_aggregate_evidence() -> None:
    report = WalkForwardReport(
        [
            _window(0, csi_alpha=0.5, csi_up=1.2, csi_down=0.7),
            _window(1, csi_alpha=0.6, csi_up=1.3, csi_down=None),
        ]
    )

    text = (
        report.format_report() if hasattr(report, "format_report") else _format_report_text(report)
    )

    assert "    CSI 300 ETF proxy Alpha (252D compounded): 0.500000" in text
    assert "    CSI 300 ETF proxy Beta: 1.100000" in text
    assert "    CSI 300 ETF proxy R-squared: 0.800000" in text
    assert "    CAPM observation count (daily sessions): 240" in text
    assert "    Monthly Up Capture ratio (benchmark up months): 1.200000" in text
    assert "    Up capture selected months: 9" in text
    assert "    Monthly Down Capture ratio (benchmark down months): n/a" in text
    assert "    Down capture selected months: 4" in text
    assert "csi_300_buy_hold benchmark-regime evidence:" in text
    assert "  capm_alpha: mean=0.550000" in text
    assert "  down_capture_ratio: mean=0.700000" in text
    assert "equal_weight_monthly benchmark-regime evidence:" in text
    assert "  capm_alpha: mean=n/a" in text


def _format_report_text(report: WalkForwardReport) -> str:
    from vela_core.walk_forward.report import format_report

    return format_report(report)


def _summary(valid_count: int, window_count: int, *, value: float = 0.1) -> dict[str, object]:
    if valid_count == 0:
        return {
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "window_count": window_count,
            "valid_count": 0,
            "evidence_status": "insufficient_evidence",
        }
    return {
        "mean": value,
        "median": value,
        "min": value,
        "max": value,
        "std": 0.0,
        "window_count": window_count,
        "valid_count": valid_count,
        "evidence_status": "sufficient" if valid_count >= 3 else "insufficient_evidence",
    }


def _rate(window_count: int) -> dict[str, object]:
    return {
        "numerator": window_count,
        "denominator": window_count,
        "value": 1.0,
        "window_count": window_count,
        "valid_count": window_count,
        "evidence_status": "sufficient" if window_count >= 3 else "insufficient_evidence",
    }


def _v2_evidence(window_count: int, *, alpha_valid: int | None = None) -> dict[str, object]:
    alpha_valid = window_count if alpha_valid is None else alpha_valid
    csi_benchmark = {
        "total_return_difference": _summary(window_count, window_count),
        "annualized_return_difference": _summary(window_count, window_count),
        "tracking_error": _summary(window_count, window_count),
        "information_ratio": _summary(window_count, window_count),
        "outperformance_rate": _rate(window_count),
        "capm_alpha": _summary(alpha_valid, window_count, value=0.5),
        "capm_beta": _summary(alpha_valid, window_count, value=1.1),
        "capm_r_squared": _summary(alpha_valid, window_count, value=0.8),
        "up_capture_ratio": _summary(window_count, window_count, value=1.2),
        "down_capture_ratio": _summary(window_count, window_count, value=0.7),
    }
    equal_weight_benchmark = {
        **csi_benchmark,
        "capm_alpha": _summary(0, window_count),
        "capm_beta": _summary(0, window_count),
        "capm_r_squared": _summary(0, window_count),
    }
    return {
        "metrics": {
            name: _summary(window_count, window_count)
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
        "positive_window_rate": _rate(window_count),
        "generalization_gap": _summary(window_count, window_count),
        "benchmarks": {EQ: equal_weight_benchmark, CSI: csi_benchmark},
        "parameter_stability": {},
    }


def _add_parent_with_windows(
    session, *, evidence_version: str, evidence: dict[str, object], regime_on_rows: bool
) -> WalkForwardRun:
    parent = WalkForwardRun(
        strategy_id="demo",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 1),
        window_count=2,
        walk_forward_config_json={"window": {}},
        base_strategy_config_json={"strategy_id": "demo"},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2026-01-02",
            "configured_end_date": "2026-02-01",
            "following_session": None,
            "official_sessions": ["2026-01-02", "2026-01-03", "2026-01-05", "2026-01-06"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version=evidence_version,
        evidence_json=evidence,
        started_at=datetime(2026, 1, 1),
        finished_at=datetime(2026, 1, 2),
    )
    session.add(parent)
    session.flush()
    for ordinal in range(2):
        test_start = date(2026, 1, 2 + ordinal * 3)
        test_end = date(2026, 1, 3 + ordinal * 3)
        oos = BacktestRun(
            strategy_id="demo",
            config_version=f"wf-{ordinal:012d}",
            start_date=test_start,
            end_date=test_end,
            parameters_json='{"benchmark_regime_metric_version":"benchmark_regime_metrics_v1"}',
            started_at=datetime(2026, 1, 1),
            finished_at=datetime(2026, 1, 2),
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
            for trade_date, net_value in (
                (test_start, "1"),
                (test_end, "1.1"),
            )
        )
        for key in (EQ, CSI):
            benchmark = BacktestBenchmark(
                backtest_run_id=oos.id, benchmark_key=key, display_name=key
            )
            if regime_on_rows:
                if key == CSI:
                    benchmark.capm_alpha = Decimal("0.5")
                    benchmark.capm_beta = Decimal("1.1")
                    benchmark.capm_r_squared = Decimal("0.8")
                    benchmark.capm_observation_count = 240
                benchmark.up_capture_ratio = Decimal("1.2")
                benchmark.up_capture_observation_count = 9
                benchmark.down_capture_ratio = Decimal("0.7")
                benchmark.down_capture_observation_count = 4
            session.add(benchmark)
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
    session.commit()
    return parent


def test_wf_v2_evidence_round_trips_and_continues_reading_v1(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'v2.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        v2_parent = _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=_v2_evidence(2, alpha_valid=2),
            regime_on_rows=True,
        )
        v1_parent = _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION,
            evidence=_v1_evidence(),
            regime_on_rows=False,
        )
        v2_id, v1_id = v2_parent.id, v1_parent.id

    with sessionmaker(bind=engine)() as session:
        v2 = get_walk_forward_run(session, run_id=v2_id, strategy_id="demo")
        v1 = get_walk_forward_run(session, run_id=v1_id, strategy_id="demo")
        assert v2 is not None and v2.evidence_version == EVIDENCE_VERSION_V2
        assert isinstance(
            validate_wf_evidence(v2.evidence_version, v2.evidence_json), WalkForwardEvidenceV2
        )
        assert v1 is not None and v1.evidence_version == EVIDENCE_VERSION


def _v1_evidence() -> dict[str, object]:
    benchmark = {
        "total_return_difference": _summary(2, 2),
        "annualized_return_difference": _summary(2, 2),
        "tracking_error": _summary(2, 2),
        "information_ratio": _summary(2, 2),
        "outperformance_rate": _rate(2),
    }
    return {
        "metrics": {
            name: _summary(2, 2)
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
        "positive_window_rate": _rate(2),
        "generalization_gap": _summary(2, 2),
        "benchmarks": {EQ: benchmark, CSI: benchmark},
        "parameter_stability": {},
    }


def test_wf_v2_query_rejects_source_row_valid_count_mismatch(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'mismatch.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        # Document claims only one valid CAPM window but both OOS rows carry values.
        _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=_v2_evidence(2, alpha_valid=1),
            regime_on_rows=True,
        )

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError, match="source OOS rows"):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


def test_wf_v2_query_rejects_source_row_aggregate_value_mismatch(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'aggregate-mismatch.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        evidence = _v2_evidence(2, alpha_valid=2)
        evidence["benchmarks"][CSI]["capm_alpha"].update(
            {"mean": 999.0, "median": 999.0, "min": 999.0, "max": 999.0, "std": 0.0}
        )
        _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=evidence,
            regime_on_rows=True,
        )

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError, match="source OOS rows"):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


def test_wf_v2_query_rejects_invalid_source_observation_count(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'invalid-source-count.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        parent = _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=_v2_evidence(2, alpha_valid=2),
            regime_on_rows=True,
        )
        for benchmark in parent.windows[0].oos_backtest_run.benchmarks:
            if benchmark.benchmark_key == CSI:
                benchmark.up_capture_observation_count = -1
        session.commit()

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError, match="observation count"):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


def test_wf_v2_query_rejects_source_without_regime_metric_version(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'missing-metric-version.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        parent = _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=_v2_evidence(2, alpha_valid=2),
            regime_on_rows=True,
        )
        parent.windows[0].oos_backtest_run.parameters_json = "{}"
        session.commit()

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError, match="metric version"):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


def test_wf_v2_query_rejects_missing_benchmark_key(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'key.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        evidence = _v2_evidence(2, alpha_valid=2)
        del evidence["benchmarks"][CSI]
        _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=evidence,
            regime_on_rows=True,
        )

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


def test_wf_v2_query_rejects_non_finite_value(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'nan.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        evidence = _v2_evidence(2, alpha_valid=2)
        evidence["benchmarks"][CSI]["capm_alpha"]["mean"] = float("nan")
        _add_parent_with_windows(
            session,
            evidence_version=EVIDENCE_VERSION_V2,
            evidence=evidence,
            regime_on_rows=True,
        )

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")


def test_wf_v2_query_rejects_unsupported_version(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'v3.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _add_parent_with_windows(
            session,
            evidence_version="wf_evidence_v4",
            evidence=_v2_evidence(2, alpha_valid=2),
            regime_on_rows=True,
        )

    with sessionmaker(bind=engine)() as session:
        with pytest.raises(PersistedDataContractError, match="unsupported"):
            get_walk_forward_run(session, run_id=1, strategy_id="demo")
