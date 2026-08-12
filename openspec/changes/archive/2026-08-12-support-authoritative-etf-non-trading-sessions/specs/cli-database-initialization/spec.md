## ADDED Requirements

### Requirement: Synchronize ETF session-status reference data from CLI
The system SHALL provide `vela sync-etf-session-status` accepting a versioned session-status path and the existing explicit database target. It SHALL validate the complete document plus referenced persisted ETF/listing identities and atomically synchronize only authoritative full-day session statuses. Existing `sync-etf-pool` SHALL remain the sole CLI path for configured ETF inception/listing metadata. The status command SHALL report inserted, updated, and unchanged counts and SHALL exit non-zero without partial writes on failure.

#### Scenario: Synchronize into explicitly selected database
- **WHEN** the user supplies a valid status document and `--database-url` for an initialized SQLite database whose referenced ETFs have listing metadata
- **THEN** the command synchronizes only statuses in that selected database
- **AND** prints deterministic inserted, updated, and unchanged counts

#### Scenario: Invalid reference file fails atomically
- **WHEN** any status entry is invalid, references missing listing metadata, or conflicts with a raw market price
- **THEN** the command exits non-zero with actionable context
- **AND** commits no status change from that invocation

#### Scenario: ETF pool sync owns listing metadata
- **WHEN** the user runs the existing ETF-pool synchronization with configured listing dates
- **THEN** it synchronizes ETF inception/listing fields without reading or mutating session-status entries

#### Scenario: Tests never target repository database
- **WHEN** CLI synchronization is exercised by automated tests
- **THEN** every test uses a test-owned file-backed SQLite database
- **AND** no test targets the repository `vela.db`
