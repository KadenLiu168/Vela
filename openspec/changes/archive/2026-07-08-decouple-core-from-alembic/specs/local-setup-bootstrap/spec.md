## ADDED Requirements

### Requirement: Caller-provided script location for bootstrap
The system SHALL require callers of `run_local_setup_bootstrap` to provide `script_location` explicitly. The function SHALL NOT compute a default script location from a hardcoded project-relative path.

#### Scenario: Caller omits script_location
- **WHEN** a caller invokes `run_local_setup_bootstrap` without the `script_location` argument
- **THEN** the function raises a `TypeError` (missing required keyword argument)
- **AND** no Alembic migration is attempted

#### Scenario: API endpoint passes script_location explicitly
- **WHEN** a client posts to `POST /api/setup/bootstrap`
- **THEN** the endpoint passes an explicit `script_location` derived from the app-layer project root to `run_local_setup_bootstrap`
- **AND** the endpoint does not rely on a default value computed inside `vela_core`

#### Scenario: Bootstrap still runs three steps in order
- **WHEN** a caller invokes `run_local_setup_bootstrap` with all required arguments including `script_location`
- **THEN** the function applies Alembic migrations via `vela_core.migration.run_alembic_upgrade`
- **AND** synchronizes the configured ETF pool
- **AND** runs a full market data fetch
- **AND** returns a `BootstrapResult` with per-step status
