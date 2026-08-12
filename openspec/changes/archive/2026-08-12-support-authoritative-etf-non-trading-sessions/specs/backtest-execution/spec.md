## MODIFIED Requirements

### Requirement: Trading day gap detection before backtest execution
The system SHALL use ordered `TradingCalendar` rows as the authoritative official-session axis for the inclusive backtest range and the configured strategy's exact required lookback history. Before generating or persisting a historical signal, it MUST require a declared `listing_date` for every active ETF and resolve each required on/after-listing ETF/session from exactly one raw market price or authoritative full-day non-trading status. Missing calendar coverage, metadata, unresolved gaps, status/price conflicts, and missing carry anchors MUST fail without a configurable warning-only mode or gap threshold.

Confirmed full-day statuses SHALL resolve to unchanged adjusted valuation with `tradable = false`; they SHALL NOT create raw prices. A scheduled target whose changed current/target trade-leg union contains a non-tradable ETF SHALL remain wholly pending until all legs are tradable. A newer successful target replaces an older pending target.

#### Scenario: Trading calendar defines requested dates
- **WHEN** a backtest range contains official calendar sessions and raw or status-backed ETF inputs
- **THEN** the runner uses the ordered calendar rows, not the union of stored price dates, as requested trading dates
- **AND** every equity-curve interval represents consecutive official sessions

#### Scenario: Exact strategy lookback sessions are validated
- **WHEN** the configured strategy requires N prior sessions
- **THEN** the runner resolves the exact N preceding official sessions before the first rebalance date
- **AND** validates only that exact set plus requested sessions
- **AND** an unrelated input outside that set does not block the run

#### Scenario: Missing trading calendar coverage fails
- **WHEN** the trading calendar contains no requested session or too few exact preceding sessions
- **THEN** the backtest raises before generating or persisting any signal

#### Scenario: Missing listing metadata fails
- **WHEN** an active research-universe ETF has null `listing_date`
- **THEN** preflight fails with the ETF identity
- **AND** it does not use fund inception or first stored price as a substitute

#### Scenario: Pre-listing sessions are not required
- **WHEN** an active ETF's listing date falls within or after the candidate required range
- **THEN** official sessions before listing require neither price nor status
- **AND** the ETF is absent from the dated strategy universe before listing
- **AND** every required on/after-listing session remains subject to resolution

#### Scenario: Raw price resolves required session
- **WHEN** a listed active ETF has one raw price and no full-day status on a required session
- **THEN** that session is complete, adjusted, and tradable

#### Scenario: Confirmed non-trading session resolves without raw price
- **WHEN** a listed ETF has authoritative full-day status, no raw price, and a prior resolved value
- **THEN** preflight emits a non-tradable carried adjusted valuation for that session
- **AND** does not persist a synthetic `MarketPrice`

#### Scenario: Unexplained active-universe gap fails
- **WHEN** a listed active ETF has neither price nor status on any required session
- **THEN** the backtest raises before generating or persisting a signal
- **AND** the error includes exact category totals and a bounded deterministic ETF/date sample

#### Scenario: Contradictory evidence fails
- **WHEN** an ETF/session has both a raw price and full-day non-trading status
- **THEN** preflight fails rather than selecting one source

#### Scenario: Non-tradable target defers whole rebalance
- **WHEN** a newly effective target would change a currently held or target ETF that is non-tradable
- **THEN** no trade leg executes and no transaction cost is charged on that session
- **AND** the existing portfolio remains invested and the complete target remains pending

#### Scenario: Pending rebalance executes once
- **WHEN** all changed legs of the pending target are tradable on a later official session
- **THEN** the complete target executes atomically after that session's valuation
- **AND** transaction cost is charged once

#### Scenario: Newer signal supersedes pending target
- **WHEN** a newer successful signal becomes effective before an older pending target can execute
- **THEN** the pending target becomes the newer complete target
- **AND** no stale trade is later executed

#### Scenario: Failure leaves no partial artifacts
- **WHEN** calendar, metadata, status, or resolved-input validation fails
- **THEN** no strategy signal, backtest run, equity row, benchmark, or signal link from the attempt is persisted
- **AND** transaction ownership remains with the caller

#### Scenario: Obsolete tolerance controls remain unavailable
- **WHEN** callers use mandatory resolved-input validation
- **THEN** the public API exposes no `BacktestGapDetectionConfig` or `gap_detection`
- **AND** the CLI exposes no strictness or gap-threshold bypass
