## Context

Vela already has the lower-level pieces for daily ETF market data ingestion: `ETFInfo`, `MarketDataProvider`, `AkShareMarketDataProvider`, provider-to-`MarketPrice` mapping, SQLite market price upsert behavior, and `DataFetchLog`. The CLI currently only exposes `init-db`, so COP-35 needs a first user-facing command that runs the full daily price fetch path.

There is also an active `record-market-data-fetch-log` change that designs core fetch logging but explicitly excludes CLI behavior. This change covers the COP-35 end-to-end workflow and should either reuse the same core orchestration shape or replace that narrower change during implementation to avoid duplicate orchestration APIs.

## Goals / Non-Goals

**Goals:**
- Add a full daily market data fetch command to the `vela` CLI.
- Use active ETFs as the current ETF pool: `ETFInfo.is_active = true`.
- Fetch through AkShare, map provider rows to `MarketPrice`, upsert into SQLite, and record a `DataFetchLog`.
- Continue after per-symbol provider failures and report partial outcomes.
- Print a concise execution summary for operators.

**Non-Goals:**
- Do not add named ETF pools, pool membership tables, or ETF import commands.
- Do not implement incremental fetching, automatic date-range inference, scheduling, retry policy, or background jobs.
- Do not add schema migrations.
- Do not put provider, mapping, or upsert logic directly in the CLI entrypoint.

## Decisions

1. Treat active ETF metadata rows as the ETF pool.

   Rationale: the repository has no named pool model, while `ETFInfo.is_active` already represents the actionable universe. This keeps COP-35 focused on market data fetching instead of adding pool management.

   Alternative considered: add named ETF pools now. That would expand the P0 into data modeling and pool administration before the fetch path exists.

2. Put the fetch workflow in the core package and keep the CLI thin.

   Rationale: the workflow coordinates database lookup, provider calls, mapping, upsert, and fetch logging. Keeping that in core makes it testable and reusable by later schedulers or APIs.

   Alternative considered: implement the workflow in `apps/cli`. That would be faster initially but would make later non-CLI entrypoints duplicate business logic.

3. Support only full fetch mode in the COP-35 CLI.

   Rationale: the ticket asks for full market data fetching. Incremental date calculation has separate product behavior and should not be guessed here.

   Alternative considered: add both full and incremental flags. Incremental behavior would require additional decisions around last-success lookup and missing trading days.

4. Record one `DataFetchLog` per command run.

   Rationale: the existing log model stores requested symbols and task-level lifecycle fields. One row per command run gives a clear audit trail without adding new tables.

   Alternative considered: record one log row per symbol. That improves symbol-level diagnostics but makes command-level summaries harder and changes the existing log model intent.

5. Return zero exit status for `success` and `partial`, non-zero for `failed`.

   Rationale: `partial` means useful data was written but some symbols need attention; the printed summary and fetch log carry the failure detail. Complete failure should be script-detectable.

   Alternative considered: return non-zero for partial. That is stricter, but it makes a run with successful persisted data look operationally identical to a total failure.

## Risks / Trade-offs

- AkShare symbols may not match all `ETFInfo.symbol` values -> Record provider failures per symbol and show failed symbols in the summary.
- Partial runs can leave stale data for failed symbols -> Persist successful symbols and mark the log as `partial` with concise error text.
- Empty active ETF universe could look like success without work -> Treat it as a failed command with a clear message because no requested symbols exist.
- Two active changes may overlap on core fetch logging -> Implement one shared core orchestration path and avoid creating duplicate APIs.
