## MODIFIED Requirements

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
