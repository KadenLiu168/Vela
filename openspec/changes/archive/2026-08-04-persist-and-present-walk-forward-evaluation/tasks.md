## 1. Prerequisite and versioned contract gate

- [x] 1.1 Before implementation edits, verify `strengthen-walk-forward-evaluation-contract` and `add-active-and-downside-risk-metrics` have completed their applicable full gates and independent review; re-read their final report, metric and persistence types and stop if either contract is still moving.
- [x] 1.2 Add failing `wf_evidence_v1` Pydantic round-trip tests for all eight strategy summaries, positive rate, generalization gap, both benchmark return/TE/IR groups, effective validated-config parameter stability, metric-local nulls, threshold-only evidence status and rejection of missing/extra/non-finite fields.
- [x] 1.3 Implement the single evidence domain schema used by report serialization, persistence validation, typed query reads and API responses; add unsupported-version and corrupt-document tests that fail closed.
- [x] 1.4 Add fixed-byte/vector tests for the exact `wf_provenance_v1` configuration payload keys, canonicalization bytes, SHA-256 output, path independence, declared array-order preservation and effective-field changes.
- [x] 1.5 Add fixed-byte/vector tests for the tagged ETF/session/following-session/loaded-price record stream, exact SHA-256 output, execution-sensitive ETF-id remapping and other relevant input drift, inclusion of observable non-official rows and exclusion of output, pre-inception and future-price rows.
- [x] 1.6 Add failing candidate-audit tests for the four fixed skip categories, count/reason reconciliation and absence of raw exception, traceback, candidate or dynamic-status text.

## 2. Persistence model and migration

- [x] 2.1 Add failing ORM tests for typed `WalkForwardRun` and ordered `WalkForwardRunWindow` fields, non-negative/reconciled counts, parent ordinal uniqueness, unique OOS backtest ownership, relationships and application-level lack of mutation helpers.
- [x] 2.2 Implement the parent/child SQLAlchemy models with typed date/identity/timestamp/checksum columns and JSON documents, without duplicating OOS strategy or benchmark metrics and without claiming SQLite delete enforcement.
- [x] 2.3 Add persistence helpers that validate provenance/evidence, window count, child order, OOS ownership and candidate counts before one final flush while leaving commit/rollback to the caller.
- [x] 2.4 Create one Alembic revision for both tables, count checks, ownership/ordinal uniqueness, the `(strategy_id, finished_at, id)` history index and foreign-key declarations without enabling global SQLite foreign keys or backfilling history.
- [x] 2.5 Add file-backed upgrade/downgrade tests that seed legacy and OOS Backtest/Signal/curve/benchmark rows, insert valid WF history after upgrade, exercise declared constraints with explicit FK enforcement where relevant, and prove every evidence-owner row survives downgrade unchanged.

## 3. Provenance, atomic runner persistence and queries

- [x] 3.1 Implement pre-execution candidate validation, `TradingCalendar`-only window generation and maximum strategy-declared lookback derivation before any source OOS call, including no-valid-candidate, negative-lookback, price-date/calendar disagreement, incomplete-calendar and missing-price failure tests.
- [x] 3.2 Implement the exact compact input-manifest schema with execution-sensitive local ETF ids plus canonical identities/inception dates, full required official-session sequence, nullable following-session sentinel, global/per-ETF counts and nullable bounds, including zero-row ETF entries and no raw price-value array.
- [x] 3.3 Extend window/report results with OOS backtest id, candidate/eligible/skipped counts and normalized reason counts; preserve the prerequisite evidence fields and add serialization tests.
- [x] 3.4 Add failing runner tests requiring successful executions to persist one parent and chronological children at the end of the caller transaction, flush/return the parent id and never commit or roll back.
- [x] 3.5 Implement runner persistence linking every child to exactly one selected OOS run and storing dot-path-resolved effective parameters from the selected validated config, train Sharpe, reconciled counts and both provenance checksums.
- [x] 3.6 Add provenance, late-window, fixed-benchmark, evidence-validation, parent/child flush and caller-commit failure tests proving no WF, OOS, signal, strategy-curve or benchmark artifact becomes durable and no persisted id is reported.
- [x] 3.7 Add repeat-run tests proving distinct parent/OOS identities with equal checksums for equal effective inputs, path-independent configuration identity and no reuse or overwrite.
- [x] 3.8 Implement tested core list/count/detail query helpers with limit 1..100, non-negative offset, current-strategy filtering, stable `finished_at DESC, id DESC` ordering, exact total, chronological eager-loaded windows, exact OOS/dual-benchmark ownership, empty legacy history and no equity-curve load.
- [x] 3.9 Add typed-query tests proving unsupported provenance/evidence versions, invalid JSON shapes and parent/child count drift raise the persisted-data contract error instead of returning partial data.

## 4. CLI completion contract

- [x] 4.1 Add CLI tests proving a successful managed commit prints `Walk-forward run id: <id>` and preserves terminal/`--output` evidence content.
- [x] 4.2 Add commit-failure tests proving a flushed id is never printed as persisted and all source artifacts roll back.
- [x] 4.3 Restructure the CLI return/print boundary only as needed so report formatting remains unchanged and id output occurs after `managed_session` exits successfully.

## 5. Read-only HTTP API and cross-version evidence access

- [x] 5.1 Define exact Pydantic WF summary/page/detail/configuration/manifest/evidence/window/OOS/benchmark schemas with ISO date/timestamp strings, persisted Decimal string/null fields, integer/null longest-drawdown duration, peak/trough/nullable-recovery dates and aggregate JSON number/null fields.
- [x] 5.2 Add a domain router implementing only `GET /api/walk-forwards` and `GET /api/walk-forwards/{run_id}` with default limit 10, bounds 1..100, non-negative offset, current-strategy-only scope, exact total and standard 404/unexpected-error behavior.
- [x] 5.3 Add API tests for stable ordering, pagination boundaries, absence of `strategyId`, empty legacy history, provenance versions/checksums, following-session manifest, full `wf_evidence_v1`, ordered OOS links, fixed benchmarks and absence of mutation endpoints.
- [x] 5.4 Change Backtest Detail, Backtest Signals and Signal Detail by-id queries to filter by current `strategy_id` but not `config_version`; preserve all list/latest filters and add ordinary historical-version plus `wf-*` success tests.
- [x] 5.5 Add isolation tests proving other-strategy Backtest/Signal/WF ids remain indistinguishable from missing ids and corrupt persisted WF documents return no partial response.

## 6. Walk-forward Web history and detail

- [x] 6.1 Extend Web API client/types and validation fixtures for the exact paginated WF summary/detail schema, persisted Decimal-string, integer-duration and aggregate-number encodings, legacy empty history and standard error responses.
- [x] 6.2 Add lazy `/walk-forwards` and `/walk-forwards/:id` route/navigation tests covering direct load, active navigation, route-id changes, loading, stale-response suppression, empty/error states and not-found detail.
- [x] 6.3 Build the fixed-page-size-10 history page with exact-total pagination, run identity/time, strategy, configured interval, window count, provenance/evidence versions and compact checksums using existing primitives.
- [x] 6.4 Add detail component tests for all eight strategy summaries, duration peak/trough/ongoing-recovery dates, evidence counts/status, positive rate, dual-benchmark return/TE/IR groups, IS/OOS gap, parameter frequencies/transitions, provenance manifest and candidate/reason reconciliation.
- [x] 6.5 Build the dedicated detail page using existing design-system primitives, explicitly presenting independent OOS windows without a score, pass/fail, Dashboard addition or continuous curve.
- [x] 6.6 Add end-to-end component/route tests for WF Detail → `wf-*` Backtest Detail → paginated Backtest Signals → Signal Detail and for other-strategy 404 behavior.
- [x] 6.7 Run browser QA at 1440x1000 and 390x844 for loading/empty/error/not-found/content states, keyboard navigation/focus, exact pagination, locally labeled table overflow, dense evidence readability and console errors.

## 7. Validation

- [x] 7.1 Run focused provenance, evidence-schema, model, migration, runner, persistence, query, CLI, API and Web tests against test-owned file-backed SQLite databases; do not migrate or write default `vela.db`.
- [x] 7.2 Run `openspec validate persist-and-present-walk-forward-evaluation --strict` and trace every requirement/scenario to design, implementation task and planned test evidence.
- [x] 7.3 After the final stable implementation revision, run the complete Python and Web CI-equivalent gates and record results for independent review.
