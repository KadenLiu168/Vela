## ADDED Requirements

### Requirement: Canonical ingestion-to-quant core contract validation

The repository SHALL include one canonical pytest workflow that exercises the real ingestion-to-quant core contracts against a temporary file-backed SQLite database using controlled external-source responses.

#### Scenario: Canonical workflow reaches persisted read models

- **WHEN** the canonical core pipeline test runs
- **THEN** it MUST initialize the temporary database exclusively through Alembic migration to head
- **AND** it MUST NOT call ORM `create_all` for the canonical database
- **AND** it MUST call the real ETF pool and trading-calendar synchronization services
- **AND** it MUST call the real full market-data fetch service with a controlled provider
- **AND** it MUST verify provider-shaped close prices and a non-unit factor are persisted at the model's declared precision
- **AND** it MUST call the real live signal service and real backtest runner without replacing strategy generation, equity calculation, or metric calculation
- **AND** it MUST read the persisted run through the backtest result service and Dashboard aggregation service

#### Scenario: Canonical stages exchange committed state

- **WHEN** the canonical workflow advances from migration through synchronization, fetch, signal, backtest, and readback
- **THEN** the engine and session factory MUST be created after Alembic migration completes
- **AND** each major service stage MUST finish through its existing production transaction boundary, using caller-managed sessions where the core service does not commit
- **AND** the next stage MUST use a fresh session to consume committed database state
- **AND** the test MUST NOT add commits inside core functions whose transaction is caller-managed

#### Scenario: Live and backtest signal branches remain distinct

- **WHEN** a manual signal is generated before the canonical backtest executes
- **THEN** the manual signal MUST remain unlinked to the backtest run
- **AND** the backtest MUST persist its own historical signals with `source="backtest"`
- **AND** the run's linked signal IDs and equity calculation MUST be scoped only to signals generated for that run

#### Scenario: Real reruns remain isolated

- **WHEN** the canonical workflow runs the same test-owned strategy and date range a second time through the real backtest runner
- **THEN** the two runs' linked signal ID sets MUST be disjoint
- **AND** the first run's persisted signals, equity curve, metrics, and data snapshot MUST remain unchanged
- **AND** the two runs' complete `data_snapshot_json` values, including `data_checksum`, MUST be equal because their persisted market inputs are equal
- **AND** both runs MUST remain independently readable

#### Scenario: Canonical assertions divide structural and arithmetic responsibilities

- **WHEN** the canonical workflow validates a successful backtest
- **THEN** it MUST assert deterministic selected identities, ranking and weight invariants, persisted linkage, result structure, and readback equality
- **AND** it MUST NOT replace the focused core tests responsible for exact momentum, trend, equity, cost, and performance-metric arithmetic

### Requirement: Network-independent backend workflow validation

Backend workflow tests SHALL remain deterministic and SHALL NOT require live Tencent or akshare access.

#### Scenario: Pytest workflow uses controlled source boundaries

- **WHEN** the canonical core or P0 API workflow runs under pytest
- **THEN** the workflow MUST inject a controlled market-data provider instead of constructing a real network provider
- **AND** trading-calendar synchronization MUST import an in-process fake `akshare` module whose fixed DataFrame response contains no network operation
- **AND** provider calls MUST be inspectable through their recorded symbol and date bounds
- **AND** no subprocess CLI fetch/calendar pipeline SHALL be required by this change

## MODIFIED Requirements

### Requirement: Full P0 workflow validation

The repository SHALL include automated pytest coverage for the COP-127 full P0 user workflow data-source loop. This API workflow SHALL complement the canonical core pipeline by validating transport delegation, serialization, persistence readback, and Dashboard linkage without duplicating focused financial arithmetic or the canonical core workflow's complete synchronization and rerun assertions.

#### Scenario: Pytest validates full P0 workflow loop

- **WHEN** a developer runs the API workflow tests through pytest
- **THEN** pytest MUST execute a test that reads Dashboard state, triggers market data fetch, triggers signal generation, triggers backtest execution, and reads backtest detail through real API endpoints
- **AND** the test MUST use deterministic SQLite data, a validated test-owned strategy configuration, controlled source responses, and existing backend workflows
- **AND** the test MUST verify follow-up API reads restore the persisted market data, signal, backtest, and detail state
- **AND** the test MUST verify serialized signal identities, ranks, and weights and production-shaped equity-curve `positions_json`
- **AND** the test MUST verify Dashboard state links to the generated fetch, the latest successful signal under production ordering, and the recent backtest run
- **AND** the earlier manual signal MUST remain independently readable and unlinked to the backtest

#### Scenario: P0 assertions remain transport-focused

- **WHEN** the P0 API workflow verifies a completed backtest
- **THEN** response metric values MUST match the corresponding persisted run values
- **AND** the workflow MUST retain unique HTTP status, response-shape, and read-after-write assertions
- **AND** trading-day and signal-count assertions MUST be derived from controlled official sessions and linked/detail collections rather than hardcoded natural-day counts or existence-only checks
- **AND** controlled provider request assertions MUST retain deterministic symbol ordering and include fixed start and end bounds
- **AND** it MUST NOT pin exact financial metric goldens or duplicate the canonical core workflow's full rerun-isolation proof
