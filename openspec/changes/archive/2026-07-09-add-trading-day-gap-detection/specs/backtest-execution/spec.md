## ADDED Requirements

### Requirement: Trading day gap detection before backtest execution
The system SHALL detect trading-day gaps after resolving the backtest trading
dates and before generating signals, comparing the resolved trading-date union
(and each active ETF's stored dates) against the trading calendar.

By default the system MUST warn about detected gaps (printing them) and continue
the backtest. An opt-in strict mode MUST raise without persisting a backtest run
when systematic gaps exceed a configurable threshold; per-ETF gaps MUST never
trigger strict failure (they are usually suspensions, not corruption).

When the `trading_calendar` table has no rows covering the requested backtest
range, the system MUST skip gap detection with a clear warning in the default
mode, and MUST refuse to run in strict mode (a strict check has no reference to
check against).

#### Scenario: Warn about gaps by default
- **WHEN** a backtest is run with the default (non-strict) data-quality mode and the trading calendar has covering rows and systematic and/or per-ETF gaps are detected
- **THEN** the system prints the detected gaps as a warning and proceeds with the backtest

#### Scenario: No warning when dates match the calendar
- **WHEN** a backtest is run in default mode and the stored dates cover every calendar trading day in the range (per the inception-boundary rule)
- **THEN** the system prints no gap warning and proceeds with the backtest

#### Scenario: Strict mode fails on excessive systematic gaps
- **WHEN** a backtest is run in strict mode and the number of systematic gaps exceeds the configured threshold
- **THEN** the system raises without persisting a backtest run, identifying the missing trading days

#### Scenario: Strict mode tolerates gaps within threshold
- **WHEN** a backtest is run in strict mode and the number of systematic gaps is within the configured threshold
- **THEN** the system warns about the gaps and proceeds with the backtest

#### Scenario: Per-ETF gaps never trigger strict failure
- **WHEN** a backtest is run in strict mode and only per-ETF gaps are detected (no systematic gaps)
- **THEN** the system warns about the per-ETF gaps and proceeds with the backtest

#### Scenario: Skip detection when the calendar is empty in default mode
- **WHEN** a backtest is run in default mode and the `trading_calendar` table has no rows covering the requested range
- **THEN** the system prints a warning that the calendar is not synced and proceeds with the backtest without gap detection

#### Scenario: Strict mode refuses to run without a calendar
- **WHEN** a backtest is run in strict mode and the `trading_calendar` table has no rows covering the requested range
- **THEN** the system raises without persisting a backtest run, explaining that strict mode requires a synced trading calendar
