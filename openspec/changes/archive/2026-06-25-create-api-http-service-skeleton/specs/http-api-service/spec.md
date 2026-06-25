## ADDED Requirements

### Requirement: HTTP API service skeleton
The repository SHALL include an `apps/api` FastAPI service skeleton that can be imported and tested without starting a network server.

#### Scenario: API app is importable
- **WHEN** a developer imports the API application object
- **THEN** the import succeeds from the `vela_api` package

### Requirement: API startup command
The API service SHALL provide a documented root-level startup command named `uv run vela-api`.

#### Scenario: Developer starts the API service
- **WHEN** a developer runs `uv run vela-api`
- **THEN** the command starts the FastAPI service using uvicorn

### Requirement: API health endpoint
The API service SHALL expose `GET /api/health` as the minimal local health endpoint.

#### Scenario: Health endpoint returns healthy status
- **WHEN** a client sends `GET /api/health`
- **THEN** the response status is 200 and the response body reports healthy service status

### Requirement: API service boundary
The API service SHALL keep strategy and data-processing behavior in `vela_core` and SHALL NOT duplicate strategy logic in the API application skeleton.

#### Scenario: API skeleton adds no strategy endpoint
- **WHEN** a developer inspects the initial API routes
- **THEN** only the health endpoint is exposed by this change
