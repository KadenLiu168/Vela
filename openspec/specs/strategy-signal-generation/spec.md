# strategy-signal-generation Specification

## Purpose
Defines pure-function strategy signal generation from injected inputs (no DB session, no `MarketPrice` queries): trend filtering, momentum scoring, ranking, and defensive fallback.
## Requirements
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

### Requirement: Export latest strategy signal report

The system SHALL provide a core report export helper that formats the latest successful persisted
strategy signal for an exact, case-sensitive `strategy_id` and `config_version` as human-readable
text.

#### Scenario: Export latest successful signal report
- **WHEN** backend code exports a report for a strategy id and config version with at least one successful persisted strategy signal
- **THEN** the report includes the signal date, config version, signal id, generated timestamp, result, and fallback status
- **AND** the report includes each selected ETF with exchange, symbol, target weight, rank, score, and fallback status
- **AND** signals belonging to other strategies or config versions are ignored

#### Scenario: Export date-constrained signal report
- **WHEN** backend code exports a report for a strategy id, config version, and signal date
- **THEN** the report uses the latest successful persisted signal for that exact strategy id, config version, and signal date

#### Scenario: Report fallback signal
- **WHEN** backend code exports a report for a persisted defensive fallback signal
- **THEN** the report marks fallback status as active
- **AND** the fallback position shows no rank or score value

#### Scenario: No successful signal exists
- **WHEN** backend code exports a report and no matching successful strategy signal exists for the given strategy id and config version
- **THEN** the helper reports that no latest successful strategy signal is available

### Requirement: Generate historical strategy signals
The system SHALL derive rebalance dates with the shared rebalance-date logic and generate one result
per date with the same shared single-date result, expected-failure, and optional callback
persistence semantics. It SHALL resolve the selected bound strategy once per historical generation
call, derive its non-negative required history from `lookback_days()`, and use indexed boundaries
over each caller-supplied ascending ETF price series. Each eligible ETF's per-date strategy input
SHALL contain only rows on or before the rebalance date and no more than the declared number of
prior observations plus the signal-date observation. Historical orchestration SHALL remain
strategy-agnostic, issue no per-rebalance `MarketPrice` query, return ascending results, and preserve
inception-date eligibility.

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

#### Scenario: Historical generation resolves strategy once
- **WHEN** historical generation produces multiple rebalance dates for one typed config
- **THEN** registry dispatch creates one parameter-bound strategy for the historical call
- **AND** every rebalance invocation uses that same bound strategy without branching on type

#### Scenario: Historical generation uses bounded declared history
- **WHEN** a strategy declares a lookback of N prior sessions and a longer ascending price history is
  present
- **THEN** each eligible ETF input contains at most N prior observations plus an available
  rebalance-date observation
- **AND** changing the backtest start/end span without changing N does not enlarge a per-date
  strategy window beyond that bound

#### Scenario: Historical generation does not use future data
- **WHEN** later prices exist in the injected panel
- **THEN** the per-date strategy input contains only rows on or before that rebalance date

#### Scenario: Historical generation preserves inception eligibility
- **WHEN** an ETF has a declared inception date within the injected history
- **THEN** the ETF is absent before its inception date
- **AND** its bounded input on or after inception contains no stored row before inception

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

#### Scenario: Unsorted injected series is rejected
- **WHEN** an ETF price sequence supplied to historical generation is not ascending by trade date
- **THEN** generation fails clearly before using a binary-search boundary
- **AND** it does not silently produce a reordered or look-ahead-contaminated signal

#### Scenario: Long-history preparation remains lookback-bounded
- **WHEN** a controlled long-history panel is generated across many rebalance dates
- **THEN** the cumulative rows supplied to strategy invocations do not exceed the sum of each
  eligible ETF's `lookback_days() + 1` bound per rebalance
- **AND** generated results match the controlled pre-optimization expectations

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

### Requirement: Persist strategy signal records provenance

The core `persist_strategy_signal` helper SHALL require a `source` argument for every persisted signal and SHALL accept an optional `backtest_run_id`. The helper SHALL write both values onto the `strategy_signal` row.

#### Scenario: Live signal persisted with source
- **WHEN** the live generation path persists a signal with `source="manual"` or `source="scheduled"`
- **THEN** the persisted row's `source` equals the supplied value
- **AND** the persisted row's `backtest_run_id` is null

#### Scenario: Backtest signal persisted with source and run id
- **WHEN** the backtest generation path persists each signal with `source="backtest"` and `backtest_run_id=None`, then links them to the run
- **THEN** each linked signal row's `source` equals `backtest`
- **AND** each linked signal row's `backtest_run_id` equals the producing `backtest_run.id`

#### Scenario: Caller must supply source
- **WHEN** backend code calls `persist_strategy_signal` without a `source`
- **THEN** the call fails at the persistence layer (the parameter is required)

### Requirement: Live generation accepts a caller-supplied source

The core live generation service SHALL accept a `source` argument (default `manual`) and pass it through to persistence. The HTTP generate endpoint and CLI SHALL forward an optional caller-supplied `source` (restricted to `manual` or `scheduled`) and default to `manual` when omitted.

#### Scenario: Default live source is manual
- **WHEN** backend code generates a live signal without specifying `source`
- **THEN** the persisted signal's `source` is `manual`

#### Scenario: Scheduled live source is recorded
- **WHEN** an automated caller requests live signal generation with `source="scheduled"`
- **THEN** the persisted signal's `source` is `scheduled`
- **AND** no scheduler or automation engine is created by this requirement

#### Scenario: Live endpoint rejects backtest source
- **WHEN** a client requests live signal generation with `source="backtest"`
- **THEN** the endpoint rejects the request (HTTP 400) because `backtest` is reserved for backtest runs

#### Scenario: Core live service rejects non-live source
- **WHEN** backend code calls the live generation service with `source="backtest"`, `source="legacy"`, or an unknown value
- **THEN** the service raises before persisting a signal

### Requirement: Backtest run links its signals

`run_backtest` SHALL capture every `strategy_signal_id` it produces; each signal SHALL be persisted up front with `source="backtest"` and `backtest_run_id=None`, and after the `backtest_run` row is created, exactly those captured signals SHALL have their `backtest_run_id` set to that run id (and no other signal's) before the caller-managed transaction commits.

#### Scenario: Every signal from a run is linked
- **WHEN** a backtest run completes and persists signals across its rebalance dates
- **THEN** each of those signal rows has `backtest_run_id` equal to the run id
- **AND** each has `source="backtest"`
- **AND** no signal outside the run receives that `backtest_run_id`

#### Scenario: Link helper is testable in isolation
- **WHEN** a core helper links a set of signal ids to a run id
- **THEN** it updates only distinct supplied ids that are unlinked and already have `source="backtest"`
- **AND** it verifies that the affected-row count equals the number of distinct supplied ids
- **AND** it raises on a missing, non-backtest, or already-linked id instead of accepting a partial link

#### Scenario: Empty link input is a no-op
- **WHEN** the link helper receives no signal ids
- **THEN** it performs no update and returns without error

#### Scenario: Missing persisted id does not commit partial provenance
- **WHEN** any historical generation result unexpectedly has a null `strategy_signal_id`
- **THEN** `run_backtest` raises before commit
- **AND** callers using the managed session boundary roll back the run and its signals

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
