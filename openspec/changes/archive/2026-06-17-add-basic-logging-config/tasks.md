## 1. Tests

- [x] 1.1 Add tests for importing and calling `setup_logging()` from the core package.
- [x] 1.2 Add tests for the default `INFO` level and custom string or numeric levels.
- [x] 1.3 Add a test that verifies emitted log output uses the unified format.
- [x] 1.4 Add test isolation that detaches pre-existing root handlers before each logging test, closes test-created handlers afterward, and restores root logger state.

## 2. Core Implementation

- [x] 2.1 Create `packages/core/src/vela_core/logging.py`.
- [x] 2.2 Implement `setup_logging(level: str | int = logging.INFO) -> None` using the standard library logging module.
- [x] 2.3 Configure a single shared log format containing timestamp, level, logger name, and message.

## 3. Verification

- [x] 3.1 Run `uv run pytest`.
- [x] 3.2 Run `uv run ruff check .`.
