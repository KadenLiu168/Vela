## MODIFIED Requirements

### Requirement: YAML configuration loading
The system SHALL provide public loader functions that load supported YAML files into typed configuration objects.

#### Scenario: Load ETF pool from path
- **WHEN** backend code calls the ETF pool config loader with a YAML file path
- **THEN** the loader reads the file and returns an ETF pool configuration object

## REMOVED Requirements

### Requirement: Strategy envelope configuration schema
**Reason**: Vela already has the concrete `strategy-configuration` capability and `StrategyConfig` model for strategy parameter validation.
**Migration**: Use `config/strategy_v1.yaml` with `load_strategy_config()` and `StrategyConfig` for strategy configuration.
