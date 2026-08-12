from datetime import date
from decimal import Decimal

import pytest
from vela_core.data_quality import detect_etf_trading_day_gaps
from vela_core.models import ETFInfo, ETFSessionStatus, MarketPrice
from vela_core.resolved_session_price import (
    ResolvedSessionInputError,
    resolve_session_prices,
)


def test_resolver_uses_decimal_raw_close_and_factor() -> None:
    etf = _etf(1, listing_date=date(2024, 1, 2))
    raw = _price(1, date(2024, 1, 2), close="1.234567", factor="1.234567890123")

    resolved = resolve_session_prices(
        official_sessions=[date(2024, 1, 2)],
        active_etfs=[etf],
        raw_prices={1: [raw]},
        session_statuses={},
    )

    point = resolved[1][0]
    assert point.adjusted_value == Decimal("1.234567") * Decimal("1.234567890123")
    assert point.raw_close == Decimal("1.234567")
    assert point.raw_factor == Decimal("1.234567890123")
    assert point.tradable is True
    assert point.resolution == "market_price"
    assert point.status is None


def test_resolver_carries_single_and_consecutive_confirmed_statuses() -> None:
    etf = _etf(1, listing_date=date(2024, 1, 2))
    sessions = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    raw = _price(1, sessions[0], close="7.25", factor="2")
    statuses = {
        1: [
            _status(1, sessions[1], reason="holder_meeting"),
            _status(1, sessions[2], reason="holder_meeting_continued"),
        ]
    }

    resolved = resolve_session_prices(
        official_sessions=sessions,
        active_etfs=[etf],
        raw_prices={1: [raw]},
        session_statuses=statuses,
    )

    assert [point.adjusted_value for point in resolved[1]] == [
        Decimal("14.50"),
        Decimal("14.50"),
        Decimal("14.50"),
    ]
    assert [point.tradable for point in resolved[1]] == [True, False, False]
    assert [point.resolution for point in resolved[1]] == [
        "market_price",
        "confirmed_non_trading_carry",
        "confirmed_non_trading_carry",
    ]
    assert resolved[1][2].carry_from_trade_date == sessions[1]
    assert resolved[1][1].reason == "holder_meeting"


def test_resolver_excludes_pre_listing_sessions() -> None:
    etf = _etf(1, listing_date=date(2024, 1, 3))
    raw_prices = {
        1: [
            _price(1, date(2024, 1, 2), close="2", factor="1"),
            _price(1, date(2024, 1, 3), close="3", factor="1"),
        ]
    }

    resolved = resolve_session_prices(
        official_sessions=[date(2024, 1, 2), date(2024, 1, 3)],
        active_etfs=[etf],
        raw_prices=raw_prices,
        session_statuses={},
    )

    assert [point.trade_date for point in resolved[1]] == [date(2024, 1, 3)]


def test_resolver_rejects_unknown_gap_conflict_and_missing_anchor() -> None:
    etf = _etf(1, listing_date=date(2024, 1, 2))
    sessions = [date(2024, 1, 2), date(2024, 1, 3)]

    with pytest.raises(ResolvedSessionInputError) as gap_info:
        resolve_session_prices(
            official_sessions=sessions,
            active_etfs=[etf],
            raw_prices={1: [_price(1, sessions[0], close="1", factor="1")]},
            session_statuses={},
        )
    assert gap_info.value.category_counts == {"unexplained_gap": 1}
    assert "SSE:510300 on 2024-01-03" in str(gap_info.value)

    with pytest.raises(ResolvedSessionInputError) as conflict_info:
        resolve_session_prices(
            official_sessions=[sessions[0]],
            active_etfs=[etf],
            raw_prices={1: [_price(1, sessions[0], close="1", factor="1")]},
            session_statuses={1: [_status(1, sessions[0])]},
        )
    assert conflict_info.value.category_counts == {"raw_status_conflict": 1}

    with pytest.raises(ResolvedSessionInputError) as anchor_info:
        resolve_session_prices(
            official_sessions=[sessions[0]],
            active_etfs=[etf],
            raw_prices={},
            session_statuses={1: [_status(1, sessions[0])]},
        )
    assert anchor_info.value.category_counts == {"missing_carry_anchor": 1}


def test_resolver_reports_all_categories_with_deterministic_bounded_sample() -> None:
    missing_listing = _etf(2, listing_date=None)
    gap_etf = _etf(1, listing_date=date(2024, 1, 2))

    with pytest.raises(ResolvedSessionInputError) as info:
        resolve_session_prices(
            official_sessions=[date(2024, 1, 2), date(2024, 1, 3)],
            active_etfs=[missing_listing, gap_etf],
            raw_prices={1: []},
            session_statuses={},
            sample_limit=1,
        )

    assert info.value.category_counts == {
        "missing_listing_metadata": 1,
        "unexplained_gap": 2,
    }
    assert info.value.samples == (
        "missing_listing_metadata: ETF 2 SSE:512000 listing_date=missing",
    )
    assert "unexplained_gap=2" in str(info.value)


def test_first_stored_diagnostic_boundary_cannot_authorize_execution() -> None:
    sessions = [date(2024, 1, 2), date(2024, 1, 3)]
    etf = _etf(1, listing_date=sessions[0])
    raw_prices = [_price(1, sessions[1], close="1", factor="1")]

    assert (
        detect_etf_trading_day_gaps(
            {1: [sessions[1]]},
            sessions,
            {1: sessions[1]},
        )
        == []
    )

    with pytest.raises(ResolvedSessionInputError, match="unexplained_gap=1"):
        resolve_session_prices(
            official_sessions=sessions,
            active_etfs=[etf],
            raw_prices=raw_prices,
            session_statuses={},
        )


@pytest.mark.parametrize(
    ("before", "after", "ratio"),
    [
        ("5", "1", "5"),
        ("2", "1", "2"),
        ("0.982", "2.686363014635480782382710983", "0.36555"),
    ],
)
def test_split_merge_factor_change_keeps_resolved_value_continuous(
    before: str,
    after: str,
    ratio: str,
) -> None:
    etf = _etf(1, listing_date=date(2024, 1, 2))
    sessions = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]

    resolved = resolve_session_prices(
        official_sessions=sessions,
        active_etfs=[etf],
        raw_prices={
            1: [
                _price(1, sessions[0], close=before, factor="1"),
                _price(1, sessions[2], close=after, factor=ratio),
            ]
        },
        session_statuses={1: [_status(1, sessions[1], reason="share_split_merge")]},
    )

    assert resolved[1][1].tradable is False
    assert resolved[1][1].adjusted_value == resolved[1][0].adjusted_value
    assert resolved[1][2].adjusted_value == pytest.approx(
        resolved[1][0].adjusted_value,
        rel=Decimal("0.0001"),
    )


def _etf(etf_id: int, *, listing_date: date | None) -> ETFInfo:
    return ETFInfo(
        id=etf_id,
        exchange="SSE",
        symbol="510300" if etf_id == 1 else "512000",
        name="Test ETF",
        currency="CNY",
        listing_date=listing_date,
        is_active=True,
    )


def _price(etf_id: int, trade_date: date, *, close: str, factor: str) -> MarketPrice:
    value = Decimal(close)
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=value,
        high_price=value,
        low_price=value,
        close_price=value,
        factor_hfq=Decimal(factor),
    )


def _status(etf_id: int, trade_date: date, *, reason: str = "holder_meeting") -> ETFSessionStatus:
    return ETFSessionStatus(
        etf_id=etf_id,
        trade_date=trade_date,
        status="full_day_suspension",
        reason=reason,
        source_uri="https://example.test/announcement",
        source_published_date=trade_date,
    )
