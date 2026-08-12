## MODIFIED Requirements

### Requirement: Per-ETF trading day gap detection
The system SHALL provide a pure, session-free ingestion-diagnostic function `detect_etf_trading_day_gaps` that compares each ETF's stored trading days against expected trading-calendar days and returns one warning per `(etf_id, trade_date)` gap, suppressing dates before a caller-supplied diagnostic boundary.

The function MUST accept `etf_actual_dates`, `expected_dates`, and `inception_boundaries`, and MUST return `EtfTradingDayGap` records sorted by `(etf_id, trade_date)`. A fetch caller MAY use `max(inception_date, first_stored_date)` to bound warnings to the locally observed fetch range. This diagnostic boundary and its warn-only result MUST NOT determine strategy, backtest, benchmark, or Walk-forward admissibility; execution uses authoritative `listing_date` and ETF session status and MUST fail on every unexplained required gap.

#### Scenario: Detect a per-ETF gap after diagnostic boundary
- **WHEN** the detector receives an ETF series missing a calendar day on or after its supplied boundary
- **THEN** it returns an `EtfTradingDayGap` for that ETF and date

#### Scenario: Suppress gaps before diagnostic boundary
- **WHEN** a missing calendar day falls before the supplied ingestion-diagnostic boundary
- **THEN** the detector does not return that gap

#### Scenario: No gaps when ETF covers diagnostic range
- **WHEN** an ETF covers every expected date on or after its supplied boundary
- **THEN** the detector returns no gap for that ETF

#### Scenario: Deterministic ordering across ETFs
- **WHEN** the detector finds multiple gaps across multiple ETFs
- **THEN** it returns warnings sorted by `(etf_id, trade_date)`

#### Scenario: Fetch boundary cannot authorize execution
- **WHEN** a first-stored-date boundary suppresses an ingestion warning for a post-listing truncated period
- **THEN** execution preflight still treats every required post-listing ETF/session without raw price or authoritative status as unresolved
