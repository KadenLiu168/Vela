import json
from datetime import date
from decimal import Decimal

from vela_core import (
    DuplicateTradeDateWarning,
    build_quality_warnings_json,
    detect_duplicate_trade_dates,
)
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
