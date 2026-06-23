## 1. Core Signal Generation

- [x] 1.1 Add a core signal generation service that scores active ETFs, applies trend filtering, selects Top N or defensive fallback, and persists one signal run.
- [x] 1.2 Add focused core tests for successful generated positions, defensive fallback, no active ETFs, and missing defensive asset failure.
- [x] 1.3 Export the new core signal generation API from `vela_core`.

## 2. CLI Command

- [x] 2.1 Add `generate-signal` argparse command options for database URL, strategy config path, and optional signal date.
- [x] 2.2 Wire the command to load strategy config, use the latest local market price date by default, call core generation, and print a clear summary.
- [x] 2.3 Add CLI tests for argument handling, default inputs, successful summary, and failed summary exit behavior.

## 3. Validation

- [x] 3.1 Run targeted core and CLI tests for signal generation.
- [x] 3.2 Run full tests, lint, type check, and OpenSpec validation.
