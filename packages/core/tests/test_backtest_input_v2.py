from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest
from vela_core.backtest_input import (
    BACKTEST_INPUT_VERSION,
    build_backtest_input_v2,
    validate_backtest_input_v2,
)
from vela_core.models import ETFInfo, MarketPrice
from vela_core.resolved_session_price import ResolvedSessionPrice


def test_backtest_input_v2_reconciles_raw_and_derived_records() -> None:
    etf = _etf(1, "2020-01-01")
    sessions = [date(2026, 1, 2), date(2026, 1, 3)]
    panel = {
        1: [
            _resolved(1, sessions[0], "100", tradable=True),
            ResolvedSessionPrice(
                etf_id=1,
                trade_date=sessions[1],
                adjusted_value=Decimal("100"),
                raw_close=None,
                raw_factor=None,
                tradable=False,
                resolution="confirmed_non_trading_carry",
                status="full_day_suspension",
                reason="holder_meeting",
                source_uri="https://example.test/source",
                source_published_date=date(2026, 1, 2),
                carry_from_trade_date=sessions[0],
            ),
        ]
    }

    snapshot = build_backtest_input_v2(
        active_etfs=[etf],
        official_sessions=sessions,
        following_session=date(2026, 1, 4),
        price_panel=panel,
    )

    assert snapshot["version"] == BACKTEST_INPUT_VERSION
    assert snapshot["raw_price_counts"] == {"global": 1, "per_etf": {"1": 1}}
    assert snapshot["derived_session_counts"] == {"global": 1, "per_etf": {"1": 1}}
    assert "raw_price_records" in snapshot
    assert "derived_sessions" in snapshot
    validate_backtest_input_v2(snapshot)


def test_backtest_input_v2_checksum_changes_for_temporal_evidence_and_raw_drift() -> None:
    etf = _etf(1, "2020-01-01")
    sessions = [date(2026, 1, 2), date(2026, 1, 3)]
    base = build_backtest_input_v2(
        active_etfs=[etf],
        official_sessions=sessions,
        following_session=None,
        price_panel={1: [_resolved(1, item, "100", tradable=True) for item in sessions]},
    )
    changed_raw = dict(base)
    changed_raw["raw_price_records"] = [
        {**base["raw_price_records"][0], "close_price": "101"},
        base["raw_price_records"][1],
    ]
    changed_raw["data_checksum"] = base["data_checksum"]

    with pytest.raises(ValueError, match="checksum"):
        validate_backtest_input_v2(changed_raw)

    changed_listing = dict(base)
    changed_listing["active_etfs"] = [{**base["active_etfs"][0], "listing_date": "2020-01-02"}]
    changed_listing["data_checksum"] = base["data_checksum"]
    with pytest.raises(ValueError, match="checksum"):
        validate_backtest_input_v2(changed_listing)


def test_legacy_snapshot_shape_is_not_reinterpreted_as_v2() -> None:
    legacy = {"data_checksum": "a" * 64, "per_etf_row_counts": {"1": 2}}

    assert legacy.get("version") != BACKTEST_INPUT_VERSION


def test_backtest_input_v2_excludes_prelisting_and_future_panel_rows() -> None:
    etf = _etf(1, "2026-01-02")
    official = [date(2026, 1, 2)]
    snapshot = build_backtest_input_v2(
        active_etfs=[etf],
        official_sessions=official,
        following_session=None,
        price_panel={
            1: [
                _raw(1, date(2025, 12, 31), "90"),
                _raw(1, date(2026, 1, 2), "100"),
                _raw(1, date(2026, 1, 3), "110"),
            ]
        },
    )

    assert snapshot["raw_price_counts"] == {"global": 1, "per_etf": {"1": 1}}
    assert [row["trade_date"] for row in snapshot["raw_price_records"]] == ["2026-01-02"]


def test_backtest_input_v2_rejects_unreconciled_summary_fields() -> None:
    etf = _etf(1, "2020-01-01")
    sessions = [date(2026, 1, 2), date(2026, 1, 3)]
    snapshot = build_backtest_input_v2(
        active_etfs=[etf],
        official_sessions=sessions,
        following_session=None,
        price_panel={1: [_resolved(1, item, "100", tradable=True) for item in sessions]},
    )

    corrupt = deepcopy(snapshot)
    corrupt["trading_day_count"] = 99

    with pytest.raises(ValueError, match="trading day count"):
        validate_backtest_input_v2(corrupt)


def test_backtest_input_v2_rejects_incomplete_listed_session_panel() -> None:
    etf = _etf(1, "2020-01-01")

    with pytest.raises(ValueError, match="complete source state"):
        build_backtest_input_v2(
            active_etfs=[etf],
            official_sessions=[date(2026, 1, 2), date(2026, 1, 3)],
            following_session=None,
            price_panel={1: [_resolved(1, date(2026, 1, 2), "100", tradable=True)]},
        )


def test_backtest_input_v2_rejects_carried_value_that_differs_from_its_ancestor() -> None:
    etf = _etf(1, "2020-01-01")
    sessions = [date(2026, 1, 2), date(2026, 1, 3)]
    carried = ResolvedSessionPrice(
        etf_id=1,
        trade_date=sessions[1],
        adjusted_value=Decimal("999"),
        raw_close=None,
        raw_factor=None,
        tradable=False,
        resolution="confirmed_non_trading_carry",
        status="full_day_suspension",
        reason="holder_meeting",
        source_uri="https://example.test/source",
        source_published_date=sessions[0],
        carry_from_trade_date=sessions[0],
    )

    with pytest.raises(ValueError, match="carried adjusted value"):
        build_backtest_input_v2(
            active_etfs=[etf],
            official_sessions=sessions,
            following_session=None,
            price_panel={1: [_resolved(1, sessions[0], "100", tradable=True), carried]},
        )


def _etf(identifier: int, listing_date: str) -> ETFInfo:
    return ETFInfo(
        id=identifier,
        exchange="SSE",
        symbol="510300",
        name="510300",
        listing_date=date.fromisoformat(listing_date),
        is_active=True,
    )


def _resolved(etf_id: int, trade_date: date, value: str, *, tradable: bool) -> ResolvedSessionPrice:
    return ResolvedSessionPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        adjusted_value=Decimal(value),
        raw_close=Decimal(value) if tradable else None,
        raw_factor=Decimal("1") if tradable else None,
        tradable=tradable,
        resolution="market_price" if tradable else "confirmed_non_trading_carry",
    )


def _raw(etf_id: int, trade_date: date, close: str) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        close_price=Decimal(close),
        factor_hfq=Decimal("1"),
    )
