# backtest-return-stability-series Specification

## Purpose
Defines the read-only return-stability series (63-session rolling diagnostics and monthly/yearly calendar returns) derived from a single persisted backtest net-value curve, exposed through Backtest Detail without browser-side financial calculation.

## Requirements

### Requirement: Stability derivation validates one persisted curve
The system SHALL derive stability series from one curve's persisted six-decimal net values ordered by trade date. Dates MUST be unique and strictly increasing, net values MUST be positive, and each effective return SHALL equal the current persisted net value divided by the previous persisted net value minus one. The initial point SHALL contribute no placeholder return, and malformed evidence SHALL fail instead of being sorted, deduplicated, filled, or partially returned.

#### Scenario: Persisted net values define effective returns
- **WHEN** a valid curve contains controlled dated net values whose adjacent ratios are independently known
- **THEN** every derived return uses the adjacent persisted values without intermediate quantization
- **AND** source and effective observation counts are exact

#### Scenario: Malformed curve fails closed
- **WHEN** dates are duplicate/non-increasing or any net value is non-positive
- **THEN** derivation rejects the complete stability result

### Requirement: Rolling diagnostics use 63 complete effective sessions
For each curve position with 63 preceding effective returns, the system SHALL publish one point containing the first source date, ending trade date, trailing compounded total return, population-standard-deviation Volatility multiplied by `sqrt(252)`, and Sharpe using `risk_free_rate / 252` and `sqrt(252)`. Each result SHALL use exactly 63 effective returns, retain unquantized Decimal reconstruction/compounding/mean/variance intermediates, follow the existing float square-root annualization convention, and quantize final Decimal values to six places.

#### Scenario: First rolling point uses 64 source values
- **WHEN** a valid curve contains exactly 64 points
- **THEN** it produces exactly one rolling point using all 63 adjacent effective returns
- **AND** its start/end dates identify the complete window

#### Scenario: Insufficient curve has no expanding result
- **WHEN** a valid curve contains fewer than 64 points
- **THEN** rolling status is `insufficient_observations`
- **AND** the rolling array is empty rather than calculated from a shorter window

#### Scenario: Missing legacy risk-free rate preserves other metrics
- **WHEN** a valid curve has at least 64 points but its historical run has no parseable annual risk-free-rate evidence
- **THEN** rolling total return and Volatility remain available
- **AND** every rolling Sharpe is null with `sharpe_status: unavailable_missing_risk_free_rate`

#### Scenario: Zero dispersion has null Sharpe
- **WHEN** all 63 effective returns in a window are equal
- **THEN** rolling Volatility is `0.000000`
- **AND** rolling Sharpe is null

### Requirement: Calendar returns compound ending-date observations
The system SHALL assign each effective return to the natural calendar month and year of its ending trade date, compound all assigned returns in that bucket, and publish period key, first/last contributing date, observation count, six-place total return, and `is_partial`. `is_partial` SHALL indicate only whether the requested run bounds cover the complete natural calendar period; it MUST NOT be represented as proof that the persisted curve contains every official session. It SHALL omit empty buckets and MUST NOT reset the first contributing session of a period to zero.

#### Scenario: Cross-month boundary return belongs to the new month
- **WHEN** adjacent curve points cross from one calendar month into the next
- **THEN** the return into the first session of the new month contributes to the new month's compounded return

#### Scenario: Requested-scope boundary periods are identified from run bounds
- **WHEN** requested run bounds do not cover the complete natural calendar month or year containing a returned bucket
- **THEN** that bucket is retained with `is_partial: true`
- **AND** fully bounded interior periods are marked non-partial

#### Scenario: Curve endpoints do not redefine requested scope
- **WHEN** requested bounds cover a complete natural month or year but the first or last persisted trade date falls inside that period because calendar boundaries are not official sessions
- **THEN** `is_partial` is derived from the requested bounds rather than the curve endpoint dates
- **AND** the flag is not described as an official-session completeness guarantee

### Requirement: Stability calculation is a public read-only capability
The `vela_core` package SHALL publicly export immutable stability result/point types and one shared derivation function used by HTTP detail serialization. It SHALL create no persistence rows, fields, version mutation, market-data read, trading-calendar read, or browser-side financial calculation.

#### Scenario: Repeated derivation is deterministic
- **WHEN** the public function receives the same curve, run bounds, and risk-free-rate evidence twice
- **THEN** both complete typed results are equal
- **AND** no database state changes

### Requirement: Stitched OOS resets are excluded
The system MUST NOT calculate these rolling or calendar-period series from a stitched Walk-forward OOS curve or across independent OOS window boundaries. Each OOS backtest MAY expose the capability only through its own ordinary Backtest Detail identity and authoritative curve.

#### Scenario: Walk-forward parent remains free of stability metrics
- **WHEN** a Walk-forward detail has an available stitched OOS curve
- **THEN** no rolling Sharpe, Volatility, Return, monthly return, or yearly return is derived from that stitched curve
- **AND** linked individual OOS backtests remain independently inspectable
