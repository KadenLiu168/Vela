## 1. Specification Validation

- [x] 1.1 Run `openspec status --change "define-strategy-signal-model"` and confirm the change is apply-ready.

## 2. Model Tests

- [x] 2.1 Add focused tests for `StrategySignal` required columns, nullable fields, status values, and result values.
- [x] 2.2 Add tests confirming multiple `StrategySignal` rows with the same `signal_date` and `config_version` are allowed.
- [x] 2.3 Add focused tests for `StrategySignalPosition` required columns, nullable `rank` and `score`, and foreign keys.
- [x] 2.4 Add tests confirming duplicate `strategy_signal_id` and `etf_id` position rows are rejected.
- [x] 2.5 Add tests confirming the same ETF can appear in different signal runs and repeated ranks are allowed within one signal run.
- [x] 2.6 Add tests for strategy signal and position lookup indexes.

## 3. ORM Implementation

- [x] 3.1 Add `StrategySignal` with signal date, configuration version, generation timestamp, status, result, optional error message, and audit timestamp fields.
- [x] 3.2 Add `StrategySignalPosition` with signal foreign key, ETF foreign key, optional rank, optional score, target weight, and creation timestamp fields.
- [x] 3.3 Add `StrategySignal.STATUSES` and `StrategySignal.RESULTS` class variables with the supported values from the spec.
- [x] 3.4 Add the unique constraint on `StrategySignalPosition.strategy_signal_id` and `StrategySignalPosition.etf_id`.
- [x] 3.5 Add indexes for signal date/config version, status/generated timestamp, and signal position lookup by signal.
- [x] 3.6 Expose both models through `vela_core.models` so `Base.metadata` includes both tables.

## 4. Migration

- [x] 4.1 Update Alembic model imports so migration autogeneration can discover `StrategySignal` and `StrategySignalPosition`.
- [x] 4.2 Add an Alembic migration that creates the strategy signal tables, foreign keys, unique constraint, and indexes.

## 5. Verification

- [x] 5.1 Run `uv run pytest packages/core/tests`.
- [x] 5.2 Run `openspec status --change "define-strategy-signal-model"` and confirm the change remains apply-ready.
