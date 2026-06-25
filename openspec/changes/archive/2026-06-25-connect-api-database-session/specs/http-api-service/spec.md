## ADDED Requirements

### Requirement: API database session factory
The API service SHALL configure a SQLAlchemy session factory using the shared default local SQLite database URL.

#### Scenario: API app has a default session factory
- **WHEN** the API application is created
- **THEN** the app has a session factory built from the shared default database URL

### Requirement: API request database session dependency
The API service SHALL provide a request-scoped database session dependency that reuses the core managed session lifecycle.

#### Scenario: Request work succeeds
- **WHEN** an API request uses the database session dependency and completes successfully
- **THEN** the session work is committed and the session is closed

#### Scenario: Request work fails
- **WHEN** an API request uses the database session dependency and raises an exception
- **THEN** the session work is rolled back, the session is closed, and the exception remains visible to the request handler

### Requirement: API database boundary
The API service SHALL expose database session wiring for future routes without adding business API endpoints in this change.

#### Scenario: API endpoint surface remains minimal
- **WHEN** a developer inspects the API routes after database wiring is added
- **THEN** no strategy, market data, signal, or backtest endpoint has been added by this change
