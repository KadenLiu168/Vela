## Context

The core package currently has market-data and strategy-signal helpers, but no reusable way to derive rebalance dates for future backtest execution. COP-55 only requires generating weekly rebalance dates from an existing trading-date sequence.

## Goals / Non-Goals

**Goals:**

- Provide a deterministic core helper for weekly rebalance date generation.
- Define weekly rebalance dates as the last available input trading date in each ISO week.
- Keep holiday and missing-date behavior explicit by using only dates present in the input sequence.
- Cover typical, duplicate, unsorted, and holiday-gap date sequences with unit tests.

**Non-Goals:**

- No database query helper.
- No CLI command.
- No exchange calendar integration.
- No monthly, daily, or custom weekday rebalance rules.

## Decisions

- Add a pure function in `vela_core` rather than a database-backed service.
  - Rationale: COP-55 accepts a trading-date sequence as input, and a pure function is the smallest reusable backend contract.
  - Alternative considered: query `MarketPrice` rows directly. This would couple scheduling to persistence and is unnecessary for the requested scope.

- Use ISO week grouping and select the last available input date per group.
  - Rationale: the user decision defines weekly rebalance dates as each ISO week member's last available trading date.
  - Alternative considered: first available input date per ISO week. This was rejected during Explore.

- Normalize the result by sorting and deduplicating input dates before grouping.
  - Rationale: callers can pass raw trading-date sequences while still receiving stable, ascending output with at most one date per ISO week.

## Risks / Trade-offs

- The helper does not know about exchange-specific holidays beyond the supplied sequence -> tests and spec make clear that missing dates are not filled or inferred.
- ISO week boundaries can cross calendar years -> implementation groups by `date.isocalendar().year` and `week`, not by calendar year alone.
