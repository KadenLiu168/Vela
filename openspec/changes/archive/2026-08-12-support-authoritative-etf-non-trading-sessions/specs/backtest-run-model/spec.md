## MODIFIED Requirements

### Requirement: Backtest run data snapshot
The system SHALL persist a versioned `data_snapshot_json` for each new backtest run that fingerprints every effective resolved research input. New status-aware runs SHALL use `backtest_input_v2`; legacy snapshots remain nullable/readable and SHALL NOT be rewritten. The v2 document MUST include ordered official sessions, ETF id/exchange/symbol, fund inception and listing dates, raw price records, authoritative non-trading evidence, derived carried adjusted values, resolution policy version, per-source counts/bounds, and one lowercase SHA-256 checksum over a canonical compact record stream.

#### Scenario: New run persists v2 snapshot
- **WHEN** a status-aware backtest creates a run
- **THEN** its snapshot declares `backtest_input_v2`
- **AND** reconciles ordered sessions, ETF metadata, raw counts, derived counts, bounds, and checksum

#### Scenario: Checksum covers raw price drift
- **WHEN** an effective raw `close_price` or `factor_hfq` changes between otherwise equal runs
- **THEN** their checksums differ

#### Scenario: Checksum covers temporal evidence drift
- **WHEN** effective listing date, status, reason, source, share ratio, or carried adjusted value changes
- **THEN** the checksum changes even when raw prices are unchanged

#### Scenario: Identical effective inputs are stable
- **WHEN** two runs receive identical ordered sessions, metadata, raw prices, status evidence, and policy version
- **THEN** their canonical checksums are equal

#### Scenario: Legacy snapshot remains readable
- **WHEN** a pre-v2 run has the legacy snapshot shape or null snapshot
- **THEN** queries preserve it without fabrication or reinterpretation as status-aware evidence

#### Scenario: Partial-status run records attempted inputs
- **WHEN** some signal outputs are expected failures but a backtest run is persisted as partial
- **THEN** its v2 snapshot still fingerprints the complete resolved input used by the attempt

#### Scenario: Snapshot covers loaded execution envelope
- **WHEN** v2 snapshot construction receives a resolved panel
- **THEN** its bounds and counts cover the exact loaded lookback/requested envelope
- **AND** include every listed active ETF and every status-backed session in that envelope

#### Scenario: Snapshot does not leak future points
- **WHEN** the outer panel includes points after one historical signal date
- **THEN** that signal still receives only bounded points on or before its date

#### Scenario: Invalid v2 reconciliation fails
- **WHEN** counts, bounds, ordering, source-state exclusivity, carry ancestry, or checksum do not reconcile
- **THEN** persistence/query validation fails closed
