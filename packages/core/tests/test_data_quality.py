import json
from datetime import date
from decimal import Decimal

from vela_core import (
    DuplicateTradeDateWarning,
    build_quality_warnings_json,
    build_quality_warnings_json_from_sections,
    detect_duplicate_trade_dates,
    detect_etf_trading_day_gaps,
    detect_systematic_trading_day_gaps,
)
from vela_core.data_quality import EtfTradingDayGap, SystematicTradingDayGap
from vela_core.models import MarketPrice


def _price(*, etf_id: int, trade_date: date) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        volume=1000,
    )


def test_detect_duplicate_trade_dates_returns_empty_when_no_duplicates() -> None:
    prices = [
        _price(etf_id=1, trade_date=date(2026, 7, 1)),
        _price(etf_id=1, trade_date=date(2026, 7, 2)),
        _price(etf_id=2, trade_date=date(2026, 7, 1)),
    ]

    assert detect_duplicate_trade_dates(prices) == []


def test_detect_duplicate_trade_dates_returns_warnings_with_counts() -> None:
    prices = [
        _price(etf_id=1, trade_date=date(2026, 7, 1)),
        _price(etf_id=1, trade_date=date(2026, 7, 1)),
        _price(etf_id=1, trade_date=date(2026, 7, 1)),
        _price(etf_id=2, trade_date=date(2026, 7, 1)),
        _price(etf_id=2, trade_date=date(2026, 7, 1)),
    ]

    assert detect_duplicate_trade_dates(prices) == [
        DuplicateTradeDateWarning(etf_id=1, trade_date=date(2026, 7, 1), count=3),
        DuplicateTradeDateWarning(etf_id=2, trade_date=date(2026, 7, 1), count=2),
    ]


def test_detect_duplicate_trade_dates_returns_sorted_output() -> None:
    prices = [
        _price(etf_id=2, trade_date=date(2026, 7, 2)),
        _price(etf_id=2, trade_date=date(2026, 7, 2)),
        _price(etf_id=1, trade_date=date(2026, 7, 3)),
        _price(etf_id=1, trade_date=date(2026, 7, 3)),
    ]

    warnings = detect_duplicate_trade_dates(prices)

    assert [(warning.etf_id, warning.trade_date) for warning in warnings] == [
        (1, date(2026, 7, 3)),
        (2, date(2026, 7, 2)),
    ]


def test_detect_duplicate_trade_dates_does_not_mutate_input() -> None:
    prices = [
        _price(etf_id=1, trade_date=date(2026, 7, 1)),
        _price(etf_id=1, trade_date=date(2026, 7, 1)),
    ]

    detect_duplicate_trade_dates(prices)

    assert len(prices) == 2


def test_build_quality_warnings_json_returns_none_for_empty() -> None:
    assert build_quality_warnings_json([]) is None


def test_build_quality_warnings_json_returns_expected_shape() -> None:
    warnings = [
        DuplicateTradeDateWarning(etf_id=1, trade_date=date(2026, 7, 1), count=2),
        DuplicateTradeDateWarning(etf_id=3, trade_date=date(2026, 7, 5), count=4),
    ]

    result = build_quality_warnings_json(warnings)

    assert result is not None
    assert json.loads(result) == {
        "duplicate_trade_dates": [
            {"etf_id": 1, "trade_date": "2026-07-01", "count": 2},
            {"etf_id": 3, "trade_date": "2026-07-05", "count": 4},
        ]
    }


def test_detect_systematic_gaps_flags_missing_calendar_days() -> None:
    actual = [date(2026, 7, 1), date(2026, 7, 3)]
    expected = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]

    assert detect_systematic_trading_day_gaps(actual, expected) == [
        SystematicTradingDayGap(trade_date=date(2026, 7, 2)),
    ]


def test_detect_systematic_gaps_returns_empty_when_union_matches_calendar() -> None:
    dates = [date(2026, 7, 1), date(2026, 7, 2)]

    assert detect_systematic_trading_day_gaps(dates, dates) == []


def test_detect_systematic_gaps_ignores_extra_stored_dates() -> None:
    actual = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 4)]
    expected = [date(2026, 7, 1), date(2026, 7, 2)]

    assert detect_systematic_trading_day_gaps(actual, expected) == []


def test_detect_systematic_gaps_returns_sorted_output() -> None:
    actual = [date(2026, 7, 3)]
    expected = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]

    gaps = detect_systematic_trading_day_gaps(actual, expected)

    assert [gap.trade_date for gap in gaps] == [date(2026, 7, 1), date(2026, 7, 2)]


def test_detect_etf_gaps_flags_missing_day_after_inception() -> None:
    etf_actual = {1: [date(2026, 7, 1), date(2026, 7, 3)]}
    expected = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]
    inception = {1: date(2026, 7, 1)}

    assert detect_etf_trading_day_gaps(etf_actual, expected, inception) == [
        EtfTradingDayGap(etf_id=1, trade_date=date(2026, 7, 2)),
    ]


def test_detect_etf_gaps_suppresses_before_inception_boundary() -> None:
    etf_actual = {1: [date(2026, 7, 3)]}
    expected = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]
    inception = {1: date(2026, 7, 3)}

    assert detect_etf_trading_day_gaps(etf_actual, expected, inception) == []


def test_detect_etf_gaps_returns_empty_when_covered() -> None:
    etf_actual = {1: [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]}
    expected = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]
    inception = {1: date(2026, 7, 1)}

    assert detect_etf_trading_day_gaps(etf_actual, expected, inception) == []


def test_detect_etf_gaps_returns_sorted_output_across_etfs() -> None:
    etf_actual = {
        2: [date(2026, 7, 1), date(2026, 7, 3)],
        1: [date(2026, 7, 1), date(2026, 7, 3)],
    }
    expected = [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]
    inception = {1: date(2026, 7, 1), 2: date(2026, 7, 1)}

    gaps = detect_etf_trading_day_gaps(etf_actual, expected, inception)

    assert [(gap.etf_id, gap.trade_date) for gap in gaps] == [
        (1, date(2026, 7, 2)),
        (2, date(2026, 7, 2)),
    ]


def test_detect_etf_gaps_skips_etf_with_no_stored_rows() -> None:
    etf_actual = {1: [date(2026, 7, 1), date(2026, 7, 2)]}
    expected = [date(2026, 7, 1), date(2026, 7, 2)]
    inception = {1: date(2026, 7, 1), 2: date(2026, 7, 1)}

    assert detect_etf_trading_day_gaps(etf_actual, expected, inception) == []


def test_build_sections_json_merges_all_sections() -> None:
    duplicates = [DuplicateTradeDateWarning(etf_id=1, trade_date=date(2026, 7, 1), count=2)]
    systematic = [SystematicTradingDayGap(trade_date=date(2026, 7, 2))]
    etf_gaps = [EtfTradingDayGap(etf_id=3, trade_date=date(2026, 7, 3))]

    result = build_quality_warnings_json_from_sections(duplicates, systematic, etf_gaps)

    assert result is not None
    assert json.loads(result) == {
        "duplicate_trade_dates": [{"etf_id": 1, "trade_date": "2026-07-01", "count": 2}],
        "systematic_trading_day_gaps": [{"trade_date": "2026-07-02"}],
        "etf_trading_day_gaps": [{"etf_id": 3, "trade_date": "2026-07-03"}],
    }


def test_build_sections_json_returns_none_when_all_empty() -> None:
    assert build_quality_warnings_json_from_sections([], [], []) is None


def test_build_sections_json_duplicate_only_matches_phase1_shape() -> None:
    duplicates = [DuplicateTradeDateWarning(etf_id=1, trade_date=date(2026, 7, 1), count=2)]

    assert build_quality_warnings_json_from_sections(
        duplicates, [], []
    ) == build_quality_warnings_json(duplicates)


def test_build_sections_json_gap_only_omits_empty_duplicate_section() -> None:
    systematic = [SystematicTradingDayGap(trade_date=date(2026, 7, 2))]

    result = build_quality_warnings_json_from_sections([], systematic, [])

    assert result is not None
    assert json.loads(result) == {"systematic_trading_day_gaps": [{"trade_date": "2026-07-02"}]}
