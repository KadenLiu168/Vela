## ADDED Requirements

### Requirement: API contract validation is part of pytest
The repository SHALL include API contract validation in the configured Python pytest suite.

#### Scenario: API contract tests run with pytest
- **WHEN** a developer runs `uv run pytest` from the repository root
- **THEN** pytest MUST collect and execute the API contract tests covering the Phase 1 API endpoint surface
- **AND** the tests MUST validate successful response structures, empty-data structures, and key error response envelopes
