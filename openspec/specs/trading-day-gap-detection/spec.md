# trading-day-gap-detection Specification

## Purpose
TBD - created by archiving change add-trading-day-gap-detection. Update Purpose after archive.
## Requirements
### Requirement: Systematic trading day gap detection
The system SHALL provide a pure, session-free function
`detect_systematic_trading_day_gaps` that compares the union of all stored
trading days against the expected trading-calendar days for a date range and
returns one warning per calendar trading day absent from the union.

The function MUST accept `actual_dates` (the union of stored trade dates) and
`expected_dates` (the trading-calendar days for the same range) and return a
sorted list of `SystematicTradingDayGap` records, each carrying the missing
`trade_date`. The function MUST NOT hold a database session or mutate its inputs.

A systematic gap is a trading day the calendar says should exist but that no ETF
has stored data for — the failure mode that shifts `SELECT DISTINCT trade_date`
union-based sequences and corrupts position-indexed momentum windows.

#### Scenario: Detect a systematic gap
- **WHEN** `detect_systematic_trading_day_gaps` is called with `actual_dates` missing one calendar trading day that is present in `expected_dates`
- **THEN** the function returns a single `SystematicTradingDayGap` for that missing date

#### Scenario: No gaps when union matches calendar
- **WHEN** `detect_systematic_trading_day_gaps` is called with `actual_dates` equal to `expected_dates`
- **THEN** the function returns an empty list

#### Scenario: Dates outside the calendar are ignored
- **WHEN** `detect_systematic_trading_day_gaps` is called with `actual_dates` containing a date absent from `expected_dates`
- **THEN** the function does not flag that date (extra stored days are not gaps)

#### Scenario: Deterministic ordering
- **WHEN** `detect_systematic_trading_day_gaps` is called with multiple missing dates
- **THEN** the returned warnings are sorted ascending by `trade_date`

### Requirement: Per-ETF trading day gap detection
The system SHALL provide a pure, session-free ingestion-diagnostic function `detect_etf_trading_day_gaps` that compares each ETF's stored trading days against expected trading-calendar days and returns one warning per `(etf_id, trade_date)` gap, suppressing dates before a caller-supplied diagnostic boundary.

The function MUST accept `etf_actual_dates`, `expected_dates`, and `inception_boundaries`, and MUST return `EtfTradingDayGap` records sorted by `(etf_id, trade_date)`. A fetch caller MAY use `max(inception_date, first_stored_date)` to bound warnings to the locally observed fetch range. This diagnostic boundary and its warn-only result MUST NOT determine strategy, backtest, benchmark, or Walk-forward admissibility; execution uses authoritative `listing_date` and ETF session status and MUST fail on every unexplained required gap.

#### Scenario: Detect a per-ETF gap after inception
- **WHEN** `detect_etf_trading_day_gaps` is called for an ETF whose stored dates miss a calendar day that falls after the ETF's inception boundary
- **THEN** the function returns an `EtfTradingDayGap` for that `etf_id` and `trade_date`

#### Scenario: Suppress gaps before inception boundary
- **WHEN** `detect_etf_trading_day_gaps` is called for an ETF where a calendar day is missing but that day falls before the ETF's inception boundary
- **THEN** the function does not return a gap for that `etf_id` and `trade_date`

#### Scenario: No gaps when ETF covers the calendar
- **WHEN** `detect_etf_trading_day_gaps` is called for an ETF whose stored dates cover every calendar day after its inception boundary
- **THEN** the function returns no gaps for that `etf_id`

#### Scenario: Deterministic ordering across ETFs
- **WHEN** the detector finds multiple gaps across multiple ETFs
- **THEN** it returns warnings sorted by `(etf_id, trade_date)`

#### Scenario: Detect a per-ETF gap after diagnostic boundary
- **WHEN** the detector receives an ETF series missing a calendar day on or after its supplied boundary
- **THEN** it returns an `EtfTradingDayGap` for that ETF and date

#### Scenario: Suppress gaps before diagnostic boundary
- **WHEN** a missing calendar day falls before the supplied ingestion-diagnostic boundary
- **THEN** the detector does not return that gap

#### Scenario: No gaps when ETF covers diagnostic range
- **WHEN** an ETF covers every expected date on or after its supplied boundary
- **THEN** the detector returns no gap for that ETF

#### Scenario: Fetch boundary cannot authorize execution
- **WHEN** a first-stored-date boundary suppresses an ingestion warning for a post-listing truncated period
- **THEN** execution preflight still treats every required post-listing ETF/session without raw price or authoritative status as unresolved

### Requirement: Multi-section quality warnings envelope
The system SHALL provide a pure function
`build_quality_warnings_json_from_sections` that merges duplicate-trade-date
warnings and trading-day-gap warnings into a single JSON envelope string, and
SHALL keep the Phase 1 `build_quality_warnings_json` function for backward
compatibility.

The envelope MUST use top-level keys `duplicate_trade_dates`,
`systematic_trading_day_gaps`, and `etf_trading_day_gaps`. The function MUST
return `None` when all sections are empty, so the persisted
`DataFetchLog.quality_warnings` column stays null for clean batches. The
`duplicate_trade_dates` section MUST serialize identically to the Phase 1
envelope so existing consumers are not broken.

#### Scenario: Merge duplicate and gap warnings
- **WHEN** `build_quality_warnings_json_from_sections` is called with both duplicate warnings and gap warnings
- **THEN** the returned JSON object contains all three top-level keys with non-empty arrays for the present sections

#### Scenario: Empty envelope returns null
- **WHEN** `build_quality_warnings_json_from_sections` is called with no warnings of any kind
- **THEN** the function returns `None`

#### Scenario: Duplicate-only envelope matches Phase 1 shape
- **WHEN** `build_quality_warnings_json_from_sections` is called with only duplicate warnings
- **THEN** the `duplicate_trade_dates` array serializes identically to `build_quality_warnings_json` for the same input

#### Scenario: Gap-only envelope omits empty duplicate section
- **WHEN** `build_quality_warnings_json_from_sections` is called with only gap warnings
- **THEN** the returned JSON object includes the gap sections and omits an empty `duplicate_trade_dates` array

