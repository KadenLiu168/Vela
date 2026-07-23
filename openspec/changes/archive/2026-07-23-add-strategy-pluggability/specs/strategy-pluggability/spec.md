## ADDED Requirements

### Requirement: Bound strategy protocol contract
The system SHALL define a `Strategy` protocol whose instance is bound to one validated strategy configuration. It SHALL expose `lookback_days()` and single-date `generate_signal(...)`. Generation SHALL accept a signal date, caller-supplied active ETFs, and a price panel, and SHALL return `list[GeneratedSignalPosition]`. A strategy SHALL NOT receive a database session, query `MarketPrice`, persist, flush, or commit.

#### Scenario: Strategy produces positions from injected inputs
- **WHEN** a bound strategy is invoked with a non-empty active ETF list and price panel
- **THEN** it reads only its immutable parameters and injected inputs
- **AND** every returned position has etf_id, exchange, symbol, and target_weight

#### Scenario: Strategy declares lookback
- **WHEN** orchestration asks for lookback
- **THEN** the strategy returns a non-negative number of prior trading sessions
- **AND** dual momentum returns the maximum short, long, and moving-average window
- **AND** equal weight returns 0

#### Scenario: Expected strategy failure uses the domain error
- **WHEN** a strategy cannot generate because of an expected data/config condition specific to that strategy
- **THEN** it raises `StrategyGenerationError` with a clear message
- **AND** it does not construct or persist a platform result itself

### Requirement: Shared generation owns result and persistence semantics
The generic single-date signal-generation wrapper SHALL resolve the strategy, validate shared preconditions, invoke the protocol, convert positions to the existing success result, convert `StrategyGenerationError` to the existing failed result, and invoke the optional persistence callback exactly once for either outcome. Unexpected exceptions SHALL propagate.

#### Scenario: Empty active universe is a failed result
- **WHEN** the caller supplies no active ETFs
- **THEN** the wrapper returns a failed result with a clear error message
- **AND** it does not invoke a concrete strategy

#### Scenario: Empty strategy selection is a valid signal
- **WHEN** a strategy validly returns no positions from a non-empty active universe
- **THEN** the wrapper returns status success with result `empty`

#### Scenario: Expected failure is persisted through the callback
- **WHEN** a strategy raises `StrategyGenerationError` and a callback is supplied
- **THEN** the wrapper invokes the callback once with failed status and no positions
- **AND** returns the callback's signal id in the failed result

#### Scenario: Programming error is not hidden
- **WHEN** a strategy raises an exception other than `StrategyGenerationError`
- **THEN** the exception propagates
- **AND** the wrapper does not synthesize a failed strategy result

### Requirement: Strategy registry and type dispatch
The system SHALL maintain an immutable plain-dict registry from supported type strings to factories. `resolve_strategy(config)` SHALL use the config type to create a parameter-bound strategy. Shared orchestration SHALL contain no strategy-type-specific conditionals.

#### Scenario: Resolve dual momentum
- **WHEN** resolution receives a dual-momentum config variant
- **THEN** it returns a dual-momentum strategy bound to that variant's parameters

#### Scenario: Resolve equal weight
- **WHEN** resolution receives an equal-weight config variant
- **THEN** it returns an equal-weight strategy bound to its parameters

#### Scenario: Direct unknown registry lookup is rejected
- **WHEN** registry resolution is called with an unsupported type outside normal typed loading
- **THEN** it raises a clear project-owned error naming the type

#### Scenario: Orchestration does not branch on type
- **WHEN** live or backtest signal generation uses either registered type
- **THEN** it resolves through the registry and calls the protocol
- **AND** it does not import a concrete strategy or use type-specific conditionals

### Requirement: Adding a strategy has four bounded touchpoints
A new strategy SHALL be addable by (1) adding its parameter model and top-level config variant to the discriminated union, (2) implementing one bound strategy module, (3) adding one registry factory mapping, and (4) adding focused contract/config tests and a config fixture. Shared signal orchestration, backtest flow, holdings, equity-curve, metrics, transaction cost, persistence, and reports SHALL require no edits.

#### Scenario: New strategy does not touch shared capabilities
- **WHEN** a developer follows the four-touchpoint contract
- **THEN** no edits are required in backtest_runner, strategy_signal_generation, strategy_signal_service, strategy_equity_curve, portfolio_holdings, persistence, or report modules
- **AND** selecting it at runtime requires configuration changes only

### Requirement: Uniform strategy position contract
All implementations SHALL return the same `GeneratedSignalPosition` class (not a parallel DTO) with etf_id, exchange, symbol, target_weight, optional rank, and optional score. Shared consumers SHALL not inspect the producing strategy type.

#### Scenario: Existing import remains the same class
- **WHEN** callers import `GeneratedSignalPosition` from the existing signal-generation/package export path
- **THEN** they receive the same class used by strategy implementations

#### Scenario: Platform consumes positions without strategy knowledge
- **WHEN** persistence, holdings, equity-curve, metrics, or reports consume generated positions
- **THEN** they use only the uniform fields
- **AND** they do not branch on strategy type

### Requirement: Equal-weight validation strategy
The system SHALL register an `equal_weight` strategy that, for a non-empty caller-supplied active ETF list, returns one deterministic position per ETF with weight `Decimal("1") / Decimal(N)`, rank and score unset, and lookback 0. It SHALL not read the price panel.

#### Scenario: Equal weight allocates every active ETF
- **WHEN** equal weight receives N active ETFs in any input order
- **THEN** it returns N positions ordered deterministically by ETF id
- **AND** every target weight is `Decimal("1") / Decimal(N)`
- **AND** rank and score are null

#### Scenario: Equal weight requires no historical prices
- **WHEN** equal weight receives a non-empty active list and an empty price panel
- **THEN** generation succeeds
- **AND** its lookback is 0

### Requirement: Dual-momentum behavior remains stable
The dual-momentum implementation SHALL retain the current trend filter, forward-adjusted momentum scoring, ranking, Top N, defensive fallback, no-future-data, result, and persistence behavior.

#### Scenario: Existing regression behavior is preserved
- **WHEN** existing dual-momentum fixtures run through the registry and shared wrapper
- **THEN** positions, ranks, scores, weights, status/result labels, equity curve, and metrics match pre-change expectations
- **AND** expected defensive-asset failures remain failed results rather than escaping exceptions
