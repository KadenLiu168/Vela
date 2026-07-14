## MODIFIED Requirements

### Requirement: Defensive asset identity
The system SHALL represent one or more defensive assets in strategy configuration, each with explicit ETF identity fields.

#### Scenario: Defensive asset uses exchange and symbol
- **WHEN** backend code validates the strategy configuration defensive assets
- **THEN** each defensive asset includes an exchange value
- **AND** each defensive asset includes a symbol value

#### Scenario: At least one defensive asset is required
- **WHEN** backend code validates a strategy configuration with an empty `defense.assets` list
- **THEN** validation fails

#### Scenario: Duplicate defensive assets are rejected
- **WHEN** backend code validates a strategy configuration whose `defense.assets` list contains two entries with the same exchange and symbol
- **THEN** validation fails

#### Scenario: Defensive asset exists in active ETF universe
- **WHEN** backend code loads a strategy configuration with one or more defensive assets
- **THEN** each defensive asset exists in the ETF pool referenced by `universe_config`
- **AND** each matching ETF pool entry is active

#### Scenario: Defensive asset outside active ETF universe is rejected
- **WHEN** backend code loads a strategy configuration whose defensive asset is missing from the referenced ETF pool or is inactive
- **THEN** validation fails with a project-level configuration error identifying `defense.assets[i]`

### Requirement: Versioned strategy configuration file
The system SHALL provide a checked-in `config/strategy_v1.yaml` file for the initial ETF rotation strategy configuration.

#### Scenario: Strategy v1 config defines required parameter groups
- **WHEN** backend code parses `config/strategy_v1.yaml`
- **THEN** the configuration includes momentum window parameters
- **AND** the configuration includes score weight parameters
- **AND** the configuration includes trend filter parameters
- **AND** the configuration includes Top N selection parameters
- **AND** the configuration includes one or more defensive assets (a `defense.assets` list)
- **AND** the configuration includes transaction cost parameters
- **AND** the configuration includes performance metric parameters
