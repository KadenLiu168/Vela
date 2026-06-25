## ADDED Requirements

### Requirement: Project CLI starts in normal uv environment
The system SHALL expose the installed `vela` console script through the uv-managed project environment without requiring manual `PYTHONPATH` configuration.

#### Scenario: Show CLI help after dependency sync
- **WHEN** a developer runs `uv sync` from the repository root
- **AND** the developer runs `uv run vela --help`
- **THEN** the command exits successfully
- **AND** the command prints the available CLI commands

#### Scenario: Initialize database through installed CLI
- **WHEN** a developer runs `uv run vela init-db --database-url <sqlite-url>` from the repository root after dependency sync
- **THEN** the command exits successfully
- **AND** the command applies the Alembic migrations to the target SQLite database
- **AND** the command does not require manual `PYTHONPATH` configuration
