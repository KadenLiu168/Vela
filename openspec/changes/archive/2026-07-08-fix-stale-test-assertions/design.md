## Context

Six pytest tests are red on `main` and two `mypy` errors are present, all pre-existing and unrelated to the recently archived `reduce-signal-generation-sql-amplification` change. Investigation traced them to three independent root causes, each a case of **tests/types drifting behind a legitimate production or configuration change**:

| Root cause | Origin | Affected tests |
|---|---|---|
| A. ETF pool expanded 6 -> 11 | `cbd85325 add etfs pool` | `test_config.py` (x2), `test_sync_etf_pool.py` (x2 assertions) |
| B. `strategy_id` casing `dual_momentum` -> `Dual_momentum` | `02c1aea8` (yaml) | `test_dashboard.py`, `test_api_config.py` |
| C. dashboard `etf_list` gained `earliest_trade_date` | `c25bfb07` (F-109) | `test_market_data_fetch.py`, `test_dashboard.py` (masked behind B) |
| D. untyped `counts` dict from `Row[tuple]` query | `d5736eb6` | `strategy_signal_report.py:115-116` (mypy) |

In every case the **production code/configuration is the source of truth** and is internally consistent (verified: yaml has 11 ETFs and `Dual_momentum`; DB stores 11 ETFs and `Dual_momentum`; `dashboard_aggregation.py` emits `earliest_trade_date`; frontend `DashboardPage.tsx` consumes it). The tests encode stale snapshots. The fix realigns tests/types to production, and the new `test-suite-validation` requirement codifies the principle so the drift does not recur.

## Goals / Non-Goals

**Goals:**
- Restore a green `uv run pytest`, `uv run ruff check`, and `uv run mypy` on `main`.
- Replace snapshot assertions with contract assertions so future legitimate config/response-shape changes do not redden the suite.
- Resolve the two `mypy` errors with a minimal annotation.
- Codify the contract-over-snapshot principle in `test-suite-validation`.

**Non-Goals:**
- Renaming `strategy_id` (`Dual_momentum` convention) - production is consistent; renaming crosses change boundaries.
- Refactoring the dashboard aggregation, config loader, or sync CLI - production is unchanged.
- Adding new test coverage beyond fixing the drifted assertions.
- Touching the recently archived signal-generation change.

## Decisions

### Decision 1: Fix direction is tests -> production, never production -> tests
**Choice:** In all four root causes, production/config is correct and tests are wrong; fix the tests.
**Why:** Each production change was a deliberate feature (pool expansion, casing normalization, dashboard field, history-browsing query). Reverting production would undo intended behavior. The tests' job is to verify the contract, not freeze the snapshot.
**Alternative considered:** Normalize `strategy_id` back to lowercase. Rejected - `Dual_momentum` is the checked-in value, DB-stored value, and frontend-expected value; the test literal is the only lowercase occurrence.

### Decision 2: Contract assertions derive expected values from loaded config, not literals
**Choice:** For root causes A and B, assertions read the expected value from `load_app_config(...)` / `load_etf_pool_config(...)` at test time rather than hardcoding `11` or `"Dual_momentum"`.
**Why:** A literal `== 11` would redden again on the next pool expansion. Deriving from loaded config makes the assertion express the real contract ("loader returns what the YAML contains") and is immune to legitimate growth.
**Alternative considered:** Assert only `len(config.etfs) >= 1` (non-empty). Rejected - too weak; it would not catch a loader that silently drops ETFs. Deriving the expected count from the source YAML preserves the count check while removing the drift.

### Decision 3: Root cause C fix adds the missing field to the expected fixture
**Choice:** Add `earliest_trade_date` to the expected `etf_list` entries in `test_market_data_fetch.py` (`"2026-06-17"`) and `test_dashboard.py` (`QQQ` -> `"2026-06-23"`, `SPY` -> `"2026-06-22"`). The `test_dashboard.py` drift was masked behind the `strategy_id` failure fixed in root cause B.
**Why:** The production aggregation already emits this field for the seeded data (SPY has only `2026-06-17`, so that is its earliest), and the frontend already consumes it. The test fixture simply must mirror the real response shape - this is exactly the new requirement's "response-shape" scenario.
**Alternative considered:** Assert only a subset of fields (loose matching). Rejected - the existing test style uses exact-equality assertions on the dashboard body; switching to subset matching would weaken the contract and diverge from neighboring tests.

### Decision 4: mypy fix is a local annotation, not a query rewrite
**Choice:** Annotate `counts: dict[int, int]` and build it via a dict comprehension over the `Row[tuple[int, int]]` results, rather than `dict(rows)`.
**Why:** `dict(Sequence[Row[tuple[int,int]]])` does not infer because `Row` is not a `tuple` for `dict()`'s converter. A comprehension `r[0]: r[1]` makes the unpacking explicit and satisfies mypy with zero behavior change. Minimal and surgical.
**Alternative considered:** Cast `dict(cast(list, rows))`. Rejected - `cast` hides the type error instead of expressing the conversion; the comprehension is clearer.

### Decision 5: Single change, not per-root-cause changes
**Choice:** Bundle all four root causes (A/B/C/D) into one change.
**Why:** They share one root cause class (drifted tests/types), one goal (restore green), and one principle (contract-over-snapshot). Splitting into four changes would be ceremony with no isolation benefit - each fix is independent and low-risk. The user framed them together as "point 6".
**Alternative considered:** One change per root cause. Rejected - excessive overhead for 1-3 line fixes each.

## Risks / Trade-offs

- [Contract assertions are slightly more verbose] -> Deriving expected values from loaded config adds a line or two per test. Accepted: the immunity to drift is worth it, and the new spec requirement mandates this style.
- [Exact-equality on dashboard body remains brittle to unrelated field additions] -> If production adds another dashboard field later, `test_market_data_fetch.py` will reddden again. Accepted for now: the new requirement's "response-shape" scenario makes this an intentional, visible contract break rather than silent drift. A future change could introduce a shared response-shape fixture if drift recurs frequently.
- [Bundling D (mypy) with A/B/C (tests)] -> Slightly mixes "test fix" and "production annotation". Accepted: D is annotation-only with no behavior change, shares the drift root cause, and keeping the CI fully green in one change is more valuable than purity.

## Migration Plan

No migration. Pure test/type fixes with no runtime, API, DB, or config impact. Deploy is a single commit; rollback is revert with no side effects.

## Open Questions

None. All four root causes have verified sources of truth and decided fix directions.
