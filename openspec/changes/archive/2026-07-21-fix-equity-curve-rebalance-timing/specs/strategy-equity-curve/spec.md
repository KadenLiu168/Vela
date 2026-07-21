## MODIFIED Requirements

### Requirement: Calculate strategy equity curve
The system SHALL calculate a daily strategy net value curve for requested trading dates using portfolio holding snapshots and market prices, and SHALL attribute each close-to-close market-return interval to the holding snapshot effective at the interval's start.

#### Scenario: Initial net value
- **WHEN** backend code calculates an equity curve for a non-empty trading-date list
- **THEN** the first curve point has net value `1.000000`

#### Scenario: One daily weighted return
- **WHEN** backend code calculates an equity curve for two trading dates with ETFs held in the first date's snapshot and those ETFs have prices on both dates
- **THEN** the second curve point net value equals the first net value multiplied by one plus the sum of each first-snapshot ETF target weight times its price return between those dates

#### Scenario: Carry holdings through interval
- **WHEN** backend code calculates an equity curve for consecutive dates whose holding snapshots carry the same successful strategy signal
- **THEN** each close-to-close daily return uses those carried-forward target holdings

#### Scenario: Interval ending at a rebalance-effective date uses prior holdings
- **WHEN** the holding snapshot for trading date T differs from the snapshot for the prior requested trading date
- **THEN** the close-to-close market return ending on T uses the prior trading date's target holdings
- **AND** the target holdings first appearing in the T snapshot do not receive market return from before T

#### Scenario: Interval after a rebalance uses new holdings
- **WHEN** the holding snapshot for trading date T contains target holdings that differ from the prior snapshot
- **THEN** the close-to-close market return from T to the following requested trading date uses the target holdings from the T snapshot

#### Scenario: Empty prior holdings keep market return neutral
- **WHEN** backend code calculates a curve point whose prior holding snapshot has no holdings
- **THEN** the close-to-close market return contribution for that point is zero

#### Scenario: Missing price return input is neutral
- **WHEN** an ETF held in the interval-start snapshot lacks either the previous or current strategy price for a daily return
- **THEN** that ETF contributes zero to the daily weighted return

#### Scenario: Empty trading-date list
- **WHEN** backend code calculates an equity curve for an empty trading-date list
- **THEN** the returned curve is empty

### Requirement: Test strategy equity curve calculation
The system SHALL include regression tests for strategy equity curve calculation covering held-position returns, initial net value, daily net values, and both sides of a rebalance-effective boundary.

#### Scenario: Verify initial and daily net values from held-position returns
- **WHEN** the strategy equity curve is calculated for multiple trading dates with held ETFs that have complete strategy prices
- **THEN** the tests verify the first curve point has net value `1.000000`
- **AND** the tests verify each following daily net value equals the prior net value multiplied by one plus the weighted interval-start held-position return
- **AND** the tests verify each following daily return value

#### Scenario: Verify the interval ending at a rebalance uses old holdings
- **WHEN** the strategy equity curve is calculated across a date where the effective holding snapshot changes and the old and new assets have materially different returns
- **THEN** the tests verify the interval ending on that date uses the old target holdings
- **AND** the tests verify the resulting daily return and net value include losses or gains from the old holdings

#### Scenario: Verify the interval after a rebalance uses new holdings
- **WHEN** the strategy equity curve includes a complete close-to-close interval after a changed holding snapshot becomes effective
- **THEN** the tests verify that following interval uses the new target holdings
- **AND** the tests verify the new holdings receive no market return from the preceding interval

### Requirement: Apply transaction costs to strategy equity curve
The system SHALL deduct transaction costs from strategy equity curve daily returns using the transaction cost rate defined by the strategy configuration and turnover at the transition from the interval-start snapshot to the interval-end snapshot.

#### Scenario: Initial entry cost
- **WHEN** backend code calculates an equity curve point whose prior snapshot is empty and whose current snapshot contains target holdings
- **THEN** the point's daily return subtracts turnover equal to the sum of current target weights multiplied by `transaction_cost_bps / 10000`
- **AND** the empty prior snapshot contributes zero market return for that interval

#### Scenario: Rebalance cost
- **WHEN** backend code calculates an equity curve point whose current target holdings differ from the prior trading date
- **THEN** the point's daily return uses the prior snapshot for market return
- **AND** the point's daily return subtracts turnover equal to the sum of absolute target weight changes multiplied by `transaction_cost_bps / 10000`

#### Scenario: Unchanged holdings
- **WHEN** consecutive holding snapshots have identical target holdings
- **THEN** the daily return has no transaction-cost deduction

#### Scenario: Zero transaction cost
- **WHEN** backend code calculates an equity curve with strategy configuration transaction cost set to zero
- **THEN** the daily return is not reduced by transaction costs
