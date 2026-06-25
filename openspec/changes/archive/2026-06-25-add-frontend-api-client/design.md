## Context

`apps/web` already has a scoped Vite React TypeScript skeleton and an `api/client.ts` file that only resolves the API base URL. The local FastAPI app already exposes `GET /api/health`, which is enough to validate a real frontend request without adding backend routes.

## Goals / Non-Goals

**Goals:**

- Provide one shared frontend API client path for later page work.
- Normalize successful JSON responses, HTTP failures, and network failures.
- Use the existing API health endpoint for the first real frontend request.
- Keep default browser calls on `/api` so Vite can proxy local development requests to the FastAPI service.

**Non-Goals:**

- Do not add backend endpoints or change API response shapes.
- Do not introduce request retries, cancellation, authentication, caching, routing, or generated API types.
- Do not create a root Node workspace or change frontend package management.

## Decisions

- Extend `apps/web/src/api/client.ts` instead of introducing another client module.
  - This matches the skeleton source layout and keeps later pages from choosing their own fetch wrappers.
  - Alternative considered: create separate endpoint-specific service files first. Rejected because only one endpoint is needed for COP-84.
- Use a small typed `apiRequest<T>()` wrapper around `fetch`.
  - It keeps the public surface understandable while still allowing endpoint helpers such as `getHealth()`.
  - Alternative considered: add Axios or another HTTP dependency. Rejected because basic fetch handling is enough here.
- Throw `ApiClientError` for both HTTP and network failures.
  - HTTP failures carry `kind: "http"` and `status`; network failures carry `kind: "network"`.
  - This gives UI code a stable error contract without inventing a larger error hierarchy.
- Add a Vite dev proxy for `/api` to `http://127.0.0.1:8000`.
  - The client can keep a same-origin default while local development requests reach the FastAPI service.
  - Tests and explicit local validation can still override the base URL.

## Risks / Trade-offs

- API error bodies may not always be JSON -> Fall back to response text or status text when building the error message.
- The real-request validation needs the local API service running -> Document it as a separate integration validation script instead of making normal unit tests depend on the backend.
- The client starts intentionally small -> Add auth, retries, or endpoint-specific types only when later COPs require them.
