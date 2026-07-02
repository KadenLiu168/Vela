## MODIFIED Requirements

### Requirement: Web skeleton validation commands
The web frontend SHALL provide package scripts for type checking, linting, testing, and building the skeleton. Type checking and production build validation MUST complete without requiring backend services, local mock services, or API integration test setup.

#### Scenario: Developer validates the frontend skeleton
- **WHEN** a developer runs the documented frontend validation commands
- **THEN** the commands complete against the `apps/web` skeleton without requiring backend services

#### Scenario: Developer validates the production frontend build
- **WHEN** a developer runs `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` from the repository root
- **THEN** TypeScript validation and the production build complete successfully
- **AND** the commands do not require a running local API service, seeded SQLite data, or frontend mock service
