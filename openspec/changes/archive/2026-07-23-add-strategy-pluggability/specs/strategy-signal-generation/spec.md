## MODIFIED Requirements

### Requirement: Generate strategy signal from local market data
The system SHALL generate a strategy signal for a requested date from a caller-supplied active ETF list, loaded strategy config, and injected price panel. The generic function SHALL resolve a bound strategy via the registry, SHALL NOT accept a database session, and SHALL issue no `MarketPrice` query. For dual momentum, the implementation SHALL preserve trend filtering, momentum scoring, ranking, and defensive fallback; strategy-specific derived data such as the defensive lookup SHALL remain inside that implementation.

#### Scenario: Generate ranked dual-momentum signal
- **WHEN** dual momentum receives a non-empty active list and a sufficient panel
- **THEN** it applies the configured trend filter before ranking
- **AND** calculates configured momentum scores for passing ETFs
- **AND** returns selected positions with rank, score, and target weight

#### Scenario: Generate signal performs zero MarketPrice queries
- **WHEN** generic generation invokes any registered strategy
- **THEN** no SQL statement targets `market_price` during that call

#### Scenario: Persistence is delegated to the caller via callback
- **WHEN** generation receives a persist callback
- **THEN** the shared wrapper invokes it once with the success or expected-failure result
- **AND** no database write occurs without a callback

#### Scenario: Apply defensive fallback during generation
- **WHEN** dual momentum finds fewer eligible ranked ETFs than Top N
- **THEN** it returns one position per configured defensive asset
- **AND** each weight is `Decimal("1") / Decimal(N)`
- **AND** the total is approximately 1 within existing Decimal/persistence tolerance
- **AND** ETF ids are resolved from the injected active list without SQL

#### Scenario: Fail when no active ETFs exist
- **WHEN** the caller-supplied active ETF list is empty
- **THEN** generic generation returns a failed result with a clear message
- **AND** it does not raise or invoke a concrete strategy

#### Scenario: Fail when defensive asset is missing locally
- **WHEN** dual-momentum fallback cannot find a configured defensive asset in the active list
- **THEN** the strategy raises `StrategyGenerationError`
- **AND** the shared wrapper returns a failed result with the clear message

#### Scenario: Empty strategy decision succeeds
- **WHEN** a strategy validly returns no positions for a non-empty active universe
- **THEN** generic generation returns status success with result `empty`

### Requirement: Generate historical strategy signals
The system SHALL derive rebalance dates with the shared rebalance-date logic and generate one result per date by invoking the same registry-dispatched single-date wrapper. It SHALL use the caller-supplied panel and active list, issue no per-rebalance `MarketPrice` query, return ascending results, and preserve optional callback persistence.

#### Scenario: Weekly historical generation
- **WHEN** historical dates use weekly frequency
- **THEN** shared logic derives weekly rebalance dates
- **AND** invokes the bound strategy once per derived date
- **AND** returns results in ascending order

#### Scenario: Monthly historical generation
- **WHEN** historical dates use monthly frequency
- **THEN** shared logic derives monthly rebalance dates
- **AND** invokes the bound strategy once per derived date
- **AND** returns results in ascending order

#### Scenario: Historical generation does not use future data
- **WHEN** later prices exist in the injected panel
- **THEN** the per-date strategy input contains/uses only rows on or before that rebalance date

#### Scenario: Historical positions are persisted via callback
- **WHEN** a callback is supplied
- **THEN** it is invoked once for every generated rebalance result, including expected failures
- **AND** no write occurs without a callback

#### Scenario: Empty historical trading dates
- **WHEN** historical trading dates are empty
- **THEN** the function returns an empty list
- **AND** no strategy is invoked and no callback is called

#### Scenario: Monthly frequency produces fewer signals than weekly
- **WHEN** the same sufficiently long date sequence runs weekly and monthly
- **THEN** monthly generation produces fewer results than weekly generation

### Requirement: Generate and persist single-date strategy signal in core
The core service SHALL resolve the date, load active ETFs and the price panel, invoke generic registry-dispatched generation, convert callback positions, and persist the result. It SHALL not construct strategy-specific inputs. Transaction ownership and source validation SHALL remain unchanged.

#### Scenario: Generate and persist using latest local market date
- **WHEN** the service is called without a date and local prices exist
- **THEN** it uses the latest local trade date
- **AND** generic generation resolves the config type
- **AND** it persists one signal row and generated positions for the config identity
- **AND** returns the persisted signal id

#### Scenario: Generate and persist using explicit signal date
- **WHEN** an explicit date is supplied
- **THEN** the service uses that exact date

#### Scenario: Missing local market prices
- **WHEN** no explicit date and no local prices exist
- **THEN** the service raises clearly before strategy invocation
- **AND** persists no signal

#### Scenario: Core service shares API and CLI behavior
- **WHEN** API and CLI generate live signals
- **THEN** both use the same date, active-list, panel, registry, conversion, persistence, and source behavior

### Requirement: Preserve pure strategy signal generation boundary
The system SHALL keep session-based loading/persistence outside the generic signal-generation wrapper and concrete strategies. Generic generation SHALL accept injected active ETFs, a price panel, and typed strategy config; it SHALL use only an optional callback for persistence.

#### Scenario: Pure generation remains injected-input only
- **WHEN** backend code calls generic single-date or historical generation
- **THEN** no database session or strategy-specific lookup is required
- **AND** no `MarketPrice` query, flush, commit, or direct persistence occurs

## ADDED Requirements

### Requirement: Pluggable strategy dispatch for signal generation
Live and historical signal-generation entry points SHALL resolve the selected strategy from the config through the registry. They SHALL not import or directly invoke concrete strategy implementations.

#### Scenario: Live signal dispatches via registry
- **WHEN** live generation uses a dual-momentum config
- **THEN** the registry returns a parameter-bound dual-momentum strategy
- **AND** the shared wrapper invokes its protocol

#### Scenario: Historical signal dispatches via registry
- **WHEN** historical generation uses an equal-weight config
- **THEN** every rebalance date invokes equal weight through the protocol
- **AND** no type branch exists in the loop

#### Scenario: Strategy-specific setup stays inside strategy
- **WHEN** a concrete strategy needs derived data such as a defense lookup
- **THEN** it derives that data from injected inputs inside its implementation

### Requirement: Generic signal entry-point compatibility
The public names `generate_strategy_signal`, `generate_historical_strategy_signals`, `GenerateStrategySignalResult`, and `GeneratedSignalPosition` SHALL remain importable from their existing core module/package paths. The generation function signatures MAY remove the dual-momentum-specific `defense_lookup` argument as part of the documented breaking Python API change.

#### Scenario: Existing generic imports remain available
- **WHEN** in-repo callers import the generic generation functions and result/position types
- **THEN** import resolution succeeds without a second competing type

#### Scenario: Removed defense lookup is reported as breaking
- **WHEN** a caller migrates from the old direct function signature
- **THEN** it supplies active_etfs, price_panel, and typed config only
- **AND** dual momentum constructs its own lookup
