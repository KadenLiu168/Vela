## ADDED Requirements

### Requirement: Dashboard market data fetch supports full mode
The web frontend SHALL expose an independent full market-data fetch entry point in the Dashboard Operations action list, wired to the existing `handleMarketDataFetch("full")` handler path and the existing `fetchFullMarketData` client function, which issues `POST /api/market-data/fetch?mode=full`. The pre-existing incremental fetch entry point SHALL remain unchanged and SHALL continue to issue `POST /api/market-data/fetch?mode=incremental`. Both entry points SHALL share the existing `activeOperation` lock (key `"marketDataFetch"`), the existing `marketDataFetchMode` state, and the existing `MarketDataFetchSummary` and `OperationErrorSummary` result and error surfaces. The change SHALL introduce no new component, no new API client function, no new API type, and no new application state.

#### Scenario: Full fetch button triggers the full mode request
- **WHEN** the Dashboard has loaded and the user clicks the "Fetch full" action in the Operations action list
- **THEN** the frontend issues `POST /api/market-data/fetch?mode=full` through the shared API client
- **AND** no `POST /api/market-data/fetch?mode=incremental` request is issued as a side effect of that click

#### Scenario: Incremental fetch button preserves the incremental request
- **WHEN** the user clicks the pre-existing "Fetch market data" action in the Operations action list
- **THEN** the frontend issues `POST /api/market-data/fetch?mode=incremental` through the shared API client
- **AND** the request URL does not contain `mode=full`

#### Scenario: Active operation lock disables the sibling fetch action
- **WHEN** a market-data fetch of either mode is in flight (the `activeOperation` lock is held as `"marketDataFetch"`)
- **THEN** both the incremental and the full fetch buttons are disabled
- **AND** clicking the disabled sibling does not issue a second fetch request

#### Scenario: Each fetch button shows its own in-progress label
- **WHEN** the incremental fetch is in flight
- **THEN** the incremental fetch button displays its in-progress label and the full fetch button displays its idle label
- **WHEN** the full fetch is in flight
- **THEN** the full fetch button displays its in-progress label and the incremental fetch button displays its idle label

#### Scenario: Full fetch result renders through the shared summary
- **WHEN** a `POST /api/market-data/fetch?mode=full` request returns a successful `MarketDataFetchResponse`
- **THEN** the Dashboard renders the `MarketDataFetchSummary` component populated with that response
- **AND** the rendered summary is the same component used for the incremental fetch result
- **WHEN** the request fails with an `ApiClientError`
- **THEN** the Dashboard renders the `OperationErrorSummary` component for the `"marketDataFetch"` operation

#### Scenario: Full fetch refreshes aggregate dashboard data
- **WHEN** a full fetch request returns a response with `status = "success"`
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed market data status reflects the updated price row count and coverage
