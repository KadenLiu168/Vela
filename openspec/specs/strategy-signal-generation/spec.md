# strategy-signal-generation Specification

## Purpose
Defines pure-function strategy signal generation from injected inputs (no DB session, no `MarketPrice` queries): trend filtering, momentum scoring, ranking, and defensive fallback.
## Requirements
### Requirement: Generate strategy signal from local market data

The system SHALL generate a strategy signal for a requested signal date using the active ETFs and the strategy configuration supplied by the caller, plus a price panel mapping already loaded for the relevant trading-date window. The signal generation function SHALL NOT accept a database session and SHALL NOT issue `MarketPrice` queries during generation.

#### Scenario: Generate ranked strategy signal from injected inputs
- **WHEN** backend code generates a strategy signal for a date with a non-empty active ETF list, a price panel covering the longest configured window, and a strategy configuration
- **THEN** the function reads only from the injected inputs and the configured `StrategyConfig`
- **AND** the function applies the configured trend filter before ranking eligible ETFs
- **AND** the function calculates configured momentum scores for ETFs that pass the trend filter
- **AND** the function returns the selected target positions with rank, score, and target weight

#### Scenario: Generate signal performs zero MarketPrice queries
- **WHEN** backend code generates a strategy signal for a date through the pure-function entry point
- **THEN** no SQL statement targets the `market_price` table during the call

#### Scenario: Persistence is delegated to the caller via callback
- **WHEN** backend code generates a strategy signal and supplies a persist callback
- **THEN** the function invokes the callback with the generated result
- **AND** the function does not commit, flush, or otherwise write to the database when no callback is supplied

#### Scenario: Apply defensive fallback during generation
- **WHEN** backend code generates a strategy signal and fewer eligible ranked ETFs exist than the configured Top N
- **THEN** the system returns one target position per configured defensive asset
- **AND** each defensive position has an equal target weight of `1 / N` where `N` is the number of configured defensive assets
- **AND** the sum of the defensive target weights equals `1.0` within Decimal rounding tolerance (each weight is `Decimal("1") / Decimal(N)`; the total is approximately, not exactly, `1.0` for N > 1)
- **AND** each defensive asset id is resolved from the caller-supplied defense lookup without issuing any database query

#### Scenario: Fail when no active ETFs exist
- **WHEN** backend code generates a strategy signal and the caller-supplied active ETF list is empty
- **THEN** the function returns a failed result with a clear error message
- **AND** the function does not raise

#### Scenario: Fail when defensive asset is missing locally
- **WHEN** backend code generates a fallback signal and any configured defensive asset exchange and symbol are not present in the caller-supplied defense lookup
- **THEN** the function returns a failed result with a clear error message

### Requirement: Export latest strategy signal report

The system SHALL provide a core report export helper that formats the latest successful persisted strategy signal as human-readable text.

#### Scenario: Export latest successful signal report
- **WHEN** backend code exports a report for a config version with at least one successful persisted strategy signal
- **THEN** the report includes the signal date, config version, signal id, generated timestamp, result, and fallback status
- **AND** the report includes each selected ETF with exchange, symbol, target weight, rank, score, and fallback status

#### Scenario: Export date-constrained signal report
- **WHEN** backend code exports a report for a config version and signal date
- **THEN** the report uses the latest successful persisted signal for that exact config version and signal date

#### Scenario: Report fallback signal
- **WHEN** backend code exports a report for a persisted defensive fallback signal
- **THEN** the report marks fallback status as active
- **AND** the fallback position shows no rank or score value

#### Scenario: No successful signal exists
- **WHEN** backend code exports a report and no matching successful strategy signal exists
- **THEN** the helper reports that no latest successful strategy signal is available

### Requirement: Generate historical strategy signals

The system SHALL generate strategy signals for historical rebalance dates from a price panel and active ETF list supplied by the caller, without issuing per-rebalance `MarketPrice` queries.

#### Scenario: Generate signals for historical rebalance dates with weekly frequency
- **WHEN** backend code generates historical strategy signals from a sequence of historical trading dates with `rebalance.frequency` set to `weekly` and a caller-supplied price panel
- **THEN** the system derives weekly rebalance dates from those trading dates
- **AND** the system generates one strategy signal for each derived rebalance date using the injected price panel
- **AND** the generated results are returned in ascending signal date order

#### Scenario: Generate signals for historical rebalance dates with monthly frequency
- **WHEN** backend code generates historical strategy signals from a sequence of historical trading dates with `rebalance.frequency` set to `monthly` and a caller-supplied price panel
- **THEN** the system derives monthly rebalance dates from those trading dates
- **AND** the system generates one strategy signal for each derived rebalance date using the injected price panel
- **AND** the generated results are returned in ascending signal date order

#### Scenario: Historical generation does not use future data
- **WHEN** backend code generates a historical strategy signal for a rebalance date that has later market prices available in the injected panel
- **THEN** strategy calculations for that signal use only panel entries with `trade_date` on or before that rebalance date

#### Scenario: Historical signal positions are persisted via callback
- **WHEN** historical strategy signal generation produces target positions for a rebalance date and the caller supplied a persist callback
- **THEN** the persist callback is invoked once per rebalance date with the generated result
- **AND** no database write occurs when no callback is supplied

#### Scenario: Empty historical trading dates
- **WHEN** backend code generates historical strategy signals from an empty trading-date sequence
- **THEN** the system returns an empty result list
- **AND** no strategy signal rows are persisted

#### Scenario: Monthly frequency produces fewer signals than weekly
- **WHEN** backend code generates historical strategy signals over the same trading-date sequence with weekly frequency and then with monthly frequency
- **THEN** the number of generated monthly-frequency signals is strictly less than the number of generated weekly-frequency signals

### Requirement: Generate and persist single-date strategy signal in core

The system SHALL provide a core service that generates and persists a single-date strategy signal from a SQLAlchemy session, a loaded strategy configuration, and an optional signal date. The service SHALL own the shared workflow for resolving the signal date, loading active ETFs, loading the price panel, building the defensive ETF lookup, invoking pure strategy signal generation, converting generated positions into persistence inputs, and persisting the signal result.

#### Scenario: Generate and persist using latest local market date
- **WHEN** backend code calls the core service without an explicit signal date and local market prices exist
- **THEN** the service uses the latest local `MarketPrice.trade_date` as the signal date
- **AND** the service persists one strategy signal row for the loaded strategy id and config version
- **AND** the service persists the generated signal positions
- **AND** the service returns a `GenerateStrategySignalResult` containing the persisted signal id

#### Scenario: Generate and persist using explicit signal date
- **WHEN** backend code calls the core service with an explicit signal date
- **THEN** the service generates and persists the strategy signal for that exact date
- **AND** the service does not replace the explicit date with the latest local market date

#### Scenario: Missing local market prices
- **WHEN** backend code calls the core service without an explicit signal date and no local market prices exist
- **THEN** the service raises a clear error indicating that no local market prices were found
- **AND** no strategy signal row is persisted

#### Scenario: Core service shares API and CLI persistence behavior
- **WHEN** the HTTP API endpoint and CLI command generate a strategy signal
- **THEN** both paths delegate signal workflow orchestration to the same core service
- **AND** both paths use the same active ETF loading, price panel loading, defensive lookup construction, persistence input conversion, and persistence behavior

### Requirement: Preserve pure strategy signal generation boundary

The system SHALL keep the pure strategy signal generation function separate from session-based persistence orchestration.

#### Scenario: Pure generation remains injected-input only
- **WHEN** backend code calls the pure strategy signal generation function
- **THEN** the function accepts injected active ETFs, price panel, defensive lookup, and strategy configuration
- **AND** the function does not require a database session
- **AND** the function does not issue `MarketPrice` queries during generation

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

