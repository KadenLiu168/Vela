## ADDED Requirements

### Requirement: Frontend ESLint validation passes
The repository SHALL provide a passing frontend ESLint validation command through `npm --prefix apps/web run lint`.

#### Scenario: Frontend ESLint validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run lint` from the repository root
- **THEN** ESLint MUST complete without lint failures or errors
- **AND** the command MUST NOT require a running local API service or frontend mock service

### Requirement: Frontend CSS lint validation passes
The repository SHALL provide a passing frontend CSS lint validation command through `npm --prefix apps/web run lint:css`.

#### Scenario: Frontend CSS lint validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run lint:css` from the repository root
- **THEN** Stylelint MUST complete without lint failures or errors
- **AND** the command MUST enforce the design-system invariants without weakening existing rules
