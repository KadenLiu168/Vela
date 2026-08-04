## ADDED Requirements

### Requirement: Persist successful Walk-forward runs and ordered windows
The system SHALL persist one logically immutable `WalkForwardRun` only after every configured window and structured evidence calculation succeeds. It SHALL persist one ordered child per selected OOS window with unique parent ordinal and unique `BacktestRun` ownership. The parent SHALL store typed configured start/end dates and window count; strategy and benchmark metrics MUST remain owned by the referenced OOS backtest records rather than being duplicated into window metric columns. The application SHALL expose no update or delete helper or HTTP mutation route for this history.

#### Scenario: Complete run creates one parent and ordered children
- **WHEN** a Walk-forward execution completes three windows successfully
- **THEN** one parent and three children are added in chronological ordinal order
- **AND** every child references its selected persisted OOS backtest
- **AND** the parent window count equals its child count

#### Scenario: Repeated execution creates distinct history
- **WHEN** the same effective configuration and input data are executed successfully twice
- **THEN** two distinct parent ids and distinct OOS run ids are persisted
- **AND** their equal configuration and input checksums remain comparable

#### Scenario: History exposes no mutation operation
- **WHEN** an application caller inspects core history helpers and HTTP routes
- **THEN** it finds read operations only
- **AND** no application operation edits or deletes a persisted evaluation

### Requirement: Configuration provenance uses an exact versioned identity
Each parent SHALL store the complete validated Walk-forward and resolved base-strategy configuration snapshots, `provenance_version = "wf_provenance_v1"`, and a lowercase SHA-256 `config_checksum`. The checksum payload SHALL be exactly `{ "version": "wf_provenance_v1", "walk_forward": <validated WF snapshot without strategy.base_config>, "base_strategy": <validated base-strategy snapshot without universe_config> }`. It SHALL serialize exact UTF-8 bytes with sorted object keys, compact separators, preserved array order, Unicode characters unescaped, non-finite numbers rejected, dates as ISO strings and Decimals as strings. Saved source paths are display metadata and MUST NOT affect the checksum.

#### Scenario: Same content at different paths has one identity
- **WHEN** identical validated WF and base-strategy content is loaded from different filesystem paths
- **THEN** both parents may retain different display paths
- **AND** their configuration checksums are identical

#### Scenario: Effective content changes identity
- **WHEN** any non-path WF or base-strategy field changes while source paths remain the same
- **THEN** the later run stores the changed validated content
- **AND** has a different configuration checksum

#### Scenario: Fixed-vector bytes remain stable
- **WHEN** a controlled configuration payload is canonicalized under `wf_provenance_v1`
- **THEN** its exact UTF-8 byte sequence and lowercase SHA-256 digest match the specified fixed vector

### Requirement: Input provenance is a compact bounded manifest
Before any source-side OOS write, the system SHALL validate every generated candidate, derive the maximum non-negative strategy lookback across valid candidates, generate the final windows, and build an `input_data_snapshot_json` manifest. Its exact top-level fields SHALL be `version`, `earliest_required_session`, `configured_end_date`, `following_session`, `official_sessions`, `active_etfs`, `loaded_price_row_count`, `first_loaded_price_date` and `last_loaded_price_date`. Date values SHALL be ISO strings or null where declared; `official_sessions` SHALL be the complete ordered sequence through the configured end. Each `active_etfs` item SHALL contain exactly integer `etf_id`, string `exchange` and `symbol`, ISO-string-or-null `inception_date`, integer `loaded_price_row_count`, and ISO-string-or-null `first_loaded_price_date` and `last_loaded_price_date`, ordered by `etf_id`. The local ETF id mapping SHALL be retained because current equal-score selection ordering can observe it. The manifest SHALL NOT duplicate complete raw price values.

#### Scenario: No valid candidate blocks source output
- **WHEN** no generated candidate validates or any valid candidate has an invalid negative lookback
- **THEN** provenance preparation fails before any OOS signal, run, curve or benchmark is added to the source session

#### Scenario: Manifest includes benchmark boundary sentinel
- **WHEN** an official session exists after the configured end date
- **THEN** the manifest records the first such session for the equal-weight benchmark's final month-boundary decision
- **AND** it records no price after the configured end date

#### Scenario: Manifest remains compact
- **WHEN** thousands of required price rows contribute to one evaluation
- **THEN** the manifest stores identities, sessions, counts, bounds and checksum metadata
- **AND** does not store an array containing every raw price value

#### Scenario: ETF with no loaded row remains explicit
- **WHEN** an active ETF's inception is after the configured end and no row enters the loaded envelope
- **THEN** its manifest entry has row count zero and null first/last loaded dates
- **AND** the ETF remains present in the ordered active-universe snapshot

### Requirement: Input checksum covers every effective database input
The parent SHALL store a lowercase SHA-256 `input_data_checksum` over newline-terminated compact UTF-8 JSON array records. The record stream SHALL contain, in order, the version record; `["etf", etf_id, exchange, symbol, inception_date_or_null]` records ordered by `etf_id`; official-session records ordered by date plus one following-session record; and `["price", etf_id, exchange, symbol, trade_date, str(close_price), str(factor_hfq)]` for every on/after-inception row in the actual loaded price panel through configured end, ordered by `(etf_id, trade_date)`. All dates SHALL use ISO format. A loaded non-official-date row SHALL contribute because the bounded strategy panel can observe it, but it SHALL NOT expand the official completeness requirement. Each record SHALL use compact separators, unescaped Unicode and reject non-finite values. Generated outputs, unrelated output rows, pre-inception prices and future prices MUST NOT contribute.

#### Scenario: Unrelated outputs do not change input identity
- **WHEN** prior signals, backtest rows or WF history differ but all bounded ETF, calendar and market inputs are identical
- **THEN** the input-data checksum remains identical

#### Scenario: Relevant inputs change identity
- **WHEN** an active ETF id mapping, identity/inception value, covered official-session sequence, following-session sentinel, required close price or required factor changes
- **THEN** the input-data checksum changes

#### Scenario: Future and pre-inception prices are excluded
- **WHEN** stored prices exist after the configured end date or before an ETF's declared inception date
- **THEN** those rows do not contribute to the input manifest or checksum

#### Scenario: Loaded non-official row remains fingerprinted
- **WHEN** an on/after-inception non-official-date price row is present inside the loaded envelope
- **THEN** it contributes to the price count and checksum because the strategy panel can observe it
- **AND** it does not become an official required session

#### Scenario: Input fixed vector is stable
- **WHEN** controlled ETF, calendar and price records are encoded under `wf_provenance_v1`
- **THEN** the exact newline-delimited bytes and lowercase SHA-256 digest match the specified fixed vector

### Requirement: Versioned evidence round-trips without semantic loss
Each parent SHALL store `evidence_version = "wf_evidence_v1"` and evidence validated by one typed domain schema at persistence and read boundaries. The document SHALL contain strategy summaries for `total_return`, `annualized_return`, `sharpe_ratio`, `max_drawdown`, `volatility`, `sortino_ratio`, `calmar_ratio` and `longest_drawdown_duration_sessions`; positive-window rate; `train_sharpe - oos_sharpe` summary; parameter stability; and separate `equal_weight_monthly`/`csi_300_buy_hold` return-difference, Tracking Error, Information Ratio and outperformance evidence.

Every metric summary SHALL contain JSON number-or-null `mean`, `median`, `min`, `max`, population `std`, integer `window_count`, integer `valid_count` and `evidence_status`. Every rate SHALL contain integer `numerator`, integer `denominator`, JSON number-or-null `value`, the same counts and `evidence_status`. Parameter stability SHALL resolve every searched dot-path from the selected validated strategy configuration's JSON-mode data and retain frequencies keyed by that effective value's canonical JSON, transition count, comparison count and nullable transition rate; raw parameter-generator Python representations MUST NOT define value identity. Evidence status SHALL be `sufficient` only when at least three windows contribute a valid value and otherwise `insufficient_evidence`; it represents only that minimum-valid-count threshold and MUST NOT imply window independence, statistical adequacy or strategy validity. The document MUST NOT add a composite score or pass/fail field.

#### Scenario: Complete evidence survives persistence
- **WHEN** a completed parent is reloaded
- **THEN** its evidence validates as `wf_evidence_v1`
- **AND** preserves all eight strategy metric summaries, rates, both benchmark groups, generalization gap and parameter stability

#### Scenario: Metric-local null semantics survive persistence
- **WHEN** one OOS metric or benchmark-relative value is null in some windows
- **THEN** only that metric's valid count excludes those windows
- **AND** its persisted summary and evidence status equal the generated report

#### Scenario: Unsupported or corrupt evidence fails closed
- **WHEN** a persisted parent has an unsupported evidence version or a document that fails its declared schema
- **THEN** the typed query raises a persisted-data contract error
- **AND** does not return a partial or silently defaulted evidence document

### Requirement: Window selection evidence is bounded and reconciled
Each window child SHALL retain train/test boundaries, OOS version, canonical selected parameters, `candidate_count`, `eligible_count`, `skipped_count`, normalized `skip_reason_counts`, train Sharpe and OOS backtest id. Every selected parameter SHALL be resolved from its searched dot-path in the selected validated strategy configuration's JSON-mode data and canonically encoded using the same effective-value identity as parameter stability, not the raw parameter-generator Python representation. Candidate count SHALL equal eligible plus skipped count; reason counts SHALL sum to skipped count. The only persisted reason keys SHALL be `invalid_config`, `training_error`, `training_non_success` and `missing_train_sharpe`. Raw exception messages, tracebacks, candidate parameters and dynamic status strings MUST NOT be stored in the reason map.

#### Scenario: Invalid and unscorable candidates reconcile
- **WHEN** one window generates candidates that fail validation, raise, return non-success or have null Sharpe
- **THEN** each skipped candidate contributes once to its fixed reason category
- **AND** candidate count equals eligible plus skipped count
- **AND** all reason counts sum to skipped count

#### Scenario: Raw failure text is not persisted
- **WHEN** a training candidate raises a multiline exception containing dynamic values
- **THEN** the child stores only `training_error` and its count
- **AND** stores no exception line, traceback or candidate payload in `skip_reason_counts`

### Requirement: Failed Walk-forward executions leave no history
Walk-forward parent and child writes SHALL participate in the same caller-owned transaction as selected OOS backtests and benchmarks. Any window, fixed benchmark, provenance, evidence-validation or persistence failure MUST roll back every source-side artifact from the command. The runner MUST NOT commit or roll back the caller session, and the first persistence phase MUST NOT open a separate transaction to retain a failed-attempt record.

#### Scenario: Late window failure rolls back earlier work
- **WHEN** a later window fails after earlier OOS rows have been added
- **THEN** no parent, child, OOS run, signal, strategy curve or benchmark from that command is committed

#### Scenario: Parent persistence failure rolls back OOS runs
- **WHEN** all windows finish but parent or child validation/flush fails
- **THEN** the caller transaction commits neither WF history nor its selected OOS backtests

#### Scenario: Commit failure produces no durable identity
- **WHEN** the runner flushes a parent id but the caller-managed commit fails
- **THEN** no WF or OOS artifact is durable
- **AND** the command does not claim that the id was persisted

### Requirement: Query immutable Walk-forward history
Core query helpers SHALL return current-strategy summaries ordered by `finished_at` descending then id descending, an exact filtered total, and one detail with chronologically ordered children and eagerly loaded OOS strategy/benchmark metrics. List pagination SHALL require `limit` 1 through 100 and non-negative offset. Unknown or other-strategy ids SHALL return no result. Existing OOS runs created before this model SHALL remain readable without an inferred parent.

#### Scenario: Stable page and total use one strategy scope
- **WHEN** current-strategy and other-strategy parents share timestamps
- **THEN** list/count return only current-strategy parents in stable newest-first order
- **AND** the total is exact before limit/offset are applied

#### Scenario: Empty legacy database has no fabricated history
- **WHEN** an upgraded database contains OOS backtests but no Walk-forward parent rows
- **THEN** the history query returns an empty collection and zero total

#### Scenario: Detail preserves OOS ownership
- **WHEN** one persisted WF detail is loaded
- **THEN** every window exposes exactly its referenced OOS backtest and both fixed benchmark values
- **AND** no unrelated backtest or equity curve is included

### Requirement: Walk-forward history migration is non-destructive
The Alembic revision SHALL create only the WF parent/child tables, typed columns, check/unique constraints, a `(strategy_id, finished_at, id)` history index and foreign-key declarations without modifying or backfilling existing backtest rows. It SHALL make no claim that the application globally enforces SQLite foreign keys. Downgrade SHALL drop the child table before the parent and preserve all existing backtest data, including OOS runs previously referenced by WF children.

#### Scenario: File-backed migration round trip preserves evidence owners
- **WHEN** a database with legacy and selected OOS backtests upgrades, receives valid WF parent/children, and downgrades the WF history revision
- **THEN** all pre-existing and referenced backtest, signal, curve and benchmark rows remain unchanged
- **AND** no history is fabricated during upgrade

#### Scenario: Declared uniqueness and checks reject invalid rows
- **WHEN** an enforcement-enabled migration test inserts a missing OOS reference, duplicate parent ordinal, duplicate OOS ownership, negative count or unreconciled count row
- **THEN** the database rejects the invalid child row
