# etf-session-status Specification

## Purpose
Defines authoritative ETF session-status evidence, deterministic resolution of confirmed non-trading sessions, and atomic reference-data synchronization contracts.

## Requirements

### Requirement: Persist authoritative ETF non-trading session evidence
The system SHALL persist only exceptional full-day ETF non-trading states in an `etf_session_status` table keyed uniquely by `(etf_id, trade_date)`. Each row MUST use status `full_day_suspension` or `corporate_action_halt`, contain a bounded stable reason, authoritative `source_uri`, `source_published_date`, and MAY contain a positive `share_ratio`. A status row SHALL NOT represent a normal trading session or a synthetic market price.

#### Scenario: Store reviewed full-day status
- **WHEN** a validated reference entry identifies one ETF and official session as a confirmed full-day suspension or corporate-action halt
- **THEN** synchronization persists exactly one status row with its reason and source evidence
- **AND** it does not create a `MarketPrice` row for that session

#### Scenario: Reject incomplete evidence
- **WHEN** a status entry has an unsupported status, missing reason/source metadata, or a non-positive supplied share ratio
- **THEN** validation fails before any reference-data row is written

#### Scenario: Reject duplicate status identity
- **WHEN** the reference data contains two entries for the same ETF and trade date
- **THEN** validation fails instead of choosing one entry by file order

### Requirement: Synchronize versioned ETF session reference data atomically
The system SHALL validate the complete versioned ETF session-status document and every referenced persisted ETF/listing identity before synchronizing session statuses. Synchronization SHALL be idempotent, SHALL update only status fields owned by that document, SHALL report inserted, updated, and unchanged counts, and SHALL leave transaction commit or rollback to the caller. Listing metadata SHALL remain owned by ETF-pool synchronization.

#### Scenario: Repeat unchanged synchronization
- **WHEN** the same validated reference document is synchronized twice
- **THEN** the second synchronization changes no ETF or status row
- **AND** it reports those records as unchanged

#### Scenario: Validation failure writes nothing
- **WHEN** any session-status entry or referenced persisted ETF/listing identity is invalid
- **THEN** synchronization writes neither the valid entries nor the invalid entry

#### Scenario: Preserve unrelated rows
- **WHEN** the selected database contains an ETF or session-status row outside the synchronized document
- **THEN** synchronization does not delete or deactivate that row

### Requirement: Resolve complete strategy-session inputs
The system SHALL resolve each listed active ETF and required ordered official session to exactly one `ResolvedSessionPrice`. A raw `MarketPrice` SHALL resolve to `adjusted_value = close_price * factor_hfq` with `tradable = true` and resolution `market_price`. An authoritative full-day status without a raw price SHALL copy the immediately preceding resolved adjusted value with `tradable = false` and resolution `confirmed_non_trading_carry`. The resolver MUST retain `Decimal` precision and MUST NOT persist derived values as raw market data.

#### Scenario: Resolve a raw market observation
- **WHEN** a listed ETF has exactly one raw price on a required official session and no full-day status
- **THEN** the resolved point is tradable and its adjusted value equals `close_price * factor_hfq`

#### Scenario: Resolve a confirmed full-day non-trading session
- **WHEN** a listed ETF has a supported authoritative status, no raw price, and a preceding resolved value
- **THEN** the resolved point is non-tradable and carries that preceding adjusted value exactly
- **AND** it retains the status reason and source evidence

#### Scenario: Resolve consecutive confirmed non-trading sessions
- **WHEN** two or more consecutive required sessions have authoritative full-day statuses after one real resolved value
- **THEN** every such session carries the same adjusted value and remains non-tradable

#### Scenario: Reject unexplained required gap
- **WHEN** a listed ETF has neither raw price nor authoritative status on a required official session
- **THEN** resolution fails with the ETF and date
- **AND** it does not infer suspension from neighboring data

#### Scenario: Reject contradictory source states
- **WHEN** the same ETF/session has both a raw price and a full-day non-trading status
- **THEN** resolution fails as contradictory evidence

#### Scenario: Reject a carry without anchor
- **WHEN** the first required listed session has a non-trading status but no preceding resolved real value
- **THEN** resolution fails instead of inventing an initial valuation

### Requirement: Report unresolved session inputs deterministically
The resolver SHALL categorize invalid inputs as missing listing metadata, unexplained ETF/session gap, raw/status conflict, or missing carry anchor. It SHALL report exact category totals and a deterministic sorted bounded sample containing actionable ETF/date context.

#### Scenario: Multiple failures produce one bounded summary
- **WHEN** resolution finds invalid inputs across multiple ETFs and sessions
- **THEN** the error reports every category count
- **AND** its bounded sample is sorted by category, ETF id, and trade date rather than exposing only the first gap
