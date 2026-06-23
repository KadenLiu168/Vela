from datetime import date

from vela_core import generate_weekly_rebalance_dates


def test_generates_last_available_trading_date_per_iso_week() -> None:
    trading_dates = [
        date(2026, 1, 5),
        date(2026, 1, 6),
        date(2026, 1, 7),
        date(2026, 1, 8),
        date(2026, 1, 9),
        date(2026, 1, 12),
        date(2026, 1, 13),
        date(2026, 1, 14),
        date(2026, 1, 15),
        date(2026, 1, 16),
    ]

    assert generate_weekly_rebalance_dates(trading_dates) == [
        date(2026, 1, 9),
        date(2026, 1, 16),
    ]


def test_uses_last_available_input_date_when_week_has_missing_trading_days() -> None:
    trading_dates = [
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 2, 19),
    ]

    assert generate_weekly_rebalance_dates(trading_dates) == [date(2026, 2, 19)]


def test_sorts_and_deduplicates_trading_dates() -> None:
    trading_dates = [
        date(2026, 1, 16),
        date(2026, 1, 9),
        date(2026, 1, 5),
        date(2026, 1, 9),
        date(2026, 1, 12),
    ]

    assert generate_weekly_rebalance_dates(trading_dates) == [
        date(2026, 1, 9),
        date(2026, 1, 16),
    ]


def test_groups_dates_by_iso_week_across_calendar_year_boundary() -> None:
    trading_dates = [
        date(2025, 12, 29),
        date(2025, 12, 31),
        date(2026, 1, 2),
        date(2026, 1, 5),
    ]

    assert generate_weekly_rebalance_dates(trading_dates) == [
        date(2026, 1, 2),
        date(2026, 1, 5),
    ]


def test_returns_empty_list_for_empty_trading_dates() -> None:
    assert generate_weekly_rebalance_dates([]) == []
