## ADDED Requirements

### Requirement: Database engine creation

The system SHALL provide a typed public function for creating a SQLAlchemy engine from a database URL.

#### Scenario: Create engine from URL

- **WHEN** backend code requests an engine for a valid database URL
- **THEN** the system returns a SQLAlchemy engine configured for that URL

### Requirement: Session factory creation

The system SHALL provide a typed public function for creating a SQLAlchemy session factory from an engine.

#### Scenario: Create session factory from engine

- **WHEN** backend code requests a session factory for an engine
- **THEN** the system returns a factory that creates SQLAlchemy `Session` instances bound to that engine

### Requirement: Managed session lifecycle

The system SHALL provide a context-managed database session boundary that commits successful work, rolls back failed work, and closes the session after use.

#### Scenario: Commit successful session work

- **WHEN** a managed session exits without an exception
- **THEN** the system commits the transaction and closes the session

#### Scenario: Roll back failed session work

- **WHEN** a managed session exits because an exception was raised
- **THEN** the system rolls back the transaction, closes the session, and re-raises the exception

#### Scenario: Close session after read-only work

- **WHEN** a managed session exits after read-only operations
- **THEN** the system closes the session without requiring caller-managed cleanup
