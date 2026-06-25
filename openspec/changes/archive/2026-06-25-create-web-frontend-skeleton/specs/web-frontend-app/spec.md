## ADDED Requirements

### Requirement: Web frontend application skeleton
The repository SHALL include an `apps/web` frontend application skeleton implemented with Vite, React, TypeScript, and npm.

#### Scenario: Web app directory exists
- **WHEN** a developer inspects the repository
- **THEN** `apps/web` contains the frontend package manifest, Vite entrypoint, TypeScript configuration, and React source entrypoint

### Requirement: Web development server command
The web frontend SHALL provide a documented development server command that can be run from the repository root as `npm --prefix apps/web run dev`.

#### Scenario: Developer starts the web dev server from the root
- **WHEN** a developer runs `npm --prefix apps/web run dev` from the repository root
- **THEN** the frontend development server starts using the `apps/web` package scripts

### Requirement: Extensible frontend source layout
The web frontend SHALL include directories for pages, components, API client code, and tests so later frontend issues can add behavior without reorganizing the app skeleton.

#### Scenario: Developer adds future frontend behavior
- **WHEN** a developer needs to add a page, reusable component, API client module, or frontend test
- **THEN** `apps/web/src` provides corresponding locations for that code

### Requirement: Web skeleton validation commands
The web frontend SHALL provide package scripts for type checking, linting, testing, and building the skeleton.

#### Scenario: Developer validates the frontend skeleton
- **WHEN** a developer runs the documented frontend validation commands
- **THEN** the commands complete against the `apps/web` skeleton without requiring backend services
