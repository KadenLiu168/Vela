# ruff: noqa: E501

from datetime import date
from decimal import Decimal

import pytest
from vela_core.walk_forward.evidence import PersistedDataContractError
from vela_core.walk_forward.stitched_oos import (
    StitchedOosSourcePoint,
    StitchedOosWindow,
    derive_stitched_oos,
)


def _window(
    ordinal: int,
    start: date,
    end: date,
    values: list[tuple[date, str]],
) -> StitchedOosWindow:
    return StitchedOosWindow(
        ordinal=ordinal,
        test_start=start,
        test_end=end,
        points=tuple(
            StitchedOosSourcePoint(trade_date=trade_date, net_value=Decimal(net_value))
            for trade_date, net_value in values
        ),
    )


def test_stitched_oos_compounds_segments_and_retains_reset_points() -> None:
    result = derive_stitched_oos(
        windows=(
            _window(
                0,
                date(2026, 1, 2),
                date(2026, 1, 5),
                [(date(2026, 1, 2), "1"), (date(2026, 1, 5), "1.1")],
            ),
            _window(
                1,
                date(2026, 1, 6),
                date(2026, 1, 7),
                [(date(2026, 1, 6), "1"), (date(2026, 1, 7), "0.9")],
            ),
        ),
        official_sessions=(
            date(2026, 1, 2),
            date(2026, 1, 5),
            date(2026, 1, 6),
            date(2026, 1, 7),
        ),
    )

    assert result.status == "available"
    assert result.initial_net_value == Decimal("1.000000")
    assert result.ending_net_value == Decimal("0.990000")
    assert result.total_return == Decimal("-0.010000")
    assert [
        (point.trade_date, point.net_value, point.window_ordinal, point.is_window_start)
        for point in result.points
    ] == [
        (date(2026, 1, 2), Decimal("1.000000"), 0, True),
        (date(2026, 1, 5), Decimal("1.100000"), 0, False),
        (date(2026, 1, 6), Decimal("1.100000"), 1, True),
        (date(2026, 1, 7), Decimal("0.990000"), 1, False),
    ]


def test_stitched_oos_defers_rounding_until_after_all_segments() -> None:
    result = derive_stitched_oos(
        windows=(
            _window(
                0,
                date(2026, 1, 2),
                date(2026, 1, 3),
                [(date(2026, 1, 2), "1"), (date(2026, 1, 3), "1.0000004")],
            ),
            _window(
                1,
                date(2026, 1, 4),
                date(2026, 1, 5),
                [(date(2026, 1, 4), "1"), (date(2026, 1, 5), "1.0000004")],
            ),
            _window(
                2,
                date(2026, 1, 6),
                date(2026, 1, 7),
                [(date(2026, 1, 6), "1"), (date(2026, 1, 7), "1.0000004")],
            ),
        ),
        official_sessions=tuple(date(2026, 1, day) for day in range(2, 8)),
    )

    assert result.ending_net_value == Decimal("1.000001")
    assert result.total_return == Decimal("0.000001")
    assert all(point.net_value.as_tuple().exponent == -6 for point in result.points)


@pytest.mark.parametrize(
    ("windows", "official_sessions", "message"),
    [
        (
            (_window(0, date(2026, 1, 2), date(2026, 1, 2), []),),
            (date(2026, 1, 2),),
            "empty",
        ),
        (
            (_window(0, date(2026, 1, 2), date(2026, 1, 2), [(date(2026, 1, 2), "0")]),),
            (date(2026, 1, 2),),
            "positive",
        ),
        (
            (
                _window(
                    0,
                    date(2026, 1, 2),
                    date(2026, 1, 3),
                    [(date(2026, 1, 2), "1"), (date(2026, 1, 2), "1.1"), (date(2026, 1, 3), "1.2")],
                ),
            ),
            (date(2026, 1, 2), date(2026, 1, 3)),
            "increasing",
        ),
        (
            (
                _window(
                    0,
                    date(2026, 1, 2),
                    date(2026, 1, 3),
                    [(date(2026, 1, 2), "1"), (date(2026, 1, 4), "1.1")],
                ),
            ),
            (date(2026, 1, 2), date(2026, 1, 3)),
            "bounds",
        ),
        (
            (_window(0, date(2026, 1, 2), date(2026, 1, 2), [(date(2026, 1, 2), "1")]),),
            (date(2026, 1, 3),),
            "official",
        ),
    ],
)
def test_stitched_oos_rejects_corrupt_eligible_evidence(
    windows: tuple[StitchedOosWindow, ...], official_sessions: tuple[date, ...], message: str
) -> None:
    with pytest.raises(PersistedDataContractError, match=message):
        derive_stitched_oos(windows=windows, official_sessions=official_sessions)


@pytest.mark.parametrize(
    "windows",
    [
        (
            _window(0, date(2026, 1, 2), date(2026, 1, 2), [(date(2026, 1, 2), "1")]),
            _window(1, date(2026, 1, 6), date(2026, 1, 6), [(date(2026, 1, 6), "1")]),
        ),
        (
            _window(
                0,
                date(2026, 1, 2),
                date(2026, 1, 3),
                [(date(2026, 1, 2), "1"), (date(2026, 1, 3), "1")],
            ),
            _window(
                1,
                date(2026, 1, 3),
                date(2026, 1, 6),
                [(date(2026, 1, 3), "1"), (date(2026, 1, 6), "1")],
            ),
        ),
    ],
)
def test_stitched_oos_returns_typed_unavailability_for_valid_gap_or_overlap(
    windows: tuple[StitchedOosWindow, ...],
) -> None:
    result = derive_stitched_oos(
        windows=windows,
        official_sessions=(date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 5), date(2026, 1, 6)),
    )

    assert result.status == "unavailable_non_contiguous_windows"
    assert result.initial_net_value is None
    assert result.ending_net_value is None
    assert result.total_return is None
    assert result.points == ()
