## Context

The current Walk-forward runner persists each selected OOS backtest through the caller-owned SQLite transaction but returns the grouping and aggregate evidence only as an in-memory/text report. Nothing durable identifies one complete evaluation, its effective configuration and inputs, the ordered OOS runs it selected, or the evidence produced across them. Historical OOS runs therefore cannot be reliably reconstructed into their originating Walk-forward execution.

This Change is intentionally sequenced after `strengthen-walk-forward-evaluation-contract` and `add-active-and-downside-risk-metrics`. It persists and presents their final stable evidence rather than introducing a competing schema while those contracts are still moving. Apply MUST NOT begin until both prerequisite Changes have completed their applicable full gates and independent review.

Current OOS runs use deterministic `wf-*` configuration versions. The existing Backtest and Signal by-id API endpoints require the current configured version, so an OOS link currently returns 404 even when it belongs to the current strategy. This Change must repair that read boundary as part of the evidence navigation contract.

## Goals / Non-Goals

**Goals:**

- Persist one logically immutable parent record for every completely successful Walk-forward execution and one ordered child record per selected OOS window.
- Preserve effective configuration and bounded input provenance with versioned, deterministic checksum protocols.
- Persist the complete `wf_evidence_v1` aggregate shape, including the active/downside risk metrics introduced by the prerequisite Change.
- Expose current-strategy read-only history/detail APIs and dedicated Web pages linked through the complete OOS Backtest and Signal evidence chain.
- Keep persistence inside the existing caller-owned transaction so partial or failed executions leave no Walk-forward or OOS records.

**Non-Goals:**

- No persisted failed-attempt records, retry workflow or HTTP execution endpoint.
- No automatic deduplication/cache reuse, deletion/editing API or historical backfill.
- No Dashboard cards, composite score, automatic pass/fail or configurable decision thresholds.
- No continuous/linked OOS curve, cross-window drawdown or simulated boundary turnover.
- No full copy of every market-price input row and no guarantee of replay after the source database changes.
- No global SQLite `PRAGMA foreign_keys=ON` change and no guarantee against direct manual SQL mutation.

## Decisions

### Gate implementation on the two evidence prerequisites

`strengthen-walk-forward-evaluation-contract` defines the typed evidence summaries, rates, generalization gaps and parameter stability. `add-active-and-downside-risk-metrics` extends that same shape with Sortino, Calmar, longest drawdown duration and benchmark-keyed Tracking Error/Information Ratio. Apply begins only after both shapes and their complete-gate evidence are stable; the first implementation task rechecks their final code and specs before creating `wf_evidence_v1`.

### Use one parent plus normalized ordered window children

Add `WalkForwardRun` and `WalkForwardRunWindow` models. The parent stores `strategy_id`, typed configured start/end dates, validated WF/base-strategy JSON snapshots, `provenance_version`, configuration checksum, compact input manifest/checksum, `evidence_version`, validated aggregate evidence JSON, window count, started/finished timestamps and created timestamp. A composite `(strategy_id, finished_at, id)` index supports the only history ordering/filter path. Each child stores ordinal, train/test boundaries, OOS version, canonical selected parameters, candidate/eligible/skipped counts, normalized skip-reason counts, train Sharpe and one OOS backtest id.

Each child has a unique `(walk_forward_run_id, ordinal)` and unique `oos_backtest_run_id`. Non-negative count checks and `candidate_count = eligible_count + skipped_count` are enforced before persistence and with database check constraints. `window_count` is verified against the child collection before flush and on typed reads. Strategy and benchmark metrics remain owned by the referenced `BacktestRun`/`BacktestBenchmark` records rather than being duplicated into child columns.

Immutability is an application contract: there are no update/delete helpers or HTTP mutation routes. The schema declares its foreign keys and unique ownership, but the repository does not globally enable SQLite foreign-key enforcement. This Change therefore does not claim database-level delete restriction or cascade behavior against manual SQL. Downgrade explicitly drops the child table before the parent.

Alternative considered: store the complete report as opaque text or one unvalidated JSON blob. Rejected because list/filter/link queries and version compatibility would be unreliable. Alternative considered: enable SQLite foreign keys globally to enforce deletion behavior. Rejected here because it changes every existing relationship and may expose unrelated historical orphan data; that requires a separate database-integrity Change.

### Define one exact `wf_evidence_v1` document

The persisted evidence document is validated by the same Pydantic domain model used at persistence, query and HTTP response boundaries. Its exact top-level fields are:

- `metrics`: summaries keyed by `total_return`, `annualized_return`, `sharpe_ratio`, `max_drawdown`, `volatility`, `sortino_ratio`, `calmar_ratio` and `longest_drawdown_duration_sessions`.
- `positive_window_rate`: the strengthened report's positive OOS rate.
- `generalization_gap`: the `train_sharpe - oos_sharpe` summary.
- `benchmarks`: exactly `equal_weight_monthly` and `csi_300_buy_hold`; each owns `total_return_difference`, `annualized_return_difference`, `tracking_error`, `information_ratio` summaries and its `outperformance_rate`.
- `parameter_stability`: parameter-keyed canonical value frequencies, transition count, comparison count and nullable transition rate. Each value is resolved from the searched dot-path in the selected validated strategy configuration's JSON-mode data; raw parameter-generator Python representations are never used as the persisted value identity.

A metric summary contains JSON number-or-null `mean`, `median`, `min`, `max` and population `std`, plus integer `window_count`, integer `valid_count` and `evidence_status`. A rate contains integer `numerator`, integer `denominator`, JSON number-or-null `value`, the same counts and `evidence_status`. `evidence_status` remains `sufficient` only when at least three windows contribute a valid value and otherwise `insufficient_evidence`; it represents only that minimum-valid-count threshold and does not assert window independence, statistical adequacy or strategy validity. Aggregate JSON numbers retain the existing in-memory report semantics; Decimal metrics read from persisted Backtest/window columns are serialized by HTTP as strings or null, while longest-drawdown duration is an integer or null.

The parent stores `evidence_version = "wf_evidence_v1"` separately from the document. Unsupported versions or a document that fails validation raise a typed persisted-data contract error; the API returns the standard unexpected-error envelope and never a partial evidence response. A later shape requires a new version and compatibility reader.

### Snapshot effective configuration with `wf_provenance_v1`

Persist the complete validated `WalkForwardConfig.model_dump(mode="json")` and validated resolved base `StrategyConfig` snapshot for audit display. Source path strings may remain in these snapshots, but paths are not effective historical inputs and are excluded from configuration identity.

For `config_checksum`, construct exactly `{ "version": "wf_provenance_v1", "walk_forward": <validated WF snapshot without strategy.base_config>, "base_strategy": <validated base-strategy snapshot without universe_config> }`. Both removed values are source locators rather than calculation inputs: the current execution reads its active universe from `ETFInfo`, whose effective membership and identities are covered by the input manifest. Preserve declared parameter/value ordering because it is execution configuration. Serialize with UTF-8 `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` after converting dates to ISO strings, paths to display strings and Decimals to `str`; hash those exact bytes with SHA-256 and store the lowercase hexadecimal digest. Identical effective content at different source paths therefore compares equal, while any effective field change compares different.

### Capture a compact pre-execution input manifest and checksum

Before any source-side OOS write, generate and validate every candidate configuration, resolve its strategy-declared non-negative lookback, load `TradingCalendar` as the sole window/session axis, generate the final windows, and derive the maximum required lookback envelope. The runner MUST NOT derive windows from distinct `MarketPrice.trade_date` values or fall back between price and calendar sources. If no candidate validates, any lookback is invalid, the official-session envelope is incomplete, or required prices are incomplete, fail before creating source-side output.

`input_data_snapshot_json` has exactly these top-level fields: `version = "wf_provenance_v1"`, ISO `earliest_required_session`, ISO `configured_end_date`, ISO-or-null `following_session`, ordered ISO `official_sessions`, ordered `active_etfs`, integer `loaded_price_row_count`, and ISO-or-null `first_loaded_price_date`/`last_loaded_price_date`. Each `active_etfs` entry has exactly integer `etf_id`, string `exchange`/`symbol`, ISO-or-null `inception_date`, integer `loaded_price_row_count`, and ISO-or-null `first_loaded_price_date`/`last_loaded_price_date`; entries are ordered by `etf_id`. The local id mapping is execution-sensitive because the current strategy uses it for deterministic equal-score ordering; omitting it could assign one checksum to inputs capable of selecting different ETFs. The post-end following-session sentinel is included because equal-weight monthly benchmark behavior uses it to classify the last session; no post-end price is included because execution does not read one. The manifest duplicates no raw price-value array.

The input checksum is a streaming sequence of compact UTF-8 JSON array records, each followed by `"\n"`, in this exact group order:

1. `["version", "wf_provenance_v1"]`.
2. One `["etf", etf_id, exchange, symbol, inception_date_or_null]` per active ETF, ordered by `etf_id`.
3. One `["session", trade_date]` per manifest session, ordered ascending, followed by `["following_session", date_or_null]`.
4. One `["price", etf_id, exchange, symbol, trade_date, str(close_price), str(factor_hfq)]` per on/after-inception row in the actual loaded price panel from the earliest envelope date through configured end, ordered by `(etf_id, trade_date)`. This includes a stored non-official-date row because the current bounded strategy panel can observe it, although such a row does not expand the official completeness requirement.

Each record uses `json.dumps(..., separators=(",", ":"), ensure_ascii=False, allow_nan=False)`. Hash the concatenated bytes with SHA-256 and store the lowercase digest in the parent `input_data_checksum` column. The manifest intentionally does not duplicate all raw price values: it supports comparison and drift detection, while complete offline replay remains out of scope. Generated signals/backtests, unrelated output rows, pre-inception prices and prices after the configured end never contribute.

Alternative considered: checksum the complete SQLite file. Rejected because unrelated historical outputs and future appended data would change identity. Alternative considered: store all raw input rows. Rejected because it duplicates potentially large market datasets and diverges from the repository's compact Backtest snapshot pattern.

### Record bounded candidate selection evidence

For each window, `candidate_count` is the number of generated combinations. `eligible_count` is the number of successful training runs with non-null Sharpe. Every other candidate contributes exactly once to `skipped_count` and one fixed reason category: `invalid_config`, `training_error`, `training_non_success` or `missing_train_sharpe`. The persisted reason map contains only those keys with positive counts; its count sum equals `skipped_count`. The selected-parameter document resolves each searched dot-path from the selected validated strategy configuration's JSON-mode data and encodes that effective value canonically, matching `parameter_stability`; it does not preserve a potentially different raw generator representation. Raw exception text, tracebacks, parameter values and dynamic status strings are not stored in the reason map; operational logs may retain bounded diagnostic context under existing logging rules.

### Record only complete successes in the caller transaction

Capture the evaluation start time at runner entry. Build all window results and validated structured evidence, then insert and flush the parent and children at the end of `WalkForwardRunner.run` using the source session without committing. Capture finished time only after evidence validation and before persistence. The CLI's existing `managed_session` commits OOS backtests and WF records together. Any window, fixed benchmark, provenance, evidence-validation or persistence failure propagates and the caller rolls everything back.

Do not open a separate transaction to retain failed attempts. This honors the approved first-phase choice and avoids a failure-audit write surviving while its referenced OOS runs are rolled back.

### Provide exact read-only HTTP contracts

Add a dedicated Walk-forward router:

- `GET /api/walk-forwards?limit=&offset=` is always scoped to the configured `strategy_id`. `limit` defaults to 10 and is bounded to 1..100; `offset` defaults to 0 and is non-negative. It returns `{ "runs": [...], "total": int, "limit": int, "offset": int }` ordered by `finished_at DESC, id DESC`.
- Each summary exposes `run_id`, `strategy_id`, configured `start_date`/`end_date`, `window_count`, `provenance_version`, `evidence_version`, `config_checksum`, `input_data_checksum`, `started_at` and `finished_at`.
- `GET /api/walk-forwards/{run_id}` is also scoped to the configured strategy and returns top-level `run`, `configuration`, `input_provenance`, `evidence_version`, `evidence` and chronologically ordered `windows`. `configuration` is `{ "walk_forward": object, "base_strategy": object, "config_checksum": string }`; `input_provenance` is `{ "manifest": object, "input_data_checksum": string }`.
- Each detail window exposes `ordinal`, `train_start`, `train_end`, `test_start`, `test_end`, `oos_version`, `selected_parameters`, reconciled `candidate_count`, `eligible_count`, `skipped_count`, `skip_reason_counts`, Decimal-string/null `train_sharpe`, and an `oos_backtest` summary with its id, dates, seven Decimal-string/null strategy metrics, integer/null longest-drawdown duration and duration dates. Each fixed benchmark group uses the same absolute encodings plus Decimal-string/null Tracking Error and Information Ratio. It exposes no equity curve.

Unknown and other-strategy WF ids return the standard 404 envelope. Corrupt or unsupported persisted documents produce the standard unexpected-error response. There is no `strategyId` query and no POST/PATCH/DELETE operation.

### Make same-strategy historical evidence reachable by id

Modify existing Backtest Detail, Backtest Signals and Signal Detail by-id reads to scope by the configured `strategy_id` only, regardless of `config_version`. List/latest endpoints retain their current version-filtered behavior. This makes current-strategy historical versions and `wf-*` OOS evidence navigable without a WF-specific authorization branch; records from another strategy remain indistinguishable from missing ids.

Alternative considered: allow only backtests already linked to a WF parent. Rejected because it couples generic by-id endpoints to the new tables and still leaves their linked signals inconsistent. Alternative considered: create a separate OOS detail page. Rejected because it would duplicate the authoritative Backtest Detail surface.

### Add history and detail pages without a synthetic performance chart

Add lazy routes `/walk-forwards` and `/walk-forwards/:id` plus a navigation entry. History uses a fixed page size of 10 and shows execution id/time, strategy, configured interval, window count and compact provenance identifiers. Detail has sections for execution/provenance, evidence sufficiency and OOS summaries, all eight strategy evidence metrics, separate dual-benchmark return/TE/IR comparisons, IS/OOS gaps, parameter stability, and an ordered window table linking each OOS id to `/backtests/{id}`.

The OOS link must load the existing Backtest Detail for its `wf-*` version; its Signals tab and subsequent Signal Detail links must also remain usable. Do not render a continuous curve or cross-window path metric. Dashboard and existing Backtest presentation remain otherwise unchanged.

### Preserve current CLI report behavior

Attach the flushed parent id to the returned report/result. `vela walk-forward` prints `Walk-forward run id: <id>` only after `managed_session` exits successfully, in addition to the existing terminal evidence, and writes the same evidence to `--output`. A commit failure exits non-zero and prints no persisted id.

### Migrate without backfill

Create one Alembic revision for the two tables, typed/check columns, indexes, uniqueness constraints and foreign-key declarations. Existing OOS backtests remain readable and are not inferred or backfilled. Migration tests enable foreign-key enforcement only where they are explicitly testing declared FK behavior; application runtime behavior remains unchanged. Downgrade removes only the child then parent tables and preserves all backtest, signal, curve and benchmark data, including OOS rows formerly referenced by deleted WF children.

## Risks / Trade-offs

- [Prerequisite report shapes could still move] → block Apply until both prerequisite Changes have final gate/review evidence, then re-read their stable code/specs before defining the Pydantic model.
- [Checksums can become incomparable if serialization drifts] → store `wf_provenance_v1` and lock byte-exact fixed vectors, path independence and following-session behavior.
- [Compact provenance cannot replay deleted source prices] → state comparison/drift detection scope explicitly; full raw snapshots require a separate Change.
- [Evidence JSON could drift from its typed contract] → validate at persistence and read boundaries and fail closed on unknown versions.
- [A late persistence error could leave partial OOS rows] → use the existing caller transaction and exercise failures after earlier windows in file-backed SQLite tests.
- [SQLite does not enforce declared foreign keys by default] → make no deletion-protection claim, expose no delete API and defer global enforcement to a separate integrity Change.
- [Same-strategy cross-version reads broaden historical visibility] → retain current-strategy isolation and keep list/latest defaults version-scoped; this is intentional for local audit navigation.
- [Users may infer a continuous track record from ordered windows] → omit linked curves and label every section/window as independent OOS evidence.
- [Web scope can expand into a dashboard redesign] → use dedicated history/detail pages and preserve Dashboard/list/backtest surfaces.

## Migration Plan

1. Complete and independently verify `strengthen-walk-forward-evaluation-contract` and `add-active-and-downside-risk-metrics`; refresh the target Change against their final stable revision.
2. Lock `wf_provenance_v1`, `wf_evidence_v1`, skip categories and exact API schemas with fixed-vector/round-trip tests.
3. Add the parent/child tables and verify upgrade/downgrade on a file-backed SQLite database containing legacy and OOS backtests.
4. Add atomic runner persistence and CLI id output, then core queries and HTTP routes including same-strategy cross-version by-id access.
5. Add Web history/detail routes and verify the complete WF → OOS Backtest → Signal navigation chain.
6. Roll back Web/API consumers before downgrading; downgrade removes only WF child/parent tables and preserves all existing evidence owners.

## Open Questions

None. The access boundary, compact provenance, evidence schema, candidate categories, transaction behavior, SQLite deletion trade-off, read-only API, dedicated UI and no continuous OOS curve are approved.
