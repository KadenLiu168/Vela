## Why

Vela currently treats every missing active-ETF price on an official A-share session as corrupted input, but the real Walk-forward range contains legitimate full-day ETF halts for fund-holder voting and share split/merge processing. At the same time, every local ETF lacks an authoritative listing boundary, so the validator cannot distinguish pre-listing dates, confirmed non-trading dates, and unexplained data loss without either blocking valid research or silently weakening the existing fail-fast contract.

## What Changes

- Add an authoritative ETF `listing_date` distinct from fund inception and local first-stored-price dates; active research-universe ETFs without this metadata fail preflight instead of being assumed eligible for all history.
- Add versioned, source-attributed per-ETF official-session status for confirmed full-day suspension and corporate-action halt events, with explicit import/synchronization into SQLite and conflict validation against stored market prices.
- Build one shared resolved strategy-session price panel: real `MarketPrice` rows remain the only raw observations, confirmed full-day non-trading sessions receive a derived prior-adjusted-close valuation and `tradable = false`, and every unexplained required gap remains a hard error.
- **BREAKING** Replace the current rule that every active ETF must have a raw price on every post-listing official session with a stricter typed-input rule: each required ETF/session must have exactly one admissible source state—one raw price or one authoritative full-day non-trading status—and unknown or contradictory states fail closed.
- Apply the same official-session, valuation, and tradability semantics to historical signals, strategy equity curves, fixed benchmarks, ordinary backtests, and Walk-forward preflight/OOS execution. A scheduled rebalance that would trade a non-tradable ETF is deferred as one atomic portfolio rebalance to the next official session on which all required trade legs are tradable; partial fills and opportunity-driven universe changes are not synthesized.
- Version Walk-forward input provenance so listing metadata, non-trading-session evidence, resolved valuation policy, and derived session values participate in immutable snapshot validation and checksum drift detection while legacy provenance remains readable.
- Improve missing-input errors with deterministic category counts and bounded ETF/date samples without downgrading unresolved gaps to warnings.
- Do not synthesize or persist OHLC rows for non-trading dates, infer suspension from an isolated gap, use `first_stored_date` as an execution eligibility boundary, mutate historical runs, or write the repository `vela.db` during tests.

## Capabilities

### New Capabilities

- `etf-session-status`: Defines authoritative per-ETF official-session status, source attribution, synchronization, conflict rules, and the resolved strategy-session valuation/tradability panel.

### Modified Capabilities

- `etf-info-model`: Adds authoritative listing-date metadata and deterministic ETF-pool synchronization without conflating listing, fund inception, or local data coverage.
- `database-migrations`: Adds the listing-date and ETF-session-status SQLite schema while preserving existing metadata and historical research rows.
- `cli-database-initialization`: Adds explicit, database-targeted synchronization of versioned ETF temporal metadata and historical non-trading-session evidence.
- `trading-day-gap-detection`: Clarifies that first-stored-date suppression and per-ETF warning tolerance are ingestion diagnostics only and cannot determine backtest admissibility.
- `backtest-execution`: Resolves every required active-ETF/session through raw price or authoritative non-trading status, retains fail-fast behavior for unknown gaps, and defers blocked rebalances atomically.
- `strategy-signal-generation`: Consumes the complete resolved official-session panel, includes ETFs only on/after listing, and does not treat a non-tradable asset as immediately executable.
- `strategy-equity-curve`: Values confirmed full-day non-trading holdings deterministically without fabricating raw prices and prevents partial or synthetic rebalance execution.
- `backtest-run-model`: Versions the ordinary backtest input snapshot so status-backed derived values and their source evidence are reproducible without rewriting legacy runs.
- `backtest-benchmark-comparison`: Applies the same status-backed valuation and atomic rebalance-deferral rules to fixed benchmarks.
- `walk-forward-runner`: Uses the shared admissibility resolver before any source-side OOS output and reports aggregated unresolved-input context.
- `walk-forward-evaluation-history`: Introduces a new provenance version covering listing dates, authoritative session-status evidence, and the resolved valuation policy while preserving legacy reads.
- `http-api-service`: Exposes validated v1/v2 Walk-forward input provenance through an unambiguous typed response without partial detail on corrupt evidence.
- `web-frontend-app`: Presents status-aware v2 provenance and non-trading-session counts/sources in the existing Walk-forward Detail evidence view while keeping legacy v1 readable.

## Impact

- Core models, configuration, migrations, metadata synchronization, adjusted-price/session-panel resolution, signal generation, backtest runner, equity calculation, benchmark calculation, Walk-forward preflight/provenance, typed API/Web detail surfaces, and their deterministic tests are affected.
- CLI initialization/synchronization gains an explicit operation that writes only to the selected database; no automatic migration or repair of the user's default `vela.db` is performed.
- Existing `MarketPrice` schema semantics remain raw-provider observations. Existing persisted backtests and Walk-forward runs are not rewritten; new executions use the new policy/provenance version.
- No broker integration, real order execution, live suspension feed, reference-data management UI, or generic corporate-action accounting platform is added.
