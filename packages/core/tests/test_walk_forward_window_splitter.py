from datetime import date, timedelta

import pytest
from vela_core.walk_forward.window_splitter import generate_windows


def test_generate_windows_uses_complete_calendar_intervals() -> None:
    dates = [date(year, month, 1) for year in range(2019, 2025) for month in range(1, 13)]

    windows = generate_windows(
        dates, date(2019, 1, 1), date(2024, 12, 31), train_years=3, test_years=1, step_years=1
    )

    assert [
        (item.train_start, item.train_end, item.test_start, item.test_end) for item in windows
    ] == [
        (date(2019, 1, 1), date(2021, 12, 1), date(2022, 1, 1), date(2022, 12, 1)),
        (date(2020, 1, 1), date(2022, 12, 1), date(2023, 1, 1), date(2023, 12, 1)),
        (date(2021, 1, 1), date(2023, 12, 1), date(2024, 1, 1), date(2024, 12, 1)),
    ]


def test_generate_windows_clamps_leap_day_and_rejects_partial_range() -> None:
    dates = [date(2020, 2, 29), date(2021, 2, 28), date(2022, 2, 28)]
    windows = generate_windows(
        dates, date(2020, 2, 29), date(2022, 2, 28), train_years=1, test_years=1, step_years=1
    )
    assert windows[0].train_end == date(2020, 2, 29)
    assert windows[0].test_start == date(2021, 2, 28)

    with pytest.raises(ValueError, match="insufficient"):
        generate_windows(dates, date(2020, 2, 29), date(2021, 2, 28), 1, 1, 1)


def test_generate_windows_keeps_original_leap_day_anchor_across_steps() -> None:
    start = date(2020, 2, 29)
    end = date(2026, 2, 28)
    dates = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]

    windows = generate_windows(dates, start, end, 1, 1, 1)

    assert windows[4].train_start == date(2024, 2, 29)
