## ADDED Requirements

### Requirement: ETF temporal reference schema migration
The system SHALL provide an Alembic migration that adds nullable `ETFInfo.listing_date` and creates `etf_session_status` with a unique `(etf_id, trade_date)` identity, supported-status check constraint, required source fields, optional positive share ratio, timestamps, foreign-key ownership, and query indexes. The migration SHALL preserve all existing ETF, market-price, signal, backtest, benchmark, and Walk-forward rows and SHALL NOT guess listing dates or status events.

#### Scenario: Upgrade populated legacy SQLite database
- **WHEN** a file-backed SQLite database at the prior revision contains existing research history and is upgraded
- **THEN** every existing row and relationship is preserved
- **AND** existing ETFs have null listing dates until explicit reference-data synchronization
- **AND** the new status table is empty

#### Scenario: Enforce status constraints
- **WHEN** the migrated database receives an unsupported status, duplicate ETF/date, missing source field, or non-positive share ratio
- **THEN** the database rejects the invalid row

#### Scenario: Downgrade preserves pre-change data
- **WHEN** a migrated test database with no required new-policy execution is downgraded
- **THEN** the new table and listing column are removed
- **AND** all pre-change ETF and research rows retain their original values
