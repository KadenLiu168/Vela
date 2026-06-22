## Context

Vela already separates market data provider output from persistence: AkShare rows are normalized into `DailyPrice`, and `MarketPrice` stores internal daily ETF prices. The missing piece is an explicit mapping between these two internal shapes before future ingestion code persists rows.

## Goals / Non-Goals

**Goals:**

- Convert a provider `DailyPrice` value plus an internal `etf_id` into a `MarketPrice` ORM row.
- Preserve date, price, adjusted close, and volume values without changing their Python types.
- Keep AkShare-specific pandas column handling inside the AkShare provider and keep ORM construction outside the provider.
- Cover the mapping with focused tests.

**Non-Goals:**

- Do not implement database writes, upserts, sessions, or fetch orchestration.
- Do not resolve ETF symbols to `ETFInfo.id`.
- Do not change the `MarketPrice` schema, Alembic migrations, or provider interface.
- Do not add adjusted AkShare fetch modes.

## Decisions

1. Add a small mapping function instead of returning `MarketPrice` from providers.

   Rationale: providers currently stay independent from SQLAlchemy and from internal ETF ids. A mapper preserves that boundary while giving ingestion code a single tested conversion point.

   Alternative considered: have `AkShareMarketDataProvider` return `MarketPrice` rows. That would reduce one call site later, but it would bind provider code to ORM models and require an `etf_id` it cannot know.

2. Require callers to pass `etf_id`.

   Rationale: symbol-to-ETF lookup belongs to a later ingestion workflow that has database access. The mapper should stay deterministic and easy to test.

   Alternative considered: have the mapper query `ETFInfo` by symbol. That would force session handling into a simple field mapper and make error behavior broader than this change requires.

3. Keep the mapper single-row and pure.

   Rationale: Phase 1 needs the field contract first. Batch conversion, deduplication, and upsert conflict handling can build on this later without changing the row mapping rule.

   Alternative considered: introduce a batch ingestion service now. That would be premature because fetch logs, symbol lookup, and upsert policy have not been designed together.

## Risks / Trade-offs

- Symbol-to-ETF mismatches remain possible in future ingestion code -> Mitigation: keep `etf_id` explicit and test that the mapper never infers identity from provider symbols.
- A future batch ingestion service may need more helpers -> Mitigation: start with the smallest stable conversion function and compose it later.
- AkShare raw data is still tested through `DailyPrice` first, not directly into `MarketPrice` -> Mitigation: add an integration-style unit test that runs Fake AkShare output through provider normalization and then the mapper.
