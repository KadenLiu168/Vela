## 1. Core Report

- [x] 1.1 Add a core report module that loads the latest successful strategy signal by config version and optional signal date.
- [x] 1.2 Format signal metadata and positions as deterministic human-readable text.
- [x] 1.3 Export the core report API from `vela_core`.

## 2. CLI Export

- [x] 2.1 Add an `export-signal-report` CLI command with database URL, strategy config path, optional signal date, and optional output file arguments.
- [x] 2.2 Print the report to stdout by default and write it to the requested file path when `--output` is provided.
- [x] 2.3 Return a non-zero exit status with a clear message when no matching successful signal exists.

## 3. Tests and Validation

- [x] 3.1 Add core tests for normal reports, fallback reports, date-constrained latest selection, and missing latest signals.
- [x] 3.2 Add CLI tests for default inputs, stdout output, file output, and missing latest signal handling.
- [x] 3.3 Run focused tests, full tests, lint, type check, and OpenSpec validation.
