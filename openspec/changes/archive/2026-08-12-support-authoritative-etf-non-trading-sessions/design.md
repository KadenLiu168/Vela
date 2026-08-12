## Context

Vela uses `TradingCalendar` as the official session axis and currently requires one `MarketPrice` row for every active ETF on every required session on or after `ETFInfo.inception_date`. That fail-fast rule intentionally prevents a missing row from becoming a silent zero return or a multi-session observation. It also rejects legitimate full-day non-trading events because the model has no authoritative instrument/session state.

The current local data exposes both sides of the problem. `ETFInfo.inception_date` is nullable and is never populated by ETF-pool synchronization, while the 2019–2024 Walk-forward envelope contains four isolated post-listing gaps. Public fund/exchange evidence identifies those dates as one holder-meeting suspension and three share split/merge processing dates. The adjacent stored `factor_hfq` values also change by the announced split/merge ratios for three events. Those dates have no raw exchange close to fetch, so inserting a copied OHLC row would misrepresent a derived valuation as an observation.

Two earlier contracts must remain distinct:

- fetch-time gap detection may use `max(inception_date, first_stored_date)` and warn because it diagnoses the locally fetched range;
- backtest/Walk-forward execution must not use `first_stored_date` to hide truncated inputs and must fail on every unexplained required gap.

The active `add-durable-walk-forward-execution` Change preserves immutable input provenance and explicitly excludes financial/evidence semantic changes. This Change is therefore independent and must integrate with, not broaden, that lifecycle work. Tests and validation use only test-owned SQLite databases; the repository `vela.db` is never migrated or repaired automatically.

## Goals / Non-Goals

**Goals:**

- Distinguish fund inception, exchange listing eligibility, raw price availability, and an authoritative full-day non-trading event.
- Resolve every active ETF/official-session pair into an auditable admissible state before strategy output.
- Preserve fail-fast behavior for absent metadata, unexplained gaps, contradictory evidence, and insufficient carry history.
- Represent a confirmed non-trading session as a derived unchanged adjusted valuation with `tradable = false`, without persisting fabricated market prices.
- Keep signal, strategy, benchmark, equity, ordinary backtest, and Walk-forward behavior on one shared resolved-session contract.
- Define deterministic pending-rebalance behavior when a target cannot be executed atomically.
- Version ordinary-backtest and Walk-forward provenance so every status-backed output is reproducible.
- Provide an explicit, database-targeted synchronization path for reviewed temporal metadata and historical exception evidence.

**Non-Goals:**

- Inferring suspension or a corporate action from price gaps, factor jumps, volume, or neighboring values.
- Filling an unexplained missing price, mutating raw `MarketPrice`, or treating `first_stored_date` as an execution boundary.
- Intraday/partial-day halts, limit-up/limit-down execution, volume/liquidity simulation, partial fills, order books, or broker integration.
- A live exchange-status feed or a generic corporate-action accounting engine.
- Rewriting historical backtests, legacy Walk-forward provenance, or the user's default database.
- Adding Web/API management screens for reference data in this Change.

## Decisions

### 1. Use `listing_date` as the economic eligibility boundary

Add nullable `ETFInfo.listing_date` while retaining nullable `inception_date` for the fund contract/economic inception date. The ETF-pool schema requires an ISO `listing_date` for every active configured ETF and synchronizes it deterministically. Runtime research preflight rejects an active ETF whose `listing_date` is null.

For an ETF and official session `D`:

- `D < listing_date`: the ETF is outside the candidate universe and needs neither price nor status;
- `D >= listing_date`: the ETF is eligible and every required session must resolve through a real price or an authoritative full-day non-trading status.

Using the first stored price was rejected because a locally truncated history is observational, not authoritative. Reinterpreting `inception_date` as listing date was rejected because a fund contract can predate exchange listing and the existing API/provenance already names the distinct field.

The schema migration does not guess or backfill listing dates. The existing versioned ETF-pool file is their sole configuration owner, and the existing ETF-pool sync against a selected database performs the operational update. Correct metadata changes input checksums by design.

### 2. Persist only exceptional authoritative instrument/session states

Add a separate versioned status file and `etf_session_status` table with one row per exceptional `(etf_id, trade_date)`:

- `status`: initially only `full_day_suspension` or `corporate_action_halt`;
- `reason`: a bounded stable reason identifier;
- `source_uri`: the authoritative announcement URL;
- `source_published_date`: the announcement date;
- optional positive `share_ratio` for split/merge evidence;
- timestamps and a unique `(etf_id, trade_date)` constraint.

Normal trading sessions do not receive status rows; an existing `MarketPrice` is their evidence. The versioned source file is validated before synchronization: ETF keys must be unique, dates must be on/after listing, source fields must be present, and ratios must be positive when supplied. Synchronization is idempotent and updates only fields controlled by that source file.

A raw price and a full-day non-trading status for the same ETF/date are contradictory and fail synchronization/resolution. A status outside the current execution envelope is retained as reference data but does not affect that run.

A boolean `is_suspended` column on `MarketPrice` was rejected because a full-day halt has no raw price row to annotate. Synthesizing a zero-volume OHLC row was rejected because it would make derived data indistinguishable from provider observations.

### 3. Resolve one complete official-session panel before consumers run

Introduce a pure core domain value, conceptually:

```text
ResolvedSessionPrice
  etf_id
  trade_date
  adjusted_value
  raw_close              # nullable
  raw_factor             # nullable
  tradable
  resolution             # market_price | confirmed_non_trading_carry
  status evidence        # nullable
```

The resolver receives ordered official sessions, listed active ETFs, raw price rows, and relevant status rows. It processes each ETF chronologically with `Decimal` arithmetic:

1. Before listing: emit nothing.
2. Raw price only: `adjusted_value = close_price * factor_hfq`, `tradable = true`.
3. Authoritative full-day status only: copy the immediately preceding resolved `adjusted_value`, set `tradable = false`, and retain the status evidence.
4. Neither source: unresolved gap, fail.
5. Both sources: contradictory state, fail.

Consecutive confirmed full-day events may carry the last real adjusted value. A first required listed session that has status but no preceding resolved real value fails; callers must load the immediately preceding official session/price needed to establish valuation. Derived values are quantized only at existing public/persistence boundaries, not during carry.

Carrying `close_price` or `factor_hfq` separately was rejected because a split/merge changes unit price and share count while economic value remains continuous. Carrying the already adjusted value represents the portfolio value invariant without inventing a raw quote.

The resolver reports deterministic category counts and a bounded sorted sample for missing listing metadata, unexplained ETF/session gaps, source conflicts, and missing carry anchors. Fetch-time warning helpers remain separate; no shared helper computes one boundary for both ingestion diagnostics and execution admissibility.

### 4. Strategies consume resolved official sessions, not sparse raw rows

Strategy-visible price panels change from sparse `MarketPrice` rows to ordered `ResolvedSessionPrice` values. Momentum and moving-average lookbacks count exact official sessions. A confirmed full-day event contributes the unchanged adjusted value for that session, so it creates an explicit zero price return instead of shortening the window or combining multiple official sessions.

An ETF joins the dated candidate universe on `listing_date`. A non-tradable session does not remove the ETF from ranking—the unchanged valuation is part of the evidence—but a generated target is only a desired allocation until execution semantics permit it. This avoids opportunistically changing the candidate universe because one asset is halted.

Direct one-date signal generation that is not executing a historical portfolio may still return the target and its scores; historical backtest execution owns the pending-rebalance state. Existing strategy implementations remain session-free and persistence-free.

### 5. Rebalances are atomic and deferred rather than partially synthesized

The equity engine keeps the currently invested state while marking every held ETF with the resolved valuation for each official session. For a confirmed full-day non-trading holding, market value is unchanged for that session.

When a different successful signal becomes effective, calculate the complete set of trade legs as the union of currently held and target ETF ids whose weights change. If any leg is `tradable = false` on that session:

- execute none of the rebalance;
- charge no transaction cost;
- retain the complete newest target as pending;
- continue valuing the existing portfolio.

On the first later official session where every pending leg is tradable, execute the whole rebalance and charge costs once. If a newer successful signal becomes effective before execution, it replaces the older pending target; stale intended trades are not queued. An empty target that liquidates a halted holding is likewise deferred. This is deterministic and avoids partial-fill assumptions outside the MVP.

The initial allocation follows the same rule: before the first executable target the portfolio remains cash. Fixed benchmarks use the identical mechanism; their scheduled rebalance does not bypass status constraints.

Treating the halted ETF as removed from the universe was rejected because it changes ranking based on future execution convenience. Executing only tradable legs was rejected because it creates unrequested partial-fill and leverage/cash behavior.

### 6. Raw market data and resolved research inputs remain separate

`MarketPrice` continues to mean a raw provider daily observation. Existing raw price APIs, price trend displays, fetch logs, and upsert behavior do not expose derived non-trading values as market data.

The adjusted-price projection layer accepts the resolved session domain values for strategy calculations while retaining a raw-row adapter for unaffected callers where practical. This keeps derivation in a pure package module and prevents ORM properties or persisted caches from becoming a second pricing authority.

### 7. Version both ordinary-backtest and Walk-forward input evidence

Ordinary `BacktestRun.data_snapshot_json` gains a versioned resolved-input shape for new runs. It records ordered official sessions, ETF id/exchange/symbol/listing date, raw price inputs, and every status-backed derived session with status/reason/source/ratio and carried adjusted value. Its checksum covers the canonical document. Legacy snapshots remain readable and unchanged.

Add `wf_provenance_v2`. Its canonical record stream contains, in order:

1. policy/provenance version;
2. ETF identity plus fund inception and listing dates;
3. ordered official sessions and following-session sentinel;
4. ordered raw price records;
5. ordered non-trading status/resolution records including carried adjusted value and source evidence.

Manifest reconciliation validates global/per-ETF raw and derived counts, date bounds, listed eligibility, source-state exclusivity, carry ancestry, supported statuses, and ordering. Query boundaries accept valid legacy `wf_provenance_v1` and new v2 documents but never reinterpret v1 as status-aware. Durable queued execution compares the exact v2 manifest/checksum again before source output; metadata or status drift terminally fails the queued run and requires resubmission.

### 8. Synchronization is explicit and safe for the local SQLite application

Add reviewed listing dates to the existing versioned ETF-pool file and continue to synchronize them through `sync-etf-pool`. Add a separate versioned session-status file containing only confirmed historical non-trading events and an explicit `sync-etf-session-status` command requiring the existing database-target selection. The status command validates the complete status file and referenced persisted ETF/listing metadata before writing, uses the caller-managed transaction, and reports inserted/updated/unchanged status counts. Neither file owns the other's fields.

Tests use file-backed `tmp_path` databases migrated from Alembic. No test invokes the command against `/Users/kaden/Vela/vela.db`. Applying the application migration and running reference-data synchronization against a user database remain separate, explicitly authorized operational steps.

### 9. Existing typed API and Web detail expose v2 provenance

The Walk-forward detail response currently validates a manifest fixed to `wf_provenance_v1`, and the Web client mirrors that literal type. Extend both to an explicit discriminated v1/v2 union. V2 exposes listing dates, raw/derived counts, resolution policy, and bounded status/source evidence; v1 preserves its existing shape. Unsupported or corrupt documents return the existing error contract with no partial detail.

The existing Walk-forward Detail provenance section displays v2 policy, listing boundaries, confirmed non-trading counts and bounded source evidence. It labels carried points as derived non-trading valuations rather than market quotes and keeps the evidence separate from performance verdicts. No reference-data editing surface, Dashboard card, or new route is added. Acceptance covers 1440x1000 and 390x844 plus semantic/keyboard behavior.

## Risks / Trade-offs

- **[Risk] A source announcement is wrong, removed, or insufficiently authoritative.** → Store the source URI, publication date, stable reason, and reviewed versioned local record; fail configuration validation when evidence is incomplete.
- **[Risk] Zero return on a halt date is a valuation policy, not a traded close.** → Expose it only as `confirmed_non_trading_carry`, retain source evidence, and never persist it as `MarketPrice`.
- **[Risk] Atomic deferral differs from a broker that could partially execute.** → Make whole-rebalance deferral an explicit versioned MVP rule and test pending-target replacement; partial execution remains out of scope.
- **[Risk] A long halt can make a stale valuation economically approximate.** → Preserve explicit status and zero-return observations so evidence is auditable; do not claim it is a live realizable quote.
- **[Risk] Changing strategy panel types has a broad internal blast radius.** → Introduce one narrow immutable domain type and migrate strategy, equity, benchmark, backtest, and Walk-forward consumers together under focused contract tests.
- **[Risk] Nullable migrated `listing_date` permits incomplete legacy databases.** → Keep the column migration-safe but make active research execution and reference-data validation fail closed until explicit synchronization supplies it.
- **[Risk] Provenance v2 changes checksums and comparability.** → Preserve legacy reads, never rewrite old runs, label the policy/version explicitly, and make new checksums intentionally reflect the changed inputs.
- **[Risk] This overlaps an unarchived durable-execution worktree.** → Limit this Change to new artifacts during proposal; during Apply re-resolve the current baseline and integrate through the existing preflight/provenance interfaces without overwriting unrelated work.
- **[Risk] A v2 backend with a v1-only client would reject or hide evidence.** → Deliver core provenance, typed API union, frontend client/rendering, and browser acceptance in one Change; retain an explicit v1 branch.

## Migration Plan

1. Complete and archive or otherwise establish a stable baseline for `add-durable-walk-forward-execution` before applying this Change; rebase the plan on its final runner/provenance interfaces.
2. Add migration-safe schema changes and deterministic reference-data validators/synchronizers; verify upgrade/downgrade on test-owned SQLite databases.
3. Add listing dates to the versioned ETF pool and the four reviewed historical non-trading events to the separate versioned status file, with authoritative evidence and exact split/merge ratios where applicable.
4. Introduce the pure resolver and migrate strategy/equity/benchmark/backtest/Walk-forward consumers with focused red-green contract tests.
5. Add versioned ordinary and Walk-forward provenance plus legacy-read and drift tests.
6. Update typed API and Web detail rendering, then run the complete Python and Web gates, browser acceptance, target/global strict OpenSpec validation, `openspec doctor`, and diff checks.
7. Operationally, stop active Vela writers, back up the selected database, explicitly run the Alembic upgrade and reference-data sync against that database, then submit a new Walk-forward run. Never mutate an already queued or historical run to adopt the new evidence.
8. Roll back by stopping writers, ensuring no new-policy run is active, downgrading the schema only if no v2-dependent operational data must remain, and restoring the pre-change application. Historical rows are never silently deleted or rewritten.

## Open Questions

None for proposal readiness. The initial status vocabulary, atomic deferral rule, four reviewed events, provenance versioning, and explicit synchronization boundary are fixed by this design; expansion to additional event types requires a later Change.
