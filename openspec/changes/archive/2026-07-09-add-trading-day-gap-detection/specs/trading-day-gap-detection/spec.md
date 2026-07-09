## ADDED Requirements

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
The system SHALL provide a pure, session-free function
`detect_etf_trading_day_gaps` that compares each ETF's stored trading days
against the expected trading-calendar days and returns one warning per
`(etf_id, trade_date)` gap, suppressing any date before the ETF's inception
boundary.

The function MUST accept `etf_actual_dates` (a mapping of `etf_id` to that ETF's
stored trade dates), `expected_dates` (the trading-calendar days), and
`inception_boundaries` (a mapping of `etf_id` to the earliest date that should
be checked for that ETF — typically `max(inception_date, first_stored_date)`).
It MUST return a sorted list of `EtfTradingDayGap` records, each carrying
`etf_id` and `trade_date`.

Suppression before the inception boundary prevents false positives for
pre-listing periods and the partial first record. Per-ETF gaps are usually
suspensions rather than corruption, so callers SHOULD treat them as warn-only.

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
- **WHEN** `detect_etf_trading_day_gaps` is called with gaps for multiple ETFs
- **THEN** the returned warnings are sorted by `(etf_id, trade_date)`

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
