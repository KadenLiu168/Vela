## ADDED Requirements

### Requirement: Trading day gap detection at fetch time
The system SHALL detect trading-day gaps after a full or incremental market
price fetch upserts its rows, comparing the stored trade-date union (and each
active ETF's stored dates) against the trading calendar, and record the result
in `DataFetchLog.quality_warnings`.

When the `trading_calendar` table has no rows covering the requested range, the
system MUST skip gap detection and record no gap warnings (the calendar has not
been synced yet). Fetch-time gap detection is warn-only: it never changes the
fetch status or error message.

The gap warnings MUST be merged with any duplicate-trade-date warnings from the
same batch via the multi-section `quality_warnings` envelope, so a single fetch
log row can carry both kinds of warnings.

#### Scenario: Record gap warnings after a successful fetch
- **WHEN** a full or incremental fetch upserts rows and the trading calendar has covering rows and the stored dates are missing calendar trading days
- **THEN** the system records a `quality_warnings` envelope containing `systematic_trading_day_gaps` and/or `etf_trading_day_gaps` sections on the fetch log

#### Scenario: No gap warnings when dates match the calendar
- **WHEN** a fetch upserts rows and the stored dates cover every calendar trading day in the requested range (per the inception-boundary rule)
- **THEN** the `quality_warnings` envelope contains no gap sections (and is `None` if there are also no duplicate warnings)

#### Scenario: Skip gap detection when the calendar is empty
- **WHEN** a fetch upserts rows and the `trading_calendar` table has no rows covering the requested range
- **THEN** the system does not attempt gap detection and records no gap warnings on the fetch log

#### Scenario: Gaps coexist with duplicate warnings
- **WHEN** a fetch batch has both duplicate trade dates and trading-day gaps
- **THEN** the `quality_warnings` envelope contains both the `duplicate_trade_dates` section and the gap sections

#### Scenario: Gaps never affect fetch status
- **WHEN** a fetch detects trading-day gaps
- **THEN** the fetch status and error message are determined solely by row counts and provider errors, not by the gap warnings
