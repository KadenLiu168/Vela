## ADDED Requirements

### Requirement: Dashboard market data fetch result summary
The web frontend SHALL render a Dashboard operation summary from the real market data fetch API response after a fetch request completes.

#### Scenario: Dashboard shows successful fetch counts
- **WHEN** the Dashboard market data fetch request returns a `success` response
- **THEN** the operation summary shows fetched, inserted, and updated row counts from the response
- **AND** the summary does not show failed symbol guidance

#### Scenario: Dashboard shows partial fetch failures
- **WHEN** the Dashboard market data fetch request returns a `partial` response
- **THEN** the operation summary shows fetched, inserted, and updated row counts from the response
- **AND** it shows the failed symbols from the response
- **AND** it shows the response error summary when one is provided
- **AND** it guides the user to retry or check the data source or local data state

#### Scenario: Dashboard shows failed fetch details
- **WHEN** the Dashboard market data fetch request returns a `failed` response
- **THEN** the operation summary shows the failed symbols from the response
- **AND** it shows the response error summary when one is provided
- **AND** it guides the user to retry or check the data source or local data state

#### Scenario: Dashboard validates against real fetch response contract
- **WHEN** frontend validation calls the local API market data fetch endpoint through the shared client
- **THEN** the response includes the status, fetched row count, inserted row count, updated row count, failed symbols, and error summary fields that the Dashboard operation summary renders
