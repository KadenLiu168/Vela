## MODIFIED Requirements

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
- **WHEN** an ETF held in the interval-start state lacks the strategy price at the previous official interval endpoint
- **THEN** equity-curve calculation raises an error identifying the ETF and missing date
- **AND** the system does not carry the value, synthesize a price, or emit a zero return

#### Scenario: Missing current held price fails
- **WHEN** an ETF held in the interval-start state lacks the strategy price at the current official interval endpoint
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
