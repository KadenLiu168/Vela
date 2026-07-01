## Context

COP-98 added `POST /api/strategy-signals/generate`, and COP-99 added structured latest signal reads. The Dashboard already renders latest signal summary from `GET /api/dashboard` and has disabled generate-signal controls in both the signal empty state and operations panel.

## Goals / Non-Goals

**Goals:**

- Route Dashboard generate-signal actions through the shared frontend API client.
- Show loading state while generation is pending and prevent duplicate signal-generation requests.
- Refresh Dashboard aggregate data after successful generation so latest signal state updates from persisted backend rows.
- Validate the shared client against a real local API and SQLite path.

**Non-Goals:**

- Add signal detail page behavior.
- Add date selection for signal generation.
- Change the backend signal generation endpoint or database models.
- Use `GET /api/strategy-signals/latest` from Dashboard in this change.

## Decisions

- Use `POST /api/strategy-signals/generate` without `signalDate` from the Dashboard action. This matches COP-100's "latest signal" goal and lets the backend resolve the latest local market date.
- Reuse `GET /api/dashboard` after success rather than adding a separate latest-signal fetch to Dashboard. Dashboard already owns the visible latest signal summary and aggregate refresh keeps all dependent panels consistent.
- Keep operation state local to Dashboard with a dedicated signal-generation pending flag. This avoids coupling market-data fetch and signal-generation loading states while still preventing duplicate submissions per operation.

## Risks / Trade-offs

- API generation may fail when no local market prices exist -> show a concise operation error and leave the existing Dashboard state visible.
- The local API integration validation requires a running FastAPI service with seeded SQLite data -> keep it opt-in through the existing `VITE_API_BASE_URL` pattern so normal frontend tests remain backend-free.
