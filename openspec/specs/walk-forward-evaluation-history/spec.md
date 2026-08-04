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
