## ADDED Requirements

### Requirement: Shared default local database URL
The system SHALL provide a shared default local SQLite database URL for application entrypoints that need the local development database.

#### Scenario: Application uses shared default database URL
- **WHEN** an application entrypoint needs the default local database URL
- **THEN** it can import the value from `vela_core.database` without defining a duplicate constant
