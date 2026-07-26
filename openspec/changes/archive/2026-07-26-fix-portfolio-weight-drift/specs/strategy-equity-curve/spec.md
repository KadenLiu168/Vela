## MODIFIED Requirements

### Requirement: Calculate strategy equity curve
The system SHALL calculate a daily strategy net value curve for requested trading dates using a continuous normalized state of per-ETF market values and cash, SHALL attribute each close-to-close market-return interval to the actual economic holdings effective at the interval's start, and SHALL rebalance that state to a new target allocation only when a different strategy signal becomes effective.

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

#### Scenario: Missing price return input freezes held value
- **WHEN** an ETF held in the interval-start state lacks either the previous or current strategy price
- **THEN** that ETF's market value is carried unchanged for the interval
- **AND** the ETF remains in the portfolio state

#### Scenario: Missing price return input is neutral
- **WHEN** an ETF held in the interval-start state lacks either the previous or current strategy price
- **THEN** that ETF contributes zero to the daily weighted return

#### Scenario: Non-positive portfolio cannot continue
- **WHEN** marked-to-market assets or transaction costs leave non-positive total assets before a required weight calculation
- **THEN** equity-curve calculation fails explicitly
- **AND** the system does not divide by zero or fabricate a later recovery

#### Scenario: Empty trading-date list
- **WHEN** backend code calculates an equity curve for an empty trading-date list
- **THEN** the returned curve is empty

### Requirement: Test strategy equity curve calculation
The system SHALL include regression tests for continuous portfolio-state calculation covering natural weight drift, the initial state, single-asset equivalence, missing-price value carry, precision, and both sides of a rebalance-effective boundary.

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

## ADDED Requirements

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
