## 1. Baseline and contract tests

- [x] 1.1 Re-resolve the final `add-durable-walk-forward-execution` runner, enqueue, and provenance interfaces before editing; preserve all unrelated work and record any post-proposal interface drift that requires a narrow artifact correction.
- [x] 1.2 Add failing configuration/model tests proving fund inception and exchange listing are distinct, every active configured ETF requires `listing_date`, and `first_stored_date` cannot substitute for missing listing metadata.
- [x] 1.3 Add failing file-backed SQLite migration tests for nullable `ETFInfo.listing_date`, the constrained/indexed `etf_session_status` table, populated legacy-history preservation, and upgrade/downgrade behavior.
- [x] 1.4 Add failing reference-data validation/synchronization tests for supported statuses, mandatory source evidence, positive optional share ratio, duplicate identity, missing listed ETF, raw/status conflict, idempotency, caller-owned rollback, and unrelated-row preservation.

## 2. ETF temporal reference data and synchronization

- [x] 2.1 Extend `ETFInfo`, ETF configuration, and ETF-pool synchronization with separately owned optional fund inception and required-active listing dates; update the versioned ETF pool with reviewed official listing dates.
- [x] 2.2 Add the `ETFSessionStatus` ORM model and Alembic migration with foreign key, unique identity, status/source/ratio constraints, timestamps, and bounded query indexes.
- [x] 2.3 Add a versioned session-status configuration model/file containing the four reviewed 2019–2024 events, authoritative source metadata, and exact split/merge ratios where applicable; do not infer additional entries from local gaps.
- [x] 2.4 Implement pure validation plus idempotent caller-transaction-owned status synchronization that rejects conflicts before writing and never creates or edits `MarketPrice` rows.
- [x] 2.5 Add `vela sync-etf-session-status` with explicit file/database inputs, deterministic counts, atomic failure behavior, and CLI tests using only test-owned databases; retain `sync-etf-pool` as the sole listing-metadata writer.

## 3. Resolved official-session price panel

- [x] 3.1 Add failing pure tests for raw-price resolution, confirmed single/consecutive non-trading carry, `Decimal` preservation, pre-listing exclusion, unexplained gap, price/status conflict, missing carry anchor, and deterministic categorized error summaries.
- [x] 3.2 Implement the immutable `ResolvedSessionPrice` domain type and one pure chronological resolver that emits real adjusted values or status-backed non-tradable carry values without persistence.
- [x] 3.3 Adapt adjusted-price projection to resolved values while retaining the raw observation boundary for unaffected market-data consumers; prove no `MarketPrice` ORM property or derived-row cache is introduced.
- [x] 3.4 Keep fetch-time `detect_etf_trading_day_gaps` behavior diagnostic-only and add a regression showing its first-stored-date suppression cannot authorize backtest or Walk-forward execution.

## 4. Historical signals and atomic portfolio execution

- [x] 4.1 Add failing historical-signal tests for exact official-session lookbacks, explicit zero-return non-trading observations, listing-date universe entry, bounded/no-future panels, and desired-target retention when the selected ETF is non-tradable.
- [x] 4.2 Migrate strategy protocol implementations and historical orchestration from sparse `MarketPrice` sequences to bounded resolved-session values without adding database access or persistence to strategies.
- [x] 4.3 Add failing equity tests for confirmed-halt valuation, unexplained held-endpoint failure, non-tradable initial allocation, whole-rebalance deferral, no cost while blocked, one later execution/cost, empty-target deferral, and newer-target replacement.
- [x] 4.4 Implement pending complete-target state in the equity engine: mark existing holdings first, execute all changed legs only when all are tradable, retain cash before blocked initial allocation, and replace stale pending targets deterministically.
- [x] 4.5 Add high-precision split/merge regressions for `513100`, `513500`, and `512100`-shaped factors proving no unit-change windfall/loss and one explicit zero-return halt session before reopening.

## 5. Backtest and fixed-benchmark integration

- [x] 5.1 Refactor ordinary backtest preflight to require active listing metadata and the shared resolver; preserve exact calendar/lookback scope, aggregate unknown/conflict errors, pre-persistence failure, and caller-owned transaction behavior.
- [x] 5.2 Apply the identical resolved valuation and atomic pending-target semantics to equal-weight monthly and CSI 300 benchmarks, including blocked initialization and newer scheduled-target replacement.
- [x] 5.3 Add end-to-end backtest tests covering all four reviewed event shapes, an unknown isolated gap that still fails, a conflicting raw/status pair, benchmark/strategy identical date axes, and complete rollback on late failure.

## 6. Versioned backtest and Walk-forward provenance

- [x] 6.1 Add failing `backtest_input_v2` canonicalization/reconciliation tests for sessions, listing metadata, raw/derived ownership and counts, status source evidence, carry ancestry, checksum drift, legacy snapshot reads, and no future-point leakage.
- [x] 6.2 Implement and persist `backtest_input_v2` for new runs without rewriting legacy/null snapshots; keep derived evidence distinct from raw market rows.
- [x] 6.3 Add failing `wf_provenance_v2` tests for exact canonical record order, listing/status/policy/checksum coverage, raw/derived count reconciliation, supported legacy v1 reads, corrupt-v2 rejection, and durable queued-input drift.
- [x] 6.4 Implement `wf_provenance_v2` manifest/record construction and validation, preserving valid v1 query semantics and ensuring listing/status changes produce new checksums rather than mutating old runs.
- [x] 6.5 Route Walk-forward enqueue and claimed execution through the shared resolver before source OOS output; verify confirmed events pass explicitly while unknown gaps, conflicts, missing listing, or changed queued evidence fail with no partial artifacts.

## 7. Typed API and Web provenance

- [x] 7.1 Add API schema/router tests for an explicit validated v1/v2 input-provenance union, exact v2 listing/status/policy fields, unchanged v1 output, OpenAPI discrimination, and no partial detail on corrupt v2.
- [x] 7.2 Implement the typed API v2 response branch without exposing mutable worker internals or adding a reference-data mutation endpoint.
- [x] 7.3 Add frontend client/component tests for v2 raw/derived counts, listing boundaries, derived-valuation labeling, accessible source evidence, unchanged v1 rendering, and no Dashboard/route expansion.
- [x] 7.4 Implement the existing Walk-forward Detail provenance-section update and verify rendered behavior at 1440x1000 and 390x844 with keyboard/overflow checks.

## 8. Safe acceptance and readiness

- [x] 8.1 Run focused configuration, migration, synchronization, resolver, strategy, equity, benchmark, backtest, provenance, Walk-forward, API, CLI, Web, and deterministic integration tests against test-owned/file-backed SQLite databases.
- [x] 8.2 On a `/tmp` copy of the user's database, explicitly migrate and synchronize both versioned reference files, then run read-only preflight evidence proving the 2,028 pre-listing dates are excluded only by listing metadata, exactly four confirmed events resolve through status evidence, and no unknown required gap remains; do not write repository `vela.db`.
- [x] 8.3 Run `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest` after the final stable revision.
- [x] 8.4 Run `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build` after the final stable revision.
- [x] 8.5 Run `openspec validate support-authoritative-etf-non-trading-sessions --strict`, `openspec validate --all --strict`, `openspec doctor`, requirement-to-code-to-test evidence tracing, `git diff --check`, and a final scope/database-safety review; do not archive, commit, push, or operate on the user's database without separate authorization.
