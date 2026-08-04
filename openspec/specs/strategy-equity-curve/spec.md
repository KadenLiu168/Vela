# strategy-equity-curve Specification

## Purpose
Defines how the daily strategy net-value equity curve is calculated from holding snapshots and market prices across trading dates.
## Requirements
### Requirement: Calculate strategy equity curve
The system SHALL calculate a daily strategy net value curve for requested trading dates using a continuous normalized state of per-ETF market values and cash, SHALL attribute each close-to-close market-return interval to the actual economic holdings effective at the interval's start, SHALL require complete strategy prices for every economically held ETF at both official interval endpoints, and SHALL rebalance that state to a new target allocation only when a different strategy signal becomes effective.

#### Scenario: Initial net value and state
- **WHEN** backend code calculates an equity curve for a non-empty trading-date list
- **THEN** the first curve point has net value `1.000000` and daily return `0.000000`
- **AND** an empty first holding snapshot initializes cash to `1.000000`
- **AND** a populated first holding snapshot initializes normalized target holdings without charging an initial-point entry cost

#### Scenario: Initial net value
- **WHEN** backend code calculates an equity curve for a non-empty trading-date list
- **THEN** the first curve point has net value `1.000000`

#### Scenario: Carry holdings through interval
- **WHEN** consecutive holding snapshots carry the same successful strategy signal
- **THEN** each close-to-close daily return uses the actual market values carried forward from the interval-start state
- **AND** the system does not reset those values to the target weights

#### Scenario: One daily weighted return
- **WHEN** backend code calculates a curve interval with ETFs held in the interval-start state and those ETFs have prices on both dates
- **THEN** each held ETF market value is multiplied by its forward-adjusted price ratio for that interval
- **AND** the interval-end net value equals cash plus the marked-to-market ETF values before any interval-end rebalance cost

#### Scenario: Actual weights drift without a new signal
- **WHEN** consecutive holding snapshots carry the same `strategy_signal_id`
- **AND** held ETFs earn different returns over an interval
- **THEN** the interval-end actual weights are derived from their marked-to-market values
- **AND** the system does not reset those actual weights to the carried target weights
- **AND** the drifted state is used as the starting state for the next interval

#### Scenario: Single fully invested holding remains equivalent
- **WHEN** one ETF has the full target allocation and no different strategy signal becomes effective
- **THEN** its actual weight remains the full risky-asset allocation
- **AND** the curve return equals that ETF's compounded interval returns

#### Scenario: Interval ending at a rebalance-effective date uses prior actual holdings
- **WHEN** a different `strategy_signal_id` first appears in the holding snapshot for trading date T
- **THEN** the close-to-close market return ending on T uses the actual state carried from the prior trading date
- **AND** target holdings first appearing in the T snapshot receive no market return from before T
- **AND** the transition to the new target occurs only after that interval return

#### Scenario: Interval ending at a rebalance-effective date uses prior holdings
- **WHEN** the holding snapshot for trading date T differs from the snapshot for the prior requested trading date
- **THEN** the close-to-close market return ending on T uses the actual state carried from the prior trading date
- **AND** target holdings first appearing in the T snapshot do not receive market return from before T

#### Scenario: Interval after a rebalance uses new holdings
- **WHEN** a different strategy signal becomes effective on trading date T
- **THEN** the post-rebalance state on T reflects the new normalized target allocation
- **AND** the close-to-close interval from T to the following requested trading date uses that post-rebalance state

#### Scenario: Empty target moves the portfolio to cash
- **WHEN** a different effective signal has no target holdings
- **THEN** the system liquidates the risky-asset state after the interval ending on that date
- **AND** the post-rebalance state holds the remaining total assets as cash

#### Scenario: Empty prior holdings keep market return neutral
- **WHEN** backend code calculates a curve point whose prior holding snapshot has no holdings
- **THEN** the close-to-close market return contribution for that point is zero

#### Scenario: Missing previous held price fails
- **WHEN** an ETF held in the interval-start state lacks either the previous or current strategy price
- **THEN** equity-curve calculation raises an error identifying the ETF and missing date
- **AND** the system does not carry the value, synthesize a price, or emit a zero return

#### Scenario: Missing current held price fails
- **WHEN** an ETF held in the interval-start state lacks either the previous or current strategy price
- **THEN** equity-curve calculation raises an error identifying the ETF and missing date
- **AND** the system does not carry the value, synthesize a price, or emit a zero return

#### Scenario: Non-positive portfolio cannot continue
- **WHEN** marked-to-market assets or transaction costs leave non-positive total assets before a required weight calculation
- **THEN** equity-curve calculation fails explicitly
- **AND** the system does not divide by zero or fabricate a later recovery

#### Scenario: Empty trading-date list
- **WHEN** backend code calculates an equity curve for an empty trading-date list
- **THEN** the returned curve is empty

### Requirement: Test strategy equity curve calculation
The system SHALL include regression tests for continuous portfolio-state calculation covering natural weight drift, the initial state, single-asset equivalence, missing held-price failure, precision, and both sides of a rebalance-effective boundary.

#### Scenario: Verify initial and daily net values from held-position returns
- **WHEN** the strategy equity curve is calculated for multiple trading dates with held ETFs that have complete strategy prices
- **THEN** the tests verify the first curve point has net value `1.000000`
- **AND** the tests verify each following daily net value reflects the interval-start actual holdings
- **AND** the tests verify each following daily return value

#### Scenario: Verify the interval ending at a rebalance uses old holdings
- **WHEN** a different signal becomes effective on T and the old and new assets have materially different returns
- **THEN** tests verify that the interval ending on T uses the old actual holdings
- **AND** tests verify the new target receives no preceding market return

#### Scenario: Verify the interval after a rebalance uses new holdings
- **WHEN** the curve includes a complete interval after a different signal becomes effective
- **THEN** tests verify that following interval uses the post-rebalance target state

#### Scenario: Verify multi-day natural drift
- **WHEN** tests calculate a 50/50 two-ETF portfolio whose assets earn different returns on consecutive intervals without a new signal
- **THEN** the first interval produces drifted actual weights
- **AND** the second interval return uses those drifted weights rather than the original 50/50 targets

#### Scenario: Verify single-asset equivalence
- **WHEN** tests calculate multiple intervals for one fully invested ETF
- **THEN** the resulting net values equal direct compounding of that ETF's interval returns

#### Scenario: Verify the interval ending at a rebalance uses old state
- **WHEN** a different signal becomes effective on T and the old and new assets have materially different returns
- **THEN** tests verify that the interval ending on T uses the old actual holdings
- **AND** tests verify the new target receives no preceding market return

#### Scenario: Verify the interval after a rebalance uses new state
- **WHEN** the curve includes a complete interval after a different signal becomes effective
- **THEN** tests verify that following interval uses the post-rebalance target state

#### Scenario: Verify high-precision state carry
- **WHEN** tests calculate a multi-day path whose intermediate values have more than six decimal places
- **THEN** the final observable result matches an independent high-precision calculation rounded only at the output boundary
- **AND** it does not match a calculation that reconstructs state from daily six-decimal outputs

#### Scenario: Verify missing held-price endpoints fail
- **WHEN** focused tests omit either the previous or current price for an ETF held at interval start
- **THEN** each case raises with the ETF and missing official date
- **AND** no test expects frozen value or neutral daily return behavior

### Requirement: Apply transaction costs to strategy equity curve
The system SHALL apply transaction costs only when a different strategy signal becomes effective, SHALL calculate turnover from the pre-trade actual risky-asset weights to the normalized new target weights, and SHALL deduct cost from marked-to-market closing assets before creating the post-rebalance state.

#### Scenario: Initial entry cost
- **WHEN** backend code calculates an equity curve point whose prior snapshot is empty and whose current snapshot contains target holdings
- **THEN** the point applies entry turnover equal to the normalized target risky-asset allocation multiplied by `transaction_cost_bps / 10000`
- **AND** the empty prior snapshot contributes zero market return for that interval

#### Scenario: Rebalance cost
- **WHEN** backend code calculates an equity curve point whose current snapshot has a different strategy signal from the prior trading date
- **THEN** the point's market return uses the prior actual state
- **AND** the point applies turnover equal to the sum of absolute differences between pre-trade actual and normalized target weights multiplied by `transaction_cost_bps / 10000`

#### Scenario: Unchanged holdings
- **WHEN** consecutive holding snapshots have the same strategy signal
- **THEN** the daily return has no transaction-cost deduction

#### Scenario: Zero transaction cost
- **WHEN** backend code calculates an equity curve with strategy configuration transaction cost set to zero
- **THEN** the daily return is not reduced by transaction costs

#### Scenario: Initial entry cost after an empty state
- **WHEN** a populated signal becomes effective after a preceding empty portfolio state
- **THEN** turnover equals the sum of the normalized target risky-asset weights
- **AND** the empty prior state contributes zero market return for the interval
- **AND** entry cost is charged against interval-end assets before allocating the new holdings

#### Scenario: Rebalance cost uses drifted actual weights
- **WHEN** a different signal becomes effective after existing holdings have drifted
- **THEN** turnover equals the sum over the union of actual and target ETF ids of the absolute difference between pre-trade actual weight and normalized target weight
- **AND** turnover is not calculated from the prior signal's target weights

#### Scenario: Same target under a new signal still rebalances
- **WHEN** a different `strategy_signal_id` becomes effective with target weights equal to the prior signal's targets
- **AND** actual weights have drifted away from those targets
- **THEN** the system trades back to the targets
- **AND** deducts transaction cost for the resulting non-zero turnover

#### Scenario: Carried signal does not rebalance
- **WHEN** consecutive snapshots carry the same `strategy_signal_id`
- **THEN** the system preserves the marked-to-market state
- **AND** deducts no transaction cost

#### Scenario: Market return and transaction cost compound in event order
- **WHEN** a portfolio earns a non-zero market return before a rebalance with non-zero turnover and cost rate
- **THEN** post-cost assets equal marked-to-market assets multiplied by `1 - turnover × transaction_cost_bps / 10000`
- **AND** daily return equals post-cost assets divided by prior-close assets minus one

#### Scenario: Zero transaction cost
- **WHEN** a different signal becomes effective with strategy transaction cost configured as zero
- **THEN** the system rebalances to the new target without reducing total assets

#### Scenario: Target thirds do not create phantom cash or turnover
- **WHEN** a signal contains three equal `Decimal("1") / Decimal(3)` target weights
- **THEN** the execution allocation normalizes the positive target weights to the full available portfolio
- **AND** Decimal repetition does not create negative cash or later phantom turnover

#### Scenario: Cost exhausts portfolio
- **WHEN** calculated transaction cost would leave zero or negative post-cost assets
- **THEN** equity-curve calculation fails explicitly

### Requirement: Calculate annualized return from strategy equity curve
The system SHALL calculate annualized return from strategy equity curve points using first net value, last net value, and elapsed calendar days.

#### Scenario: Positive elapsed curve
- **WHEN** backend code calculates annualized return for an equity curve with at least two points, a positive starting net value, and a positive calendar-day span
- **THEN** the system returns total return equal to `ending_net_value / starting_net_value - 1`
- **AND** annualized return equal to `(ending_net_value / starting_net_value) ^ (365 / elapsed_calendar_days) - 1`

#### Scenario: Flat curve
- **WHEN** backend code calculates annualized return for an equity curve whose first and last net values are equal across a positive calendar-day span
- **THEN** the system returns total return `0.000000`
- **AND** annualized return `0.000000`

#### Scenario: Not enough elapsed time
- **WHEN** backend code calculates annualized return for an equity curve with fewer than two points or without a positive calendar-day span
- **THEN** the system returns no total return or annualized return value

#### Scenario: Non-positive starting net value
- **WHEN** backend code calculates annualized return for an equity curve whose first net value is zero or negative
- **THEN** the system returns no total return or annualized return value

### Requirement: Calculate maximum drawdown from strategy equity curve
The system SHALL calculate maximum drawdown from strategy equity curve points using each point's net value and trade date.

#### Scenario: Typical drawdown curve
- **WHEN** backend code calculates maximum drawdown for an equity curve that rises to a peak and then falls to a lower trough
- **THEN** the system returns the lowest drawdown value equal to `trough_net_value / peak_net_value - 1`
- **AND** the system returns the peak and trough dates that define that maximum drawdown interval

#### Scenario: No drawdown
- **WHEN** backend code calculates maximum drawdown for an empty, flat, or all-rising equity curve
- **THEN** the system returns maximum drawdown `0.000000`
- **AND** the system returns no peak or trough date interval

### Requirement: Calculate annualized volatility from strategy equity curve
The system SHALL calculate annualized volatility from strategy equity curve daily returns using the effective return observations after the initial curve point.

#### Scenario: Typical volatile return sequence
- **WHEN** backend code calculates volatility for an equity curve with at least two effective daily return observations after the initial point
- **THEN** the system returns annualized volatility equal to the population standard deviation of those effective daily returns multiplied by the square root of 252
- **AND** the result is quantized to six decimal places

#### Scenario: Flat return sequence
- **WHEN** backend code calculates volatility for an equity curve whose effective daily return observations are all zero
- **THEN** the system returns volatility `0.000000`

#### Scenario: Not enough effective return observations
- **WHEN** backend code calculates volatility for an equity curve with fewer than two effective daily return observations after the initial point
- **THEN** the system returns no volatility value

### Requirement: Calculate Sharpe ratio from strategy metrics
The system SHALL calculate Sharpe ratio from effective equity curve daily return observations and the configured annual risk-free rate, using `mean(daily_excess_returns) / population_stddev(daily_excess_returns) × √252`.

#### Scenario: Typical positive Sharpe ratio
- **WHEN** backend code calculates Sharpe ratio for an equity curve whose effective returns have positive mean excess return and positive population standard deviation
- **THEN** the system treats only the points after the initial equity-curve point as effective return observations
- **AND** the system computes each effective daily excess return as `daily_return - risk_free_rate / 252`
- **AND** the system returns `mean(daily_excess) / population_stddev(daily_excess) × √252`
- **AND** the result is quantized to six decimal places

#### Scenario: Initial placeholder return is excluded
- **WHEN** the initial equity-curve point has its initialization placeholder return and at least two effective return observations follow it
- **THEN** the placeholder return does not contribute to the Sharpe mean or population standard deviation

#### Scenario: Negative excess return
- **WHEN** backend code calculates Sharpe ratio for an equity curve whose mean daily excess return is negative and daily excess returns have positive standard deviation
- **THEN** the system returns a negative Sharpe ratio

#### Scenario: Insufficient equity curve data
- **WHEN** backend code calculates Sharpe ratio for an equity curve with fewer than two effective daily return observations after the initial point
- **THEN** the system returns no Sharpe ratio value

#### Scenario: Zero standard deviation of daily excess returns
- **WHEN** backend code calculates Sharpe ratio for an equity curve whose daily excess returns have zero standard deviation
- **THEN** the system returns no Sharpe ratio value

#### Scenario: Backtest execution uses the corrected observations
- **WHEN** the backtest runner calculates summary metrics for an equity curve
- **THEN** it passes that equity curve and the configured annual risk-free rate to the Sharpe calculator
- **AND** it persists the resulting nullable six-decimal Sharpe value without changing the backtest result schema

### Requirement: Performance metric annualization contracts are explicit
The system SHALL preserve and distinguish calendar-time compounded annual growth from 252-trading-day arithmetic volatility and Sharpe. CAGR SHALL remain an endpoint geometric return based on elapsed calendar days; annualized volatility and Sharpe SHALL remain statistics of the effective daily return observations after the initial placeholder point. CAGR MUST NOT be used as the numerator of the daily-return Sharpe calculation.

#### Scenario: Calendar-time CAGR remains unchanged
- **WHEN** annualized return is calculated from a valid equity curve
- **THEN** CAGR equals `(ending_net_value / starting_net_value) ^ (365 / elapsed_calendar_days) - 1`
- **AND** its exponent does not depend on the number of effective return observations

#### Scenario: Trading-day volatility and Sharpe remain unchanged
- **WHEN** volatility and Sharpe are calculated from a valid equity curve
- **THEN** both calculations use only the effective daily return observations after the initial placeholder point
- **AND** volatility uses population standard deviation multiplied by `sqrt(252)`
- **AND** Sharpe uses `mean(daily_return - risk_free_rate / 252) / population_stddev(daily_return) * sqrt(252)`

#### Scenario: Valid Sharpe consistency identity
- **WHEN** focused tests calculate unquantized moments from a controlled non-constant effective daily return sequence whose net values compound those same returns
- **THEN** they derive annualized arithmetic excess return as `mean(daily_return - risk_free_rate / 252) * 252`
- **AND** they derive annualized volatility from the same observations as `population_stddev(daily_return) * sqrt(252)`
- **AND** their ratio produces the expected Sharpe value at the public six-decimal output boundary

#### Scenario: CAGR is not a Sharpe reconstruction contract
- **WHEN** a controlled non-zero-volatility equity curve has net values compounded from its effective daily returns and has both a calculable CAGR and Sharpe
- **THEN** regression tests lock the independently hand-derived values
- **AND** they demonstrate that `(CAGR - risk_free_rate) / annualized_volatility` is not required to equal Sharpe

#### Scenario: Metric compatibility is preserved
- **WHEN** this clarification is applied
- **THEN** public Python signatures, REST and CLI payload fields, database columns, and six-decimal metric values remain unchanged
- **AND** existing persisted backtest runs are not recalculated or mutated

### Requirement: Test maximum drawdown calculation
The system SHALL include regression tests for maximum drawdown calculation across representative strategy net value curves.

#### Scenario: Rising curve has no drawdown
- **WHEN** backend tests calculate maximum drawdown for an all-rising strategy equity curve
- **THEN** the tests verify maximum drawdown is `0.000000`
- **AND** the tests verify no peak or trough date interval is returned

#### Scenario: Falling curve records peak-to-trough loss
- **WHEN** backend tests calculate maximum drawdown for a strategy equity curve that falls from its initial peak
- **THEN** the tests verify the maximum drawdown value equals `trough_net_value / peak_net_value - 1`
- **AND** the tests verify the peak date is the initial peak date
- **AND** the tests verify the trough date is the lowest net value date

#### Scenario: Recovery after drawdown preserves deepest interval
- **WHEN** backend tests calculate maximum drawdown for a strategy equity curve that falls and later recovers without exceeding the prior peak
- **THEN** the tests verify the maximum drawdown remains the deepest peak-to-trough loss
- **AND** the tests verify the recovery point does not replace the trough date

### Requirement: Test transaction cost calculation
The system SHALL include regression tests for actual-weight turnover, signal-identity transitions, cost compounding, configured cost rates, and net-value impact.

#### Scenario: Different turnover amounts
- **WHEN** backend tests calculate strategy equity curves for rebalances with different actual-weight turnover
- **THEN** the tests verify each cost reflects `turnover * transaction_cost_bps / 10000` after market return

#### Scenario: Different transaction cost rates
- **WHEN** backend tests calculate the same turnover under different configured transaction cost basis points
- **THEN** the tests verify the higher cost rate produces the larger daily return deduction

#### Scenario: Net value impact
- **WHEN** backend tests calculate a strategy equity curve with transaction costs and non-zero market returns
- **THEN** the tests verify each affected net value compounds the market return before transaction cost deduction

#### Scenario: Different actual turnover amounts
- **WHEN** backend tests calculate rebalances from different pre-trade drifted weights to the same target
- **THEN** each cost reflects its actual-weight turnover multiplied by the configured rate

#### Scenario: Different transaction cost rates
- **WHEN** backend tests calculate the same rebalance under different configured cost basis points
- **THEN** the higher cost rate produces the larger post-market asset deduction

#### Scenario: Net value impact
- **WHEN** backend tests calculate a curve interval with non-zero market return and rebalance cost
- **THEN** tests verify net value using multiplicative market-return and cost sequencing

#### Scenario: Same-target signal identity regression
- **WHEN** backend tests persist two different signals with equal target weights around a period of natural drift
- **THEN** tests verify the second signal recenters the portfolio and incurs non-zero cost

### Requirement: Expose auditable portfolio state on equity points
The system SHALL expose each curve point's normalized cash, aggregate market value, and per-ETF target and actual weights from the same internal state used to calculate that point's net value.

#### Scenario: Fully invested drifted state
- **WHEN** a curve point contains drifted risky-asset holdings and no cash
- **THEN** aggregate market value equals net value
- **AND** the exposed actual weights reflect the marked-to-market position values rather than copied target weights

#### Scenario: Cash state
- **WHEN** a curve point contains no risky-asset holdings
- **THEN** cash equals net value
- **AND** aggregate market value is zero

#### Scenario: Output conservation
- **WHEN** a curve point is exposed at six-decimal output precision
- **THEN** cash plus aggregate market value equals total assets
- **AND** total assets equals net value

#### Scenario: Internal state is not reconstructed from output
- **WHEN** the calculation advances beyond an exposed curve point
- **THEN** it uses the unquantized internal state
- **AND** it does not reconstruct holdings from the point's six-decimal values

#### Scenario: Metric calculation remains state-independent
- **WHEN** annualized return, drawdown, volatility, or Sharpe is calculated from equity points
- **THEN** the metric calculation consumes only the existing trade date, net value, and daily return fields
- **AND** it does not require or reconstruct portfolio state
### Requirement: Calculate downside and drawdown-duration metrics from strategy equity
The strategy equity metric layer SHALL calculate Sortino using the configured risk-free rate, Calmar using the existing calendar-time annualized return and negative maximum drawdown, and longest drawdown duration from the ordered official-session points according to `active-and-downside-risk-metrics`.

#### Scenario: One curve produces consistent expanded metrics
- **WHEN** a valid strategy curve has sufficient effective returns, non-zero downside deviation and a non-zero maximum drawdown
- **THEN** the metric layer returns Sortino, Calmar and longest-duration fields from that same curve
- **AND** does not change total return, CAGR, maximum drawdown, volatility or Sharpe

#### Scenario: Flat curve preserves distinct null and zero values
- **WHEN** a valid strategy curve never goes underwater and has zero downside deviation
- **THEN** longest drawdown duration is zero
- **AND** Sortino and Calmar are null
