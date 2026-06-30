## ADDED Requirements

### Requirement: Dashboard strategy configuration summary
The web frontend SHALL render the Dashboard strategy panel as a read-only summary of the current strategy configuration from the dashboard aggregate response.

#### Scenario: Dashboard shows current strategy configuration summary
- **WHEN** the Dashboard route receives a successful dashboard aggregate response containing strategy configuration fields
- **THEN** the strategy panel shows the strategy id and version
- **AND** it shows the configured momentum windows
- **AND** it shows the configured score weights
- **AND** it shows the configured Top N selection
- **AND** it shows the configured defensive asset
- **AND** it shows the configured transaction cost summary

#### Scenario: Dashboard strategy summary uses API data
- **WHEN** frontend validation renders the Dashboard route with a dashboard aggregate API response
- **THEN** the visible strategy configuration values come from the response strategy object
- **AND** the page code uses the shared dashboard API client helper instead of static configuration constants

#### Scenario: Dashboard strategy summary is read-only
- **WHEN** the Dashboard route renders the strategy configuration summary
- **THEN** it does not provide controls or links for editing strategy configuration
