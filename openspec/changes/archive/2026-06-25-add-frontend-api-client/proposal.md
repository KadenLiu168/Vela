## Why

COP-84 establishes the frontend integration foundation needed before later pages call the local API. The current web skeleton only stores the API base URL, so future pages would otherwise duplicate `fetch` behavior and error handling.

## What Changes

- Extend the web frontend API module into a shared client for request execution, JSON response parsing, and basic error normalization.
- Add frontend behavior that calls the local API through the shared client instead of direct scattered `fetch` calls.
- Cover successful responses, HTTP error responses, and network errors with frontend tests.
- Add a local real-request validation path against the checked-in FastAPI service so verification is not limited to mocked fetch calls.
- Keep backend API endpoints unchanged and do not add business pages, routing, authentication, charts, or deployment behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `web-frontend-app`: Adds the shared frontend API client contract and local API request validation expectation.

## Impact

- Affects `apps/web/src/api`, the minimal frontend page/component behavior that consumes the client, and frontend tests.
- May add a web validation script for local API integration verification.
- Does not change Python API route behavior or the core business packages.
