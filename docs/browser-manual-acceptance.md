# Browser Manual Acceptance Checklist

Use this checklist for local browser acceptance and regression checks of the Phase 1 Vela web workflow.

## Legend

- Backend data required: needs `uv run vela-api` and local SQLite data from `uv run python -m tests.integration_data` or records produced by the workflow.
- Browser only: can be checked with only the Vite dev server and mocked or unavailable backend behavior.

## Setup

- [ ] Start the frontend: `npm --prefix apps/web run dev`.
- [ ] For empty API-backed checks, prepare an empty local database: `uv run python -m tests.integration_data --empty`.
- [ ] For success API-backed checks, prepare seeded local data: `uv run python -m tests.integration_data`.
- [ ] For API-backed checks, start the API: `uv run vela-api`.
- [ ] Open the frontend route shown by Vite, typically `http://localhost:5173/`.

The integration data preparation commands reset the default local SQLite database unless `--no-reset` is provided.

## Dashboard

Route: `/`

### Empty State

- [ ] Backend data required: with an empty local SQLite workflow state, open the Dashboard.
- [ ] Confirm the market data panel shows zero price rows and zero covered ETFs.
- [ ] Confirm the latest signal panel explains that no successful local signal exists yet.
- [ ] Confirm the recent backtest panel explains that no local backtest run exists yet.
- [ ] Confirm empty states point to local operations and do not mention login, accounts, hosting, or deployment.

### Error State

- [ ] Browser only: stop the local API service or use a frontend API base URL that cannot be reached.
- [ ] Refresh the Dashboard.
- [ ] Confirm the page layout remains visible.
- [ ] Confirm the Dashboard shows an API unavailable message instead of silently hiding workflow areas.

### Success State

- [ ] Backend data required: seed deterministic local data or complete the workflow steps below.
- [ ] Open the Dashboard and wait for loading to finish.
- [ ] Confirm market data status shows price rows, covered ETF count, earliest trade date, and latest trade date.
- [ ] Confirm strategy summary shows strategy id, version, momentum windows, score weights, Top N, defensive asset, and transaction cost.
- [ ] Confirm latest signal summary shows signal date, result, fallback status, and target holding count when a signal exists.
- [ ] Confirm recent backtest summary shows date range, status, total return, max drawdown, and Sharpe ratio when a backtest exists.
- [ ] Click `Refresh Dashboard` and confirm the Dashboard reloads without losing successful data.

## Market Data Fetch

Dashboard area: operation controls on `/`

### Empty State

- [ ] Backend data required: start from an empty or reset local SQLite workflow state.
- [ ] Confirm the market data panel identifies fetching market data as the next operation.
- [ ] Confirm the fetch action is available from the Dashboard.

### Error State

- [ ] Backend data required: run the API with a configuration or provider state that causes the fetch request to fail, or stop the API before submitting.
- [ ] Trigger the market data fetch action.
- [ ] Confirm duplicate submissions are disabled while the request is pending.
- [ ] Confirm the Dashboard shows a concise market data fetch error summary.
- [ ] Confirm the page remains usable after the failed operation.

### Success State

- [ ] Backend data required: run the local API with market data fetch support.
- [ ] Trigger the incremental market data fetch action from the Dashboard.
- [ ] Confirm the action shows an in-progress state while the request is pending.
- [ ] Confirm the success summary includes fetched, inserted, and updated row counts.
- [ ] Confirm the Dashboard refreshes and market data status reflects persisted local rows.

Real external market data availability can vary. For stable local regression, prefer seeded SQLite data or controlled provider validation for the primary success-path evidence.

## Signal Generation

Dashboard area: operation controls on `/`

### Empty State

- [ ] Backend data required: use a local SQLite state with no successful signal.
- [ ] Confirm the Dashboard latest signal panel explains that no successful local signal exists.
- [ ] Confirm the signal generation action is available from the Dashboard.

### Error State

- [ ] Backend data required: use a local state with insufficient market data, invalid API configuration, or stop the API before submitting.
- [ ] Trigger signal generation from the Dashboard.
- [ ] Confirm duplicate submissions are disabled while the request is pending.
- [ ] Confirm a signal generation error summary is visible.
- [ ] Confirm the Dashboard remains available for retry after the failed operation.

### Success State

- [ ] Backend data required: use seeded local market data or run market data fetch first.
- [ ] Trigger signal generation from the Dashboard.
- [ ] Confirm the success summary shows signal id, signal date, result, and target holding count.
- [ ] Confirm the Dashboard latest signal panel updates to the generated signal.
- [ ] Confirm the Signal Detail route can display the generated signal data.

## Backtest Execution

Dashboard area: backtest form on `/`

### Empty State

- [ ] Backend data required: use a local SQLite state with no recorded backtest run.
- [ ] Confirm the recent backtest panel explains that no local backtest run exists.
- [ ] Confirm the run-backtest entry point is available from the Dashboard.

### Error State

- [ ] Browser only: submit the backtest form with missing or invalid dates.
- [ ] Confirm the browser shows the validation message and does not submit the request.
- [ ] Backend data required: with valid dates but insufficient backend data or stopped API, submit the form.
- [ ] Confirm a backtest run error summary is visible.
- [ ] Confirm the form remains usable for correction and retry.

### Success State

- [ ] Backend data required: use seeded local market data and signal data, or complete market data fetch and signal generation first.
- [ ] Enter a valid start date and end date.
- [ ] Submit the backtest form.
- [ ] Confirm the in-progress state prevents duplicate submissions.
- [ ] Confirm the success summary shows run id, status, date range, trading day count, signal count, and key metrics.
- [ ] Confirm the Dashboard recent backtest panel refreshes with the new run.
- [ ] Confirm the Backtest Detail route can display the generated run.

## Signal Detail

Route: `/signals`

### Empty State

- [ ] Backend data required: use a local SQLite state with no successful signal.
- [ ] Open the Signal Detail route.
- [ ] Confirm the page explains that no successful local signal exists yet and directs the user to generate a signal from the Dashboard.

### Error State

- [ ] Browser only: stop the local API service or use an unreachable API base URL.
- [ ] Open or refresh the Signal Detail route.
- [ ] Confirm an unavailable latest-signal API message is visible.

### Success State

- [ ] Backend data required: use seeded local signal data or generate a signal from the Dashboard.
- [ ] Open the Signal Detail route.
- [ ] Confirm the page shows signal id, signal date, config version, result, fallback status, and generated timestamp.
- [ ] Confirm the target holdings table shows exchange, symbol, target weight, rank, score, and fallback values.
- [ ] If the signal has no positions, confirm the page shows the target-holdings empty state instead of a broken table.

## Backtest Detail

Route: `/backtests/1`

### Empty State

- [ ] Backend data required: use a local SQLite state where the selected run id does not exist.
- [ ] Open `/backtests/999999`.
- [ ] Confirm the page reports that the backtest run was not found.
- [ ] Backend data required: use or create a run with no valid equity curve points.
- [ ] Confirm the equity curve section shows the empty or single-point state instead of a broken chart.

### Error State

- [ ] Browser only: stop the local API service or use an unreachable API base URL.
- [ ] Open or refresh a Backtest Detail route.
- [ ] Confirm an unavailable backtest detail API message is visible.

### Success State

- [ ] Backend data required: use seeded local backtest data or run a backtest from the Dashboard.
- [ ] Open a Backtest Detail route for an existing run id.
- [ ] Confirm the page shows run id, strategy, config version, date range, status, timestamps, and error message field.
- [ ] Confirm metric cards show total return, annualized return, max drawdown, volatility, and Sharpe ratio.
- [ ] Confirm the equity curve section shows point count, start point, end point, min net value, and max net value.
- [ ] Confirm the parameters section renders the run parameters summary.

## Completion Criteria

- [ ] Dashboard empty, error, and success states have been checked.
- [ ] Market data fetch empty, error, and success states have been checked.
- [ ] Signal generation empty, error, and success states have been checked.
- [ ] Backtest execution empty, error, and success states have been checked.
- [ ] Signal Detail empty, error, and success states have been checked.
- [ ] Backtest Detail empty, error, and success states have been checked.
- [ ] Every backend-dependent step was run with a known local API and SQLite data state, or explicitly deferred with the missing data condition noted.
