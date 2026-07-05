# web-rebalance-frequency-display Specification

## Purpose
TBD - created by archiving change display-rebalance-frequency. Update Purpose after archive.
## Requirements
### Requirement: Dashboard displays rebalance frequency
The web frontend SHALL display the strategy rebalance frequency on the Dashboard Strategy panel using the same compact-list format as other strategy parameters.

#### Scenario: Weekly rebalance frequency is displayed
- **WHEN** the Dashboard loads and the API returns `strategy.rebalance.frequency` set to `"weekly"`
- **THEN** the Strategy panel displays a row labeled "Rebalance frequency" with the value "Weekly"

#### Scenario: Monthly rebalance frequency is displayed
- **WHEN** the Dashboard loads and the API returns `strategy.rebalance.frequency` set to `"monthly"`
- **THEN** the Strategy panel displays a row labeled "Rebalance frequency" with the value "Monthly"

#### Scenario: Rebalance frequency row placement
- **WHEN** the Dashboard renders the Strategy panel
- **THEN** the rebalance frequency row appears after "Universe" and before any subsequent strategy fields

### Requirement: Dashboard API includes rebalance configuration
The `GET /api/dashboard` endpoint SHALL include the `rebalance` field in the strategy summary section of the response.

#### Scenario: Dashboard response includes rebalance frequency
- **WHEN** a client requests `GET /api/dashboard`
- **THEN** the response `strategy` object includes a `rebalance` field containing a `frequency` value set to `"weekly"` or `"monthly"`

### Requirement: Test fixtures accurately reflect API shape
The web frontend test fixtures SHALL match the actual `DashboardStrategySummary` type and the API response contract.

#### Scenario: Test fixture performance field matches API
- **WHEN** a test constructs a mock `DashboardResponse`
- **THEN** the `strategy.performance` field includes `risk_free_rate` from the `PerformanceConfig` contract
- **AND** `strategy.performance` does NOT include a `rebalance_frequency` field

#### Scenario: Test fixture includes rebalance field
- **WHEN** a test constructs a mock `DashboardResponse`
- **THEN** the `strategy.rebalance` field includes a `frequency` value

