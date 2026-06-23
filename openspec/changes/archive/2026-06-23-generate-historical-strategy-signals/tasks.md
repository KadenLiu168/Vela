## 1. Historical Signal Generation

- [x] 1.1 Add a core helper that derives weekly rebalance dates from historical trading dates.
- [x] 1.2 Reuse existing single-date signal generation for each derived rebalance date and return results in date order.
- [x] 1.3 Export the historical generation helper from the core package public API.

## 2. Tests

- [x] 2.1 Cover generation on historical rebalance dates with persisted target positions.
- [x] 2.2 Cover no-future-data behavior by ensuring later prices do not affect an earlier historical signal.
- [x] 2.3 Cover empty historical trading dates returning no results and persisting no signal rows.

## 3. Validation

- [x] 3.1 Run the focused strategy signal generation tests.
- [x] 3.2 Run project test/lint checks available for this repository.
- [x] 3.3 Run OpenSpec validation for the change.
