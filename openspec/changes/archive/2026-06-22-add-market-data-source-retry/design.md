## Context

Vela already separates market data ingestion into a provider boundary, a fetch orchestration workflow, mapping, SQLite upsert, and durable `DataFetchLog` records. The AkShare provider currently wraps source-call failures in `MarketDataProviderError`, and the fetch workflow catches those failures per symbol so a run can finish as `failed` or `partial`.

COP-37 adds retry behavior for temporary data source failures. The key constraint is to make recoverable AkShare call failures less noisy without hiding final failures or broadening retry behavior to invalid returned data.

## Goals / Non-Goals

**Goals:**

- Add `tenacity` as the retry mechanism for AkShare source-call failures.
- Use a simple finite retry policy that is easy to inspect in code.
- Retry only the AkShare network/source call, not row normalization or validation.
- Preserve the existing provider-level error surface after retries are exhausted.
- Preserve existing `DataFetchLog` behavior for final failed and partial runs.

**Non-Goals:**

- Do not add configurable retry settings, environment variables, or CLI flags.
- Do not add a scheduler, background worker, circuit breaker, cache, or rate limiter.
- Do not retry invalid AkShare rows, missing columns, or local mapping/upsert failures.
- Do not change the `MarketDataProvider` protocol or return shape.
- Do not change CLI output or exit-code semantics.

## Decisions

1. Apply retry inside `AkShareMarketDataProvider`, around only `fund_etf_hist_em`.

   Rationale: COP-37 is about temporary data source failure. The provider owns AkShare-specific source access and can retry without exposing retry details to callers.

   Alternative considered: retry the entire `fetch_full_market_prices` per-symbol block. That would also retry mapping or validation failures, which are not transient source-call failures and could make errors harder to diagnose.

2. Use a fixed, finite retry policy.

   Rationale: A policy such as three total attempts with a fixed one-second wait satisfies the requirement for simple and explicit behavior. It avoids introducing tuning surfaces before production orchestration exists.

   Alternative considered: exponential backoff with jitter. That is useful for large production jobs, but it is more behavior than COP-37 asks for and makes tests and operator timing less obvious.

3. Preserve `MarketDataProviderError` after retry exhaustion.

   Rationale: Existing fetch orchestration already records provider failures in `DataFetchLog` and reports `failed_symbols`. Keeping the same error type avoids changes to the fetch workflow, CLI, and provider protocol.

   Alternative considered: return a retry result object with attempt metadata. That would require changing the provider contract and every caller for little immediate value.

4. Keep final fetch logging in the orchestration layer.

   Rationale: `DataFetchLog` represents a fetch task, not an individual source-call attempt. The existing task-level log should record the final outcome after retries finish.

   Alternative considered: write one log entry per retry attempt. That would improve diagnostics but requires a new per-symbol or per-attempt log model, which is outside COP-37.

## Risks / Trade-offs

- Retry increases command runtime when AkShare is unavailable -> Keep attempts and wait time small and fixed.
- Fixed waits may not be ideal for provider rate limiting -> Accept for now because COP-37 asks for simple behavior, not production-grade throttling.
- Attempt details are not persisted -> Preserve final failure visibility in `DataFetchLog`; add per-attempt diagnostics only if a later issue needs it.
- Retrying every source exception may include some permanent AkShare failures -> The retry limit bounds wasted time, and final errors still include provider context.

## Migration Plan

- Add the `tenacity` dependency through `uv`.
- Add focused provider tests before implementation.
- Implement retry inside the AkShare provider without changing public CLI or workflow APIs.
- Run provider tests plus market data fetcher and CLI fetch tests to confirm final logging behavior is unchanged.

Rollback is straightforward: remove the retry wrapper and dependency if the behavior causes unexpected delays or provider interaction issues.

## Open Questions

- None for COP-37. The retry policy is intentionally fixed and minimal.
