## ADDED Requirements

### Requirement: YAML-defined parameter space
The system SHALL load parameter search space definitions from a YAML configuration file, where each parameter is described by a unique dot-path name relative to the complete strategy configuration root, a type (int_range, float_range, or choice), and value bounds. The parameter space SHALL NOT contain any strategy-specific logic. Range steps SHALL be positive, range low SHALL be less than or equal to high, and choice values SHALL be non-empty.

#### Scenario: Integer range parameter
- **WHEN** a parameter is defined with type `int_range`, low=20, high=100, step=20
- **THEN** the system generates values [20, 40, 60, 80, 100].

#### Scenario: Choice parameter
- **WHEN** a parameter is defined with type `choice` and values [60, 120, 250]
- **THEN** the system generates exactly those three values.

#### Scenario: Float range parameter
- **WHEN** a parameter is defined with type `float_range`, low=0.2, high=0.6, step=0.1
- **THEN** the system uses decimal stepping and generates [0.2, 0.3, 0.4, 0.5, 0.6] without binary floating-point accumulation changing the count.

#### Scenario: Invalid parameter definitions
- **WHEN** names are duplicated, a choice has no values, a range step is non-positive, or a range has low greater than high
- **THEN** walk-forward configuration validation fails before any backtest executes.

### Requirement: Grid search combination generation
The system SHALL generate all combinations of parameter values from the parameter space, producing a list of flat dictionaries where keys are dot-path parameter names and values are the parameter values.

#### Scenario: Two parameters with two values each
- **WHEN** the parameter space has two parameters A (values [1, 2]) and B (values [10, 20])
- **THEN** the system generates 4 combinations: [{A:1, B:10}, {A:1, B:20}, {A:2, B:10}, {A:2, B:20}].

### Requirement: StrategyConfig construction via deep merge
The system SHALL construct a valid StrategyConfig for each parameter combination by copying the base strategy configuration dict, assigning every dot-path value into that copy without mutating the base dict, then validating through the existing `validate_strategy_config()` function.

#### Scenario: Valid combination produces config
- **WHEN** a combination {parameters.momentum.short_window_days: 20, parameters.momentum.long_window_days: 80} is merged into a valid base config
- **THEN** `validate_strategy_config()` returns a valid `DualMomentumStrategyConfig` with those momentum window values.

#### Scenario: Invalid combination rejected by pydantic
- **WHEN** a combination {parameters.momentum.short_window_days: 100, parameters.momentum.long_window_days: 80} violates the short < long constraint
- **THEN** `validate_strategy_config()` raises a `ValidationError` and the combination is skipped.

#### Scenario: Unknown dot path is rejected
- **WHEN** a combination assigns an unknown root or nested field
- **THEN** existing strategy validation rejects the merged configuration and the combination is skipped.

### Requirement: Memory database for search phase
Before executing any search backtest, the system SHALL use SQLite backup to create a point-in-time in-memory copy of the source database connected to the caller's session. The copy SHALL include the current schema and all input rows required by `run_backtest()`. Search backtests SHALL read and write only the in-memory copy, ensuring no search-phase signals, runs, or curve rows are persisted to the source database.

#### Scenario: Memory snapshot includes inputs
- **WHEN** the system starts parameter search
- **THEN** its in-memory database contains the source ETF metadata, market prices, trading calendar, and current schema before the first training backtest.

#### Scenario: Search backtest uses memory database
- **WHEN** the system runs a training-window backtest for a parameter combination during search
- **THEN** the backtest SHALL use the in-memory snapshot session and SHALL NOT add search-phase signals, runs, or curves to the source database.

#### Scenario: OOS evaluation uses source database
- **WHEN** the system runs the final OOS evaluation backtest with the best parameters
- **THEN** the backtest SHALL use the caller's source database session and persist its normal signals, run, and curve rows.

### Requirement: Error handling for failed parameter combinations
The system SHALL handle configuration-validation failures, backtest exceptions, non-success backtest statuses, and missing objective values for individual parameter combinations as skipped combinations. It SHALL roll back the failed combination's in-memory transaction, log its parameter values and reason, and continue without catching process-control exceptions such as `KeyboardInterrupt` or `SystemExit`.

#### Scenario: Single combination fails
- **WHEN** one parameter combination fails validation or backtest execution
- **THEN** the system rolls back that combination, logs a warning with the parameter values and reason, and continues with the remaining combinations.

#### Scenario: Failed combinations reported
- **WHEN** the walk-forward run completes and some combinations were skipped due to errors
- **THEN** the final report SHALL include a count of skipped combinations and a summary of the failure reasons.

#### Scenario: All combinations are unscorable
- **WHEN** every combination in a window is skipped or has a null objective value
- **THEN** the walk-forward run fails clearly before executing an OOS or baseline backtest for that window.
