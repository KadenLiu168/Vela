## MODIFIED Requirements

### Requirement: Generate historical strategy signals
The system SHALL derive rebalance dates with shared logic and generate one result per date with the same single-date result, expected-failure, and optional callback semantics. It SHALL resolve the bound strategy once, derive its non-negative `lookback_days()`, and use indexed boundaries over caller-supplied ascending `ResolvedSessionPrice` series. Each eligible ETF input SHALL contain only exact official-session points on or before the rebalance date, from its `listing_date`, and no more than the declared prior-session count plus the signal session. Historical orchestration SHALL remain strategy-agnostic, issue no per-rebalance database query, return ascending results, and retain each point's tradability and resolution evidence.

#### Scenario: Weekly historical generation
- **WHEN** historical dates use weekly frequency
- **THEN** shared logic derives weekly rebalance dates, invokes the bound strategy once per date, and returns ascending results

#### Scenario: Monthly historical generation
- **WHEN** historical dates use monthly frequency
- **THEN** shared logic derives monthly rebalance dates, invokes the bound strategy once per date, and returns ascending results

#### Scenario: Historical generation resolves strategy once
- **WHEN** historical generation produces multiple dates for one typed config
- **THEN** registry dispatch creates one parameter-bound strategy
- **AND** every invocation uses that same bound strategy without branching on type

#### Scenario: Historical generation uses bounded exact sessions
- **WHEN** a strategy declares N prior sessions and a longer complete resolved history is present
- **THEN** each eligible ETF input contains at most N prior official-session points plus the rebalance-session point
- **AND** changing the outer backtest span without changing N does not enlarge that window

#### Scenario: Confirmed halt remains an explicit observation
- **WHEN** a bounded window contains an authoritative full-day non-trading session
- **THEN** the window contains that session's unchanged adjusted value and `tradable = false`
- **AND** it does not substitute an older raw row or collapse two official sessions into one observation

#### Scenario: Historical generation does not use future data
- **WHEN** later resolved points exist in the injected panel
- **THEN** the per-date strategy input contains only points on or before the rebalance date

#### Scenario: Historical generation preserves listing eligibility
- **WHEN** an ETF listing date falls within injected history
- **THEN** the ETF is absent before listing
- **AND** its bounded input on or after listing contains no pre-listing point

#### Scenario: Historical positions are persisted via callback
- **WHEN** a callback is supplied
- **THEN** it is invoked once for every generated result, including expected failures
- **AND** no write occurs without a callback

#### Scenario: Empty historical trading dates
- **WHEN** historical trading dates are empty
- **THEN** the function returns an empty list
- **AND** no strategy or callback is invoked

#### Scenario: Monthly frequency produces fewer signals than weekly
- **WHEN** the same sufficiently long date sequence runs weekly and monthly
- **THEN** monthly generation produces fewer results than weekly generation

#### Scenario: Unsorted injected series is rejected
- **WHEN** an ETF resolved series is not ascending by trade date
- **THEN** generation fails before binary-search use
- **AND** does not reorder or produce look-ahead-contaminated output

#### Scenario: Long-history preparation remains lookback-bounded
- **WHEN** a controlled long panel spans many rebalance dates
- **THEN** cumulative points supplied to strategies do not exceed each eligible ETF's `lookback_days() + 1` bound per date
- **AND** generated results match controlled expectations

#### Scenario: Target retains non-tradable evidence for execution
- **WHEN** a strategy selects an ETF whose resolved rebalance-session point is non-tradable
- **THEN** signal generation retains that desired target and score
- **AND** historical portfolio execution, not ranking, decides when the complete target can execute
