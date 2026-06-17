## ADDED Requirements

### Requirement: Logging setup function
The system SHALL provide a reusable `setup_logging()` function in the core package for configuring application logging.

#### Scenario: Configure logging from core package
- **WHEN** application or test code imports and calls `setup_logging()`
- **THEN** the root logger is configured without requiring any application-specific logging setup code

### Requirement: Basic log level configuration
The system SHALL allow callers to configure the active logging level when calling `setup_logging()`.

#### Scenario: Use default log level
- **WHEN** `setup_logging()` is called without arguments
- **THEN** the configured logging level is `INFO`

#### Scenario: Use custom log level
- **WHEN** `setup_logging()` is called with a standard logging level name or numeric level
- **THEN** the configured logging level matches the requested level

### Requirement: Unified log format
The system SHALL apply one consistent log format to configured log output.

#### Scenario: Emit formatted log record
- **WHEN** a log record is emitted after `setup_logging()` has been called
- **THEN** the output includes timestamp, log level, logger name, and message in a consistent order
