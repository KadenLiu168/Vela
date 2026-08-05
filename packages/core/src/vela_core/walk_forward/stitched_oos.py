from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from vela_core.walk_forward.evidence import PersistedDataContractError

_SIX_PLACES = Decimal("0.000001")
StitchedOosStatus = Literal["available", "unavailable_non_contiguous_windows"]


@dataclass(frozen=True)
class StitchedOosSourcePoint:
    trade_date: date
    net_value: Decimal


@dataclass(frozen=True)
class StitchedOosWindow:
    ordinal: int
    test_start: date
    test_end: date
    points: tuple[StitchedOosSourcePoint, ...]


@dataclass(frozen=True)
class StitchedOosPoint:
    trade_date: date
    net_value: Decimal
    window_ordinal: int
    is_window_start: bool


@dataclass(frozen=True)
class StitchedOosResult:
    status: StitchedOosStatus
    initial_net_value: Decimal | None
    ending_net_value: Decimal | None
    total_return: Decimal | None
    points: tuple[StitchedOosPoint, ...]


def derive_stitched_oos(
    *, windows: Sequence[StitchedOosWindow], official_sessions: Sequence[date]
) -> StitchedOosResult:
    session_indexes = {trade_date: index for index, trade_date in enumerate(official_sessions)}
    _validate_window_bounds(windows, session_indexes)
    if not _windows_are_contiguous(windows, session_indexes):
        return StitchedOosResult(
            status="unavailable_non_contiguous_windows",
            initial_net_value=None,
            ending_net_value=None,
            total_return=None,
            points=(),
        )

    capital = Decimal("1")
    points: list[StitchedOosPoint] = []
    for window in windows:
        _validate_curve(window)
        local_start = window.points[0].net_value
        for index, source in enumerate(window.points):
            scaled_value = capital * source.net_value / local_start
            points.append(
                StitchedOosPoint(
                    trade_date=source.trade_date,
                    net_value=scaled_value.quantize(_SIX_PLACES),
                    window_ordinal=window.ordinal,
                    is_window_start=index == 0,
                )
            )
        capital = capital * window.points[-1].net_value / local_start

    return StitchedOosResult(
        status="available",
        initial_net_value=Decimal("1.000000"),
        ending_net_value=capital.quantize(_SIX_PLACES),
        total_return=(capital - Decimal("1")).quantize(_SIX_PLACES),
        points=tuple(points),
    )


def _validate_window_bounds(
    windows: Sequence[StitchedOosWindow], session_indexes: dict[date, int]
) -> None:
    for window in windows:
        if window.test_start not in session_indexes or window.test_end not in session_indexes:
            raise PersistedDataContractError(
                "Walk-forward test bounds are missing official sessions"
            )
        if session_indexes[window.test_start] > session_indexes[window.test_end]:
            raise PersistedDataContractError("Walk-forward test bounds are not chronological")


def _windows_are_contiguous(
    windows: Sequence[StitchedOosWindow], session_indexes: dict[date, int]
) -> bool:
    return all(
        session_indexes[current.test_start] == session_indexes[previous.test_end] + 1
        for previous, current in zip(windows, windows[1:], strict=False)
    )


def _validate_curve(window: StitchedOosWindow) -> None:
    if not window.points:
        raise PersistedDataContractError("stitched OOS source curve is empty")
    if (
        window.points[0].trade_date != window.test_start
        or window.points[-1].trade_date != window.test_end
    ):
        raise PersistedDataContractError("stitched OOS source curve does not match test bounds")
    previous_date: date | None = None
    for point in window.points:
        if point.net_value <= 0:
            raise PersistedDataContractError(
                "stitched OOS source curve net values must be positive"
            )
        if previous_date is not None and point.trade_date <= previous_date:
            raise PersistedDataContractError(
                "stitched OOS source curve dates must be strictly increasing"
            )
        previous_date = point.trade_date
