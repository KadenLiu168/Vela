## ADDED Requirements

### Requirement: Persist strategy signal records provenance

The core `persist_strategy_signal` helper SHALL require a `source` argument for every persisted signal and SHALL accept an optional `backtest_run_id`. The helper SHALL write both values onto the `strategy_signal` row.

#### Scenario: Live signal persisted with source
- **WHEN** the live generation path persists a signal with `source="manual"` or `source="scheduled"`
- **THEN** the persisted row's `source` equals the supplied value
- **AND** the persisted row's `backtest_run_id` is null

#### Scenario: Backtest signal persisted with source and run id
- **WHEN** the backtest generation path persists each signal with `source="backtest"` and `backtest_run_id=None`, then links them to the run
- **THEN** each linked signal row's `source` equals `backtest`
- **AND** each linked signal row's `backtest_run_id` equals the producing `backtest_run.id`

#### Scenario: Caller must supply source
- **WHEN** backend code calls `persist_strategy_signal` without a `source`
- **THEN** the call fails at the persistence layer (the parameter is required)

### Requirement: Live generation accepts a caller-supplied source

The core live generation service SHALL accept a `source` argument (default `manual`) and pass it through to persistence. The HTTP generate endpoint and CLI SHALL forward an optional caller-supplied `source` (restricted to `manual` or `scheduled`) and default to `manual` when omitted.

#### Scenario: Default live source is manual
- **WHEN** backend code generates a live signal without specifying `source`
- **THEN** the persisted signal's `source` is `manual`

#### Scenario: Scheduled live source is recorded
- **WHEN** an automated caller requests live signal generation with `source="scheduled"`
- **THEN** the persisted signal's `source` is `scheduled`
- **AND** no scheduler or automation engine is created by this requirement

#### Scenario: Live endpoint rejects backtest source
- **WHEN** a client requests live signal generation with `source="backtest"`
- **THEN** the endpoint rejects the request (HTTP 400) because `backtest` is reserved for backtest runs

#### Scenario: Core live service rejects non-live source
- **WHEN** backend code calls the live generation service with `source="backtest"`, `source="legacy"`, or an unknown value
- **THEN** the service raises before persisting a signal

### Requirement: Backtest run links its signals

`run_backtest` SHALL capture every `strategy_signal_id` it produces; each signal SHALL be persisted up front with `source="backtest"` and `backtest_run_id=None`, and after the `backtest_run` row is created, exactly those captured signals SHALL have their `backtest_run_id` set to that run id (and no other signal's) before the caller-managed transaction commits.

#### Scenario: Every signal from a run is linked
- **WHEN** a backtest run completes and persists signals across its rebalance dates
- **THEN** each of those signal rows has `backtest_run_id` equal to the run id
- **AND** each has `source="backtest"`
- **AND** no signal outside the run receives that `backtest_run_id`

#### Scenario: Link helper is testable in isolation
- **WHEN** a core helper links a set of signal ids to a run id
- **THEN** it updates only distinct supplied ids that are unlinked and already have `source="backtest"`
- **AND** it verifies that the affected-row count equals the number of distinct supplied ids
- **AND** it raises on a missing, non-backtest, or already-linked id instead of accepting a partial link

#### Scenario: Empty link input is a no-op
- **WHEN** the link helper receives no signal ids
- **THEN** it performs no update and returns without error

#### Scenario: Missing persisted id does not commit partial provenance
- **WHEN** any historical generation result unexpectedly has a null `strategy_signal_id`
- **THEN** `run_backtest` raises before commit
- **AND** callers using the managed session boundary roll back the run and its signals
