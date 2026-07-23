## MODIFIED Requirements

### Requirement: Versioned strategy configuration file
The system SHALL provide a checked-in `config/strategy_v1.yaml` for the initial ETF rotation strategy. The file SHALL select `type: dual_momentum`, place its momentum, score-weight, trend-filter, selection, and defense groups under `parameters`, and retain the common strategy_id, version, universe_config, rebalance, costs, and performance groups.

#### Scenario: Checked-in config uses the new shape
- **WHEN** backend code parses `config/strategy_v1.yaml`
- **THEN** it selects `type: dual_momentum`
- **AND** dual-momentum groups exist under `parameters`
- **AND** common groups remain at the top level

### Requirement: Strategy configuration schema validation
The system SHALL validate strategy configuration as a top-level Pydantic discriminated union on `type`. Each variant SHALL contain the common fields plus a typed `parameters` model, SHALL forbid unknown fields, and SHALL preserve the selected strategy's validation rules.

#### Scenario: Checked-in strategy config validates
- **WHEN** backend code loads `config/strategy_v1.yaml`
- **THEN** validation produces a dual-momentum config variant with typed dual-momentum parameters

#### Scenario: Parameters are validated per strategy type
- **WHEN** backend code validates a `type: dual_momentum` configuration
- **THEN** its parameters model validates momentum windows, score weights, trend filter, Top N, and defensive assets

#### Scenario: Equal-weight parameters are explicitly empty
- **WHEN** backend code validates `type: equal_weight` with `parameters: {}`
- **THEN** validation succeeds
- **AND** any unknown key inside `parameters` is rejected

#### Scenario: Missing required strategy parameters are rejected
- **WHEN** a selected strategy omits a required parameter
- **THEN** validation fails with a field path under `parameters`

#### Scenario: Invalid momentum windows are rejected
- **WHEN** dual-momentum parameters contain a non-positive momentum window
- **THEN** validation fails

#### Scenario: Invalid momentum window relationship is rejected
- **WHEN** the short momentum window is greater than or equal to the long window
- **THEN** validation fails

#### Scenario: Invalid score weights are rejected
- **WHEN** dual-momentum score weights do not sum to the existing scoring contract
- **THEN** validation fails

#### Scenario: Non-positive score weights are rejected
- **WHEN** either dual-momentum score weight is less than or equal to zero
- **THEN** validation fails

#### Scenario: Invalid trend filter is rejected
- **WHEN** dual-momentum parameters use an unsupported moving-average window or price relation
- **THEN** validation fails

#### Scenario: Invalid Top N is rejected
- **WHEN** dual-momentum `parameters.selection.top_n` is less than one
- **THEN** validation fails

#### Scenario: Invalid transaction cost is rejected
- **WHEN** any strategy config has a negative transaction cost
- **THEN** validation fails

#### Scenario: Invalid risk-free rate is rejected
- **WHEN** any strategy config has a negative performance risk-free rate
- **THEN** validation fails

#### Scenario: Strategy schema validation exposes assertable failure details
- **WHEN** tests validate invalid values through the strategy config adapter
- **THEN** validation identifies the failing field or a project-owned validation message

#### Scenario: Mixed legacy and new fields are rejected
- **WHEN** a config has `type` and `parameters` but also retains a legacy top-level strategy parameter such as `momentum`
- **THEN** validation rejects the unknown top-level field instead of silently ignoring it

### Requirement: Defensive asset identity
The dual-momentum parameters SHALL represent one or more defensive assets, each with explicit exchange and symbol identity. Loader validation SHALL ensure each configured defensive asset exists and is active in the ETF pool referenced by the common `universe_config`. Strategies without defensive parameters SHALL not run this validation.

#### Scenario: Defensive asset uses exchange and symbol
- **WHEN** backend code validates dual-momentum defensive assets
- **THEN** each `parameters.defense.assets` entry contains exchange and symbol

#### Scenario: At least one defensive asset is required
- **WHEN** dual momentum has an empty `parameters.defense.assets` list
- **THEN** validation fails

#### Scenario: Duplicate defensive assets are rejected
- **WHEN** two defensive entries have the same exchange and symbol
- **THEN** validation fails

#### Scenario: Defensive asset exists in active ETF universe
- **WHEN** the loader validates a dual-momentum config
- **THEN** every defensive asset exists as active in the referenced ETF pool

#### Scenario: Defensive asset outside active ETF universe is rejected
- **WHEN** a defensive asset is missing or inactive in the referenced pool
- **THEN** loading fails with a `ConfigError` identifying `parameters.defense.assets[i]`

#### Scenario: Equal weight does not require defensive assets
- **WHEN** the loader validates an equal-weight config
- **THEN** it does not require or validate a defense group

### Requirement: Strategy configuration loader error reporting
The loader SHALL wrap file-read, YAML-parse, adapter-validation, and strategy-specific universe-validation failures in `ConfigError`. It SHALL detect a legacy flat strategy shape with a top-level `momentum` key and no `type`, and fail with a migration message.

#### Scenario: Strategy validation error includes path and field
- **WHEN** strategy config validation fails through the loader
- **THEN** the `ConfigError` includes the file path and failing field path

#### Scenario: Strategy YAML parse error includes path
- **WHEN** YAML cannot be parsed
- **THEN** the `ConfigError` includes the file path and parse context

#### Scenario: Strategy missing file error includes path
- **WHEN** the config path is missing
- **THEN** the `ConfigError` includes that path

#### Scenario: Legacy flat configuration shape is rejected
- **WHEN** a document has a top-level `momentum` key and no `type`
- **THEN** loading raises `ConfigError` explaining the required `type` + `parameters` structure
- **AND** the message points to `config/strategy_v1.yaml`

#### Scenario: Unknown strategy type is rejected during loading
- **WHEN** a document uses an unregistered discriminator value
- **THEN** loading raises `ConfigError` naming the unknown type and file path

### Requirement: Trend filter configuration accepted values
Dual-momentum configuration SHALL accept `parameters.trend_filter.moving_average_days` from `{60, 120, 250}` and `parameters.trend_filter.price_relation` from `{above, below}`. Values outside those sets SHALL be rejected at load time.

#### Scenario: Supported trend filters are accepted
- **WHEN** dual momentum uses 60, 120, or 250 days with above or below
- **THEN** validation succeeds

#### Scenario: Unsupported moving average window is rejected
- **WHEN** dual momentum uses another moving-average window such as 30
- **THEN** validation fails at `parameters.trend_filter.moving_average_days`

#### Scenario: Unsupported price relation is rejected
- **WHEN** dual momentum uses a relation other than above or below
- **THEN** validation fails at `parameters.trend_filter.price_relation`

## ADDED Requirements

### Requirement: Strategy type and version discriminators
Every strategy configuration SHALL require a known `type`. `version` SHALL be any non-empty string and SHALL identify the parameter/configuration version rather than the strategy type.

#### Scenario: Type field is required
- **WHEN** a non-legacy configuration omits `type`
- **THEN** validation fails

#### Scenario: Version must be non-empty
- **WHEN** a configuration has an empty version string
- **THEN** validation fails

#### Scenario: Version accepts non-v1 values
- **WHEN** a configuration uses a non-empty value such as `v2`
- **THEN** validation succeeds if all other fields are valid

### Requirement: Persisted strategy identity is behavior-stable
Because persistence and downstream queries identify strategy behavior by `(strategy_id, config_version)`, one identity pair SHALL NOT be reused for a different `type` or different effective parameters. A strategy-type switch SHALL update the identity pair through configuration, and a parameter change SHALL use a new version.

#### Scenario: Config-only strategy switch uses isolated identity
- **WHEN** a caller switches from dual momentum to equal weight
- **THEN** the equal-weight config uses a distinct `(strategy_id, version)` pair
- **AND** persisted signals and backtest calculations for the two strategies do not select each other's rows

#### Scenario: Parameter revision increments version
- **WHEN** effective parameters change without changing strategy type
- **THEN** the config uses a new non-empty version before new signals are persisted

### Requirement: Serialized strategy configuration is type-aware
The API strategy object used by `/api/config` and `/api/dashboard` SHALL contain common fields plus `type` and typed `parameters`. It SHALL not expose dual-momentum groups as unconditional top-level fields.

#### Scenario: Dual-momentum API shape
- **WHEN** the configured type is dual momentum
- **THEN** the response has `type: dual_momentum`
- **AND** momentum, score_weights, trend_filter, selection, and defense appear under `parameters`

#### Scenario: Equal-weight API shape
- **WHEN** the configured type is equal weight
- **THEN** the response has `type: equal_weight` and `parameters: {}`
- **AND** `/api/dashboard` succeeds without dual-momentum fields
