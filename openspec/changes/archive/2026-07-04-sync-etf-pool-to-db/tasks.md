## 1. Core Sync Service

- [x] 1.1 Add focused core tests for insert, idempotent unchanged sync, updates to YAML-owned fields, and preserving out-of-pool ETF rows.
- [x] 1.2 Implement the ETF pool synchronization result type and core sync function.
- [x] 1.3 Export the sync API from `vela_core`.

## 2. CLI Workflow

- [x] 2.1 Add CLI tests for `sync-etf-pool` arguments, defaults, success summary, and failure handling.
- [x] 2.2 Implement the `sync-etf-pool` CLI command and output formatting.

## 3. Verification

- [x] 3.1 Run targeted core and CLI pytest commands for the new sync workflow.
- [x] 3.2 Run OpenSpec validation for `sync-etf-pool-to-db`.
