## Context

`MarketPrice` already defines daily price identity as `(etf_id, trade_date)`, and `upsert_market_prices` already targets that identity with SQLite `ON CONFLICT DO UPDATE`. Existing tests cover insertion, updating an existing row, different ETFs on the same date, empty input, and duplicate keys inside one batch.

COP-68 is a testing change for the duplicate ETF/trading-date ingestion path. The implementation should remain unchanged unless focused regression coverage reveals that duplicate writes can create multiple `market_price` rows.

## Goals / Non-Goals

**Goals:**

- Add explicit test coverage for repeated market price writes with the same ETF and trading date.
- Verify the persisted table has exactly one row for the duplicated key.
- Verify the final row reflects the last supplied market price values.
- Keep the change limited to market data upsert behavior.

**Non-Goals:**

- Do not change the database schema or migration history.
- Do not alter provider normalization, fetch workflows, CLI commands, or logging.
- Do not add new deduplication policy beyond the existing "last supplied value wins" behavior.

## Decisions

1. Extend `packages/core/tests/test_market_price_upsert.py` instead of adding a separate test module.
   - Rationale: the behavior belongs to the existing upsert helper and can reuse its in-memory SQLite setup and fixtures.
   - Alternative considered: add an integration test through fetch workflows. That would widen COP-68 into provider/fetch orchestration and make failures harder to diagnose.

2. Assert database row count and final stored values after duplicate same-key upsert.
   - Rationale: COP-68 acceptance criteria are about preventing duplicate records, not just returned counts.
   - Alternative considered: assert only `rows_inserted`/`rows_updated`. Counts alone do not prove the database has one persisted row.

3. Avoid implementation edits unless the new test fails.
   - Rationale: current code already deduplicates input keys and uses the database unique constraint as the conflict target.
   - Alternative considered: refactor `_deduplicate_market_prices` for readability. That is unrelated to the requested testing coverage.

## Risks / Trade-offs

- Test may overlap existing duplicate-batch coverage -> Mitigation: make the test name and assertions directly reflect the COP-68 acceptance criteria, especially the final persisted row count.
- SQLite-specific upsert behavior remains the tested boundary -> Mitigation: this matches the existing persistence contract and current project storage backend.
