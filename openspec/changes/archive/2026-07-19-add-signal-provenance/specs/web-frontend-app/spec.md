## ADDED Requirements

### Requirement: Signals list shows a Source column

The web Signals list SHALL render a "Source" column for each signal, derived from the API `source` field, using a distinct visual badge per value.

#### Scenario: Source badges are distinguishable
- **WHEN** the Signals list renders signals
- **THEN** a `manual` signal shows a neutral badge labeled "Manual"
- **AND** a `scheduled` signal shows an info badge labeled "Scheduled"
- **AND** a `backtest` signal shows an accent badge labeled "Backtest"
- **AND** a `legacy` signal shows a muted badge labeled "Legacy"
- **AND** the legacy badge exposes accessible explanatory text that the signal predates provenance tracking

#### Scenario: Existing columns preserved
- **WHEN** the Signals list renders
- **THEN** the existing columns (Signal, Signal date, Config version, Result, Generated at) remain
- **AND** pagination behavior is unchanged

### Requirement: Signal detail shows source and backtest link

The Signal detail view SHALL display the signal `source` and, when `source` is `backtest` and `backtest_run_id` is present, SHALL render a link to `/backtests/{backtest_run_id}`.

#### Scenario: Backtest signal links to its run
- **WHEN** a user opens a signal whose `source` is `backtest` with a non-null `backtest_run_id`
- **THEN** the detail view shows a link to the producing backtest run
- **AND** activating the link navigates to that backtest's detail

#### Scenario: Live signal shows no backtest link
- **WHEN** a user opens a `manual` or `scheduled` signal
- **THEN** the detail view shows the source without a backtest link

### Requirement: Backtest detail lists its signals

The backtest detail view SHALL show the API `signal_count`, list every id from `signal_ids`, and link each id to `/signals/{signal_id}`.

#### Scenario: Backtest detail enumerates signals
- **WHEN** a user opens a backtest run detail
- **THEN** the view shows the run's signals, each linking to its Signal detail page
- **AND** the count matches the API `signal_count`

#### Scenario: Backtest with no linked signals shows an empty state
- **WHEN** a user opens a backtest whose `signal_ids` array is empty
- **THEN** the view shows a zero signal count
- **AND** it renders an explicit no-linked-signals empty state
