## 1. Tests

- [x] 1.1 Add tests that load and validate `config/strategy_v1.yaml` with the strategy configuration schema.
- [x] 1.2 Add tests that reject missing required strategy parameter groups.
- [x] 1.3 Add tests that reject invalid momentum windows, invalid score weights, invalid Top N, and negative transaction costs.
- [x] 1.4 Add tests that verify the defensive asset requires explicit exchange and symbol fields.

## 2. Implementation

- [x] 2.1 Create `config/strategy_v1.yaml` with version, momentum, selection, defensive asset, and transaction cost parameters.
- [x] 2.2 Add Pydantic models for the strategy configuration contract in the core package.
- [x] 2.3 Add a small loader that reads YAML strategy config files and returns the validated schema model.
- [x] 2.4 Keep the implementation independent from signal generation, backtesting, database models, and CLI commands.

## 3. Verification

- [x] 3.1 Run the focused strategy configuration tests.
- [x] 3.2 Run the full test suite.
- [x] 3.3 Run `ruff check .`.
- [x] 3.4 Run `openspec status --change "add-strategy-v1-config"` and confirm the change is apply-ready.
