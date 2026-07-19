## ADDED Requirements

### Requirement: Strategy signal carries provenance

The `strategy_signal` table SHALL store a `source` discriminator and a nullable `backtest_run_id` foreign key on every signal row, so that live-generated signals and backtest-generated signals are distinguishable and linkable.

#### Scenario: source discriminator is required and constrained
- **WHEN** any code persists a strategy signal after this change
- **THEN** the row's `source` value is one of `manual`, `scheduled`, `backtest`, or `legacy`
- **AND** `source` is non-null
- **AND** a named database check constraint rejects any other stored value
- **AND** `legacy` is reserved for rows backfilled by the migration and is never an accepted input value on the generate endpoint

#### Scenario: backtest signals link to their run
- **WHEN** a strategy signal is produced by a backtest run
- **THEN** its `backtest_run_id` equals the producing `backtest_run.id`
- **AND** the `backtest_run` row exposes the signal through its `signals` relationship

#### Scenario: live signals have no backtest link
- **WHEN** a strategy signal is produced by live generation (manual or scheduled)
- **THEN** its `backtest_run_id` is null
- **AND** runtime validation and a named database check reject a manual or scheduled row with a non-null `backtest_run_id`

#### Scenario: legacy rows are explicitly marked
- **WHEN** a strategy signal row existed before provenance tracking was introduced
- **THEN** its `source` is `legacy`
- **AND** its `backtest_run_id` is null

#### Scenario: backtest link is indexed
- **WHEN** backend code inspects the `StrategySignal` model table indexes
- **THEN** an index exists on `backtest_run_id` for loading a run's signals
- **AND** no standalone `source` index is required until a source-filtering query is introduced

#### Scenario: runtime persistence rejects migration-only and unknown sources
- **WHEN** runtime code calls `persist_strategy_signal` with `source="legacy"` or an unknown value
- **THEN** the helper raises before adding a signal row
