## ADDED Requirements

### Requirement: ETF metadata synchronization from configured pool
The system SHALL synchronize validated ETF pool entries into persisted `ETFInfo` rows.

#### Scenario: Insert configured ETF metadata
- **WHEN** ETF pool synchronization runs against a database missing a configured `(exchange, symbol)` row
- **THEN** the system inserts an `ETFInfo` row for that configured ETF

#### Scenario: Update configured ETF metadata
- **WHEN** ETF pool synchronization runs and a configured `(exchange, symbol)` row already exists with different YAML-owned metadata
- **THEN** the system updates the persisted `name`, `currency`, `category`, and `is_active` values from the ETF pool entry

#### Scenario: Keep synchronization idempotent
- **WHEN** ETF pool synchronization runs more than once with unchanged ETF pool configuration
- **THEN** subsequent runs leave the existing ETF rows unchanged and report them as unchanged

#### Scenario: Preserve rows outside configured pool
- **WHEN** ETF pool synchronization runs and the database contains ETF rows not present in the configured pool
- **THEN** the system does not delete or automatically deactivate those rows
