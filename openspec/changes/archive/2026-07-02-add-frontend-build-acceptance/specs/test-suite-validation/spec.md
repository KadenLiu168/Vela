## ADDED Requirements

### Requirement: Frontend TypeScript validation passes
The repository SHALL provide a passing frontend TypeScript validation command through `npm --prefix apps/web run typecheck`.

#### Scenario: Frontend TypeScript validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run typecheck` from the repository root
- **THEN** TypeScript project build validation MUST complete without type errors
- **AND** the command MUST NOT require a running local API service or frontend mock service

### Requirement: Frontend production build validation passes
The repository SHALL provide a passing frontend production build validation command through `npm --prefix apps/web run build`.

#### Scenario: Frontend production build validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run build` from the repository root
- **THEN** the frontend production build MUST complete successfully
- **AND** the build MUST include TypeScript validation
- **AND** the command MUST NOT require a running local API service, seeded SQLite data, or frontend mock service
