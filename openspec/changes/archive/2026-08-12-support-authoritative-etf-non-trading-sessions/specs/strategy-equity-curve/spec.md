## MODIFIED Requirements

### Requirement: Calculate strategy equity curve
The system SHALL calculate a daily net-value curve on ordered official sessions using a continuous normalized state of per-ETF market values, cash, active signal identity, and at most one pending complete target. Each held ETF interval endpoint MUST have a resolved adjusted value. A confirmed full-day non-trading point SHALL retain the prior adjusted value and be non-tradable; an unexplained missing endpoint MUST fail. Market return SHALL be attributed to interval-start holdings before any executable rebalance. A target whose changed current/target trade-leg union contains a non-tradable ETF SHALL execute no legs, charge no cost, and remain pending until every leg is tradable; a newer effective target SHALL replace an older pending target.

#### Scenario: Initial net value and state
- **WHEN** a non-empty curve begins without an immediately executable target
- **THEN** its first point has net value `1.000000` and daily return `0.000000`
- **AND** cash is `1.000000` until a complete target can execute

#### Scenario: Executable initial target
- **WHEN** the initial target has only tradable changed legs
- **THEN** the first point initializes normalized holdings without an initial entry cost

#### Scenario: Non-tradable initial target remains cash
- **WHEN** an initial target includes a non-tradable ETF
- **THEN** no partial position is created
- **AND** the portfolio remains cash with that complete target pending

#### Scenario: Carry holdings through interval
- **WHEN** no executable different target applies across an interval
- **THEN** the interval uses actual market values carried from its start
- **AND** does not reset them to target weights

#### Scenario: One daily weighted return
- **WHEN** held ETFs have resolved values at both interval endpoints
- **THEN** each held market value is multiplied by its resolved adjusted-value ratio
- **AND** interval-end net value equals cash plus marked holdings before any rebalance cost

#### Scenario: Confirmed full-day halt has zero price return
- **WHEN** a held ETF's current endpoint is `confirmed_non_trading_carry`
- **THEN** its adjusted-value ratio for that session is exactly one
- **AND** its position remains non-tradable without creating a raw price

#### Scenario: Actual weights drift without executable rebalance
- **WHEN** held ETFs earn different returns and no complete target executes
- **THEN** actual weights derive from marked values and carry into the next interval
- **AND** they are not reset to desired weights

#### Scenario: Single fully invested holding remains equivalent
- **WHEN** one ETF has full allocation and no executable different target applies
- **THEN** its actual weight remains the full risky allocation
- **AND** the curve equals its resolved-return compounding

#### Scenario: Interval ending at target-effective date uses prior holdings
- **WHEN** a different target first becomes effective on date T
- **THEN** the interval ending on T uses prior actual holdings
- **AND** new target ETFs receive no return from before T

#### Scenario: Executable target applies after valuation
- **WHEN** every changed leg of the effective or pending target is tradable on T
- **THEN** the complete rebalance applies after the interval ending on T
- **AND** the following interval uses the new state

#### Scenario: Non-tradable leg defers complete target
- **WHEN** any changed current/target leg is non-tradable on T
- **THEN** no target leg executes and no cost is charged
- **AND** the pre-existing portfolio remains the economic state after T

#### Scenario: New target replaces pending target
- **WHEN** a newer successful signal becomes effective while an older target is pending
- **THEN** the newer complete target replaces the older one
- **AND** the older target is never executed later

#### Scenario: Empty target liquidation can be deferred
- **WHEN** an empty target would liquidate a non-tradable holding
- **THEN** liquidation remains pending until that changed leg is tradable
- **AND** cash is not fabricated before execution

#### Scenario: Empty prior holdings keep market return neutral
- **WHEN** the prior economic state has no risky holdings
- **THEN** its interval market-return contribution is zero

#### Scenario: Unresolved previous held value fails
- **WHEN** an interval-start holding lacks a resolved previous endpoint
- **THEN** calculation raises with ETF/date context
- **AND** it does not infer, synthesize, or silently carry the value

#### Scenario: Unresolved current held value fails
- **WHEN** an interval-start holding lacks a resolved current endpoint
- **THEN** calculation raises with ETF/date context
- **AND** it does not infer, synthesize, or silently carry the value

#### Scenario: Non-positive portfolio cannot continue
- **WHEN** marked assets or transaction costs leave non-positive total assets
- **THEN** calculation fails explicitly without fabricating recovery

#### Scenario: Empty trading-date list
- **WHEN** requested trading dates are empty
- **THEN** the returned curve is empty
