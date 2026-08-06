# ruff: noqa: E501

from datetime import date, timedelta
from decimal import Decimal

import pytest
from vela_core.return_stability import (
    CalendarReturnBucket,
    ReturnStabilitySourcePoint,
    derive_return_stability,
)
from vela_core.walk_forward.evidence import PersistedDataContractError

_SIX = Decimal("0.000001")
_DAYS = 252


def _point(
    day: int, net_value: str, *, year: int = 2026, month: int = 1
) -> ReturnStabilitySourcePoint:
    return ReturnStabilitySourcePoint(
        trade_date=date(year, month, day),
        net_value=Decimal(net_value),
    )


def _points(values: list[tuple[int, str]]) -> tuple[ReturnStabilitySourcePoint, ...]:
    return tuple(_point(day, net_value) for day, net_value in values)


def _daily_business_points(
    count: int, *, start: date = date(2026, 1, 1)
) -> tuple[ReturnStabilitySourcePoint, ...]:
    """Generate `count` consecutive calendar-day points (dates need not be sessions)."""
    return tuple(
        ReturnStabilitySourcePoint(
            trade_date=start + timedelta(days=index),
            net_value=Decimal("1.000000") + Decimal(index) / Decimal(100),
        )
        for index in range(count)
    )


def _oracle_window(
    points: tuple[ReturnStabilitySourcePoint, ...],
    *,
    start_index: int,
    end_index: int,
    risk_free_rate: Decimal | None,
) -> tuple[Decimal, Decimal, Decimal | None]:
    """Independent oracle: reconstructs returns from adjacent net values and applies
    the population-variance, float square-root, six-place conventions."""
    returns = [
        points[index].net_value / points[index - 1].net_value - Decimal("1")
        for index in range(start_index + 1, end_index + 1)
    ]
    total_return = (
        points[end_index].net_value / points[start_index].net_value - Decimal("1")
    ).quantize(_SIX)
    mean = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum(
        (daily_return - mean) * (daily_return - mean) for daily_return in returns
    ) / Decimal(len(returns))
    volatility = Decimal(str((float(variance) ** 0.5) * (_DAYS**0.5))).quantize(_SIX)

    sharpe: Decimal | None = None
    if risk_free_rate is not None:
        daily_risk_free_rate = risk_free_rate / Decimal(_DAYS)
        excess = [daily_return - daily_risk_free_rate for daily_return in returns]
        if not all(value == excess[0] for value in excess):
            mean_excess = sum(excess, Decimal("0")) / Decimal(len(excess))
            excess_variance = sum(
                (value - mean_excess) * (value - mean_excess) for value in excess
            ) / Decimal(len(excess))
            sharpe = Decimal(
                str(float(mean_excess) / (float(excess_variance) ** 0.5) * (_DAYS**0.5))
            ).quantize(_SIX)
    return total_return, volatility, sharpe


# --- 1.2 persisted net-value reconstruction -----------------------------------


def test_reconstructed_returns_match_adjacent_persisted_net_values() -> None:
    result = derive_return_stability(
        points=_points([(1, "1"), (2, "1.1"), (3, "1.21"), (4, "1.331")]),
        requested_start_date=date(2026, 1, 1),
        requested_end_date=date(2026, 1, 31),
        risk_free_rate=Decimal("0.02"),
    )

    assert result.source_point_count == 4
    assert result.effective_return_count == 3
    # 2026-01 has 3 reconstructed returns: 0.1, 0.1, 0.1 -> compound 0.331
    assert result.monthly == (
        CalendarReturnBucket(
            period="2026-01",
            first_date=date(2026, 1, 2),
            last_date=date(2026, 1, 4),
            observation_count=3,
            total_return=Decimal("0.331000"),
            is_partial=False,
        ),
    )


def test_unquantized_decimal_intermediates_are_used() -> None:
    # 1.0000004 / 1.000000 - 1 is 0.0000004, far below the six-place output
    # threshold; a premature quantize would truncate it to 0.000000 and the
    # compound would be wrong.
    points = _points([(1, "1.000000"), (2, "1.0000004"), (3, "1.0000008")])
    result = derive_return_stability(
        points=points,
        requested_start_date=date(2026, 1, 1),
        requested_end_date=date(2026, 1, 31),
        risk_free_rate=Decimal("0.02"),
    )
    assert result.monthly[0].total_return == Decimal("0.000001")
    assert result.monthly[0].observation_count == 2


def test_rejects_duplicate_dates() -> None:
    points = _points([(1, "1"), (2, "1.1"), (2, "1.21")])
    with pytest.raises(PersistedDataContractError):
        derive_return_stability(
            points=points,
            requested_start_date=date(2026, 1, 1),
            requested_end_date=date(2026, 1, 31),
            risk_free_rate=Decimal("0.02"),
        )


def test_rejects_non_increasing_dates() -> None:
    points = _points([(3, "1"), (2, "1.1"), (4, "1.21")])
    with pytest.raises(PersistedDataContractError):
        derive_return_stability(
            points=points,
            requested_start_date=date(2026, 1, 1),
            requested_end_date=date(2026, 1, 31),
            risk_free_rate=Decimal("0.02"),
        )


def test_rejects_non_positive_net_value() -> None:
    points = _points([(1, "1"), (2, "0"), (3, "1.1")])
    with pytest.raises(PersistedDataContractError):
        derive_return_stability(
            points=points,
            requested_start_date=date(2026, 1, 1),
            requested_end_date=date(2026, 1, 31),
            risk_free_rate=Decimal("0.02"),
        )


# --- 1.3 independent-oracle rolling tests --------------------------------------


def test_first_rolling_point_uses_64_source_values() -> None:
    points = _daily_business_points(64)
    result = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )

    assert result.rolling_status == "available"
    assert result.sharpe_status == "available"
    assert len(result.rolling) == 1
    expected_total, expected_volatility, expected_sharpe = _oracle_window(
        points,
        start_index=0,
        end_index=63,
        risk_free_rate=Decimal("0.02"),
    )
    point = result.rolling[0]
    assert point.window_start_date == points[0].trade_date
    assert point.trade_date == points[63].trade_date
    assert point.total_return == expected_total
    assert point.volatility == expected_volatility
    assert point.sharpe_ratio == expected_sharpe
    assert all(
        value.as_tuple().exponent == -6
        for value in (point.total_return, point.volatility)
        if value is not None
    )


def test_subsequent_rolling_points_advance_the_window() -> None:
    points = _daily_business_points(66)
    result = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )

    assert len(result.rolling) == 3
    for point, end_index in zip(result.rolling, (63, 64, 65), strict=False):
        expected_total, expected_volatility, expected_sharpe = _oracle_window(
            points,
            start_index=end_index - 63,
            end_index=end_index,
            risk_free_rate=Decimal("0.02"),
        )
        assert point.window_start_date == points[end_index - 63].trade_date
        assert point.trade_date == points[end_index].trade_date
        assert point.total_return == expected_total
        assert point.volatility == expected_volatility
        assert point.sharpe_ratio == expected_sharpe


def test_rolling_matches_oracle_without_risk_free_rate() -> None:
    points = _daily_business_points(65)
    result = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=None,
    )

    assert result.rolling_status == "available"
    assert result.sharpe_status == "unavailable_missing_risk_free_rate"
    assert len(result.rolling) == 2
    for point, end_index in zip(result.rolling, (63, 64), strict=False):
        expected_total, expected_volatility, _ = _oracle_window(
            points,
            start_index=end_index - 63,
            end_index=end_index,
            risk_free_rate=None,
        )
        assert point.total_return == expected_total
        assert point.volatility == expected_volatility
        assert point.sharpe_ratio is None


def test_rolling_total_return_is_product_of_reconstructed_returns() -> None:
    # Values grow by a constant 1% per point; the first 63 returns compound to
    # 1.01**63 - 1 exactly, not an expanding-window approximation.
    points = tuple(
        ReturnStabilitySourcePoint(
            trade_date=date(2026, 1, 1) + timedelta(days=index),
            net_value=(Decimal("1.01") ** index).quantize(_SIX),
        )
        for index in range(65)
    )
    result = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )
    assert len(result.rolling) == 2
    expected_total = (Decimal("1.01") ** 63 - Decimal("1")).quantize(_SIX)
    assert result.rolling[0].total_return == expected_total


# --- 1.4 rolling boundary tests ------------------------------------------------


def test_fewer_than_64_points_has_insufficient_status() -> None:
    points = _daily_business_points(63)
    result = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )

    assert result.rolling_status == "insufficient_observations"
    assert result.sharpe_status == "insufficient_observations"
    assert result.rolling == ()
    assert result.window_sessions == 63
    assert result.source_point_count == 63
    assert result.effective_return_count == 62


def test_empty_curve_has_explicit_empty_state() -> None:
    result = derive_return_stability(
        points=(),
        requested_start_date=date(2026, 1, 1),
        requested_end_date=date(2026, 12, 31),
        risk_free_rate=Decimal("0.02"),
    )

    assert result.rolling_status == "insufficient_observations"
    assert result.sharpe_status == "insufficient_observations"
    assert result.source_point_count == 0
    assert result.effective_return_count == 0
    assert result.rolling == ()
    assert result.monthly == ()
    assert result.yearly == ()


def test_zero_dispersion_has_zero_volatility_and_null_sharpe() -> None:
    # A flat persisted curve reconstructs identical zero returns: population
    # variance is zero, volatility is 0.000000, Sharpe is null.
    points = tuple(
        ReturnStabilitySourcePoint(
            trade_date=date(2026, 1, 1) + timedelta(days=index),
            net_value=Decimal("1.000000"),
        )
        for index in range(65)
    )
    result = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )

    assert len(result.rolling) == 2
    assert all(point.volatility == Decimal("0.000000") for point in result.rolling)
    assert all(point.sharpe_ratio is None for point in result.rolling)


def test_repeated_derivation_is_deterministic() -> None:
    points = _daily_business_points(70)
    first = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )
    second = derive_return_stability(
        points=points,
        requested_start_date=points[0].trade_date,
        requested_end_date=points[-1].trade_date,
        risk_free_rate=Decimal("0.02"),
    )

    assert first == second
    assert first.rolling == second.rolling
    assert first.monthly == second.monthly
    assert first.yearly == second.yearly


# --- 1.5 calendar bucket tests -------------------------------------------------


def test_cross_month_return_belongs_to_ending_month() -> None:
    jan = _point(30, "1.000000")
    feb2 = _point(2, "1.100000", month=2)
    feb27 = _point(27, "1.210000", month=2)
    mar2 = _point(2, "1.100000", month=3)
    points = (jan, feb2, feb27, mar2)

    result = derive_return_stability(
        points=points,
        requested_start_date=date(2026, 1, 1),
        requested_end_date=date(2026, 3, 31),
        risk_free_rate=Decimal("0.02"),
    )

    assert [bucket.period for bucket in result.monthly] == ["2026-02", "2026-03"]
    feb = result.monthly[0]
    assert feb.first_date == date(2026, 2, 2)
    assert feb.last_date == date(2026, 2, 27)
    assert feb.observation_count == 2
    assert feb.total_return == Decimal("0.210000")  # 1.1 * 1.1 - 1
    assert feb.is_partial is False
    mar = result.monthly[1]
    assert mar.observation_count == 1
    assert mar.total_return == Decimal("-0.090909")  # 1.0 / 1.1 - 1
    assert mar.is_partial is False
    # Yearly compounds all three returns.
    yearly = result.yearly[0]
    assert yearly.period == "2026"
    assert yearly.observation_count == 3
    assert yearly.total_return == Decimal("0.100000")  # 1.1 * 1.1 * (1/1.1) - 1


def test_requested_scope_partial_flags_come_from_run_bounds() -> None:
    points = (
        _point(2, "1.000000", month=2),
        _point(15, "1.100000", month=2),
        _point(27, "1.210000", month=2),
    )

    # Bounds cover only part of February.
    partial = derive_return_stability(
        points=points,
        requested_start_date=date(2026, 2, 1),
        requested_end_date=date(2026, 2, 20),
        risk_free_rate=Decimal("0.02"),
    )
    assert partial.monthly[0].is_partial is True

    # Bounds cover the whole natural month even though curve endpoints are not
    # the calendar boundaries (weekends/holidays).
    complete = derive_return_stability(
        points=points,
        requested_start_date=date(2026, 2, 1),
        requested_end_date=date(2026, 2, 28),
        risk_free_rate=Decimal("0.02"),
    )
    assert complete.monthly[0].is_partial is False
    assert complete.monthly[0].first_date == date(2026, 2, 15)
    assert complete.monthly[0].last_date == date(2026, 2, 27)


def test_curve_endpoints_do_not_redefine_requested_scope() -> None:
    # Requested bounds cover the full year, but the curve's first and last
    # trade dates fall inside the year (they are not official sessions on the
    # calendar boundaries). is_partial must stay False.
    points = (
        _point(2, "1.000000", month=2),
        _point(15, "1.100000", month=2),
        _point(20, "1.210000", month=2),
    )
    result = derive_return_stability(
        points=points,
        requested_start_date=date(2026, 1, 1),
        requested_end_date=date(2026, 12, 31),
        risk_free_rate=Decimal("0.02"),
    )
    assert result.yearly[0].is_partial is False
    assert result.yearly[0].first_date == date(2026, 2, 15)
    assert result.yearly[0].last_date == date(2026, 2, 20)


def test_empty_calendar_buckets_are_omitted() -> None:
    # Returns end in February (1/30 -> 2/2) and April (2/27 -> 4/1); no return
    # ends in March because no persisted point falls in March, so the March
    # bucket is omitted entirely.
    points = (
        _point(30, "1.000000"),
        _point(2, "1.100000", month=2),
        _point(27, "1.210000", month=2),
        _point(1, "1.331000", month=4),
    )

    result = derive_return_stability(
        points=points,
        requested_start_date=date(2026, 1, 1),
        requested_end_date=date(2026, 4, 30),
        risk_free_rate=Decimal("0.02"),
    )

    assert [bucket.period for bucket in result.monthly] == ["2026-02", "2026-04"]
    assert result.monthly[0].observation_count == 2
    assert result.monthly[1].observation_count == 1


def test_year_boundary_compounds_across_december_january() -> None:
    points = (
        _point(29, "1.000000", month=12, year=2025),
        _point(30, "1.100000", month=12, year=2025),
        _point(2, "1.210000", month=1, year=2026),
        _point(15, "1.331000", month=1, year=2026),
    )
    result = derive_return_stability(
        points=points,
        requested_start_date=date(2025, 12, 1),
        requested_end_date=date(2026, 1, 31),
        risk_free_rate=Decimal("0.02"),
    )

    assert [bucket.period for bucket in result.yearly] == ["2025", "2026"]
    # 12/29 -> 12/30 return belongs to 2025; the requested scope only covers
    # December, so the 2025 year bucket is partial.
    assert result.yearly[0].observation_count == 1
    assert result.yearly[0].total_return == Decimal("0.100000")
    assert result.yearly[0].is_partial is True
    # 12/30 -> 1/2 and 1/2 -> 1/15 returns compound in 2026; the requested
    # scope ends on 1/31, so the 2026 year bucket is partial.
    assert result.yearly[1].observation_count == 2
    assert result.yearly[1].total_return == Decimal("0.210000")
    assert result.yearly[1].is_partial is True
    # Monthly buckets follow the same ending-date assignment.
    assert [bucket.period for bucket in result.monthly] == ["2025-12", "2026-01"]
    assert result.monthly[0].observation_count == 1
    assert result.monthly[1].observation_count == 2
