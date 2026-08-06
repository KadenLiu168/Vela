# walk-forward-evaluation-history Specification

## Purpose
Define the durable, immutable, provenance-bearing history of successful Walk-forward evaluations and their ordered OOS windows.
## Requirements
### Requirement: Persist successful Walk-forward runs and ordered windows
The system SHALL persist one logically immutable `WalkForwardRun` only after every configured window and structured evidence calculation succeeds, with one ordered child per selected OOS window, unique parent ordinal and unique `BacktestRun` ownership. Strategy and benchmark metrics remain owned by referenced OOS records; no update/delete helper or HTTP mutation route is exposed.

#### Scenario: Complete run creates ordered children
- **WHEN** a Walk-forward execution completes successfully
- **THEN** one parent and one ordered child per selected OOS window are persisted

### Requirement: Configuration provenance uses an exact versioned identity
The parent SHALL persist the exact versioned configuration/provenance document and SHA-256 identity. Display paths MAY be retained, but SHALL NOT affect the effective configuration checksum; equal effective inputs produce equal checksums and repeated executions receive distinct run identities.

#### Scenario: Display path does not change identity
- **WHEN** equal effective configuration is loaded from different source paths
- **THEN** the effective configuration checksum is equal

### Requirement: Input provenance is a compact bounded manifest
The manifest SHALL retain bounded ETF local ids, canonical identities, inception dates, official-session sequence, following-session sentinel, loaded-price counts/bounds and checksum metadata without copying the full raw price table.

#### Scenario: Manifest excludes raw price table
- **WHEN** input provenance is persisted
- **THEN** it contains bounded manifest data and no full raw price-value array

### Requirement: Input checksum covers every effective database input
The input checksum SHALL cover execution-sensitive ETF-id mappings and strategy-visible `close_price`/`factor_hfq` rows, include observable non-official rows, and exclude output rows, pre-inception rows and future-price rows.

#### Scenario: Effective input drift changes checksum
- **WHEN** an execution-sensitive input row changes
- **THEN** the input checksum changes

### Requirement: Versioned evidence round-trips without semantic loss
Persisted `wf_evidence_v1` SHALL validate at persistence, query and API boundaries and preserve all eight strategy summaries, rates, benchmark return/Tracking Error/Information Ratio groups, generalization gap and parameter stability. Unsupported versions or corrupt documents SHALL fail closed.

#### Scenario: Corrupt evidence fails closed
- **WHEN** a persisted evidence document has an unsupported version or invalid shape
- **THEN** typed reads raise a persisted-data contract error and return no partial evidence

### Requirement: Window selection evidence is bounded and reconciled
Each child SHALL persist boundaries, selected canonical parameters, candidate/eligible/skipped counts, fixed skip-reason counts, train Sharpe and OOS id. Counts and reasons SHALL reconcile; raw exception text, tracebacks, candidates and dynamic status strings MUST NOT be stored.

#### Scenario: Candidate counts reconcile
- **WHEN** candidates are skipped during selection
- **THEN** candidate count equals eligible plus skipped and reason counts equal skipped

### Requirement: Failed Walk-forward executions leave no history
Parent, children, selected OOS backtests and benchmarks SHALL share the caller-owned transaction. Any execution, provenance, evidence or persistence failure SHALL roll back all source-side artifacts and return no persisted identity.

#### Scenario: Late failure rolls back all artifacts
- **WHEN** a later window or final persistence step fails
- **THEN** no parent, child, OOS, signal, curve or benchmark from the command is committed

### Requirement: Query immutable Walk-forward history
Queries SHALL return current-strategy summaries ordered by `finished_at DESC, id DESC`, exact totals, bounded pagination and chronological eager-loaded children. Unknown or other-strategy ids return no result; legacy OOS runs do not fabricate history.

#### Scenario: Empty legacy history stays empty
- **WHEN** an upgraded database has OOS runs but no WF parent
- **THEN** history returns an empty collection and zero total

### Requirement: Walk-forward history migration is non-destructive
The Alembic revision SHALL create only the WF parent/child tables, typed columns, checks, unique constraints, history index and foreign keys. It SHALL not backfill or alter existing backtest data; downgrade drops child before parent and preserves evidence owners.

#### Scenario: Migration preserves existing owners
- **WHEN** the WF revision is upgraded and downgraded around existing OOS data
- **THEN** pre-existing backtest, signal, curve and benchmark rows remain unchanged

### Requirement: Versioned history preserves benchmark-regime evidence
Newly persisted Walk-forward histories SHALL store `wf_evidence_v2`, containing all valid `wf_evidence_v1` content plus per-benchmark daily CAPM/monthly-capture aggregates and per-window daily-session or selected-month evidence counts defined by this Change. Persistence, query, and API boundaries SHALL validate `v2` strictly, continue to support legacy `v1`, and fail closed on unsupported versions, missing benchmark ownership, or corrupt metric/count relationships.

#### Scenario: New history round-trips v2 evidence
- **WHEN** a completed Walk-forward run with benchmark-regime metrics is persisted and queried in a fresh session
- **THEN** its `wf_evidence_v2` document round-trips every new aggregate, count, null, and evidence status
- **AND** referenced OOS benchmark rows retain the matching per-window source values

#### Scenario: Legacy v1 history remains readable
- **WHEN** a valid pre-change `wf_evidence_v1` history is queried
- **THEN** existing evidence remains readable
- **AND** no CAPM or capture value is fabricated

#### Scenario: Corrupt v2 history fails closed
- **WHEN** a `wf_evidence_v2` document has an unsupported benchmark key, invalid count, non-finite value, or source ownership mismatch
- **THEN** persistence or query rejects the complete history instead of returning partial evidence

### Requirement: Versioned history preserves tail-distribution evidence
After `add-benchmark-regime-performance-metrics`, newly persisted Walk-forward histories SHALL store `wf_evidence_v3`, containing all valid `wf_evidence_v2` content plus per-window and aggregate strategy/fixed-benchmark distribution metrics, counts, and evidence statuses. Persistence, query, and API SHALL validate v3 strictly, continue to support valid legacy v1/v2, and reject unsupported/corrupt documents without partial output.

#### Scenario: New v3 history round-trips source-owned evidence
- **WHEN** a completed Walk-forward run with distribution metrics is persisted and queried in a fresh session
- **THEN** every v3 value, null, count, status, benchmark key, and aggregate round-trips exactly
- **AND** referenced OOS records retain matching source fields

#### Scenario: Legacy v1 and v2 remain readable
- **WHEN** a valid earlier evidence document is queried
- **THEN** all evidence defined by that version remains readable
- **AND** no distribution metric or count is fabricated

#### Scenario: Corrupt v3 fails closed
- **WHEN** v3 contains an invalid version, owner, benchmark key, count relationship, non-finite value, loss invariant, or mismatch with referenced OOS fields
- **THEN** persistence or query rejects the complete history

