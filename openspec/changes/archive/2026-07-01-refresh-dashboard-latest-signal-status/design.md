## Context

COP-98 added signal generation, COP-99 added the structured latest signal API, COP-100 added the Dashboard generation action, and COP-101/COP-102 made the Signal Detail page consume `GET /api/strategy-signals/latest`. The Dashboard currently refreshes `GET /api/dashboard` after generation, but it does not explicitly read the same structured latest signal endpoint as the detail page.

## Goals / Non-Goals

**Goals:**

- Backfill the Dashboard latest signal summary after successful generation using persisted backend latest signal data.
- Keep the Dashboard summary consistent with the Signal Detail page for signal id, date, result, fallback status, and holding count.
- Preserve browser refresh behavior by continuing to load Dashboard state from backend APIs.

**Non-Goals:**

- No new backend endpoint or response field.
- No database schema or model change.
- No Signal Detail page layout redesign.
- No realtime subscriptions or polling.

## Decisions

- Use existing endpoints only: keep `POST /api/strategy-signals/generate`, `GET /api/dashboard`, and `GET /api/strategy-signals/latest`. This avoids expanding backend scope for a frontend phase issue.
- After successful generation, refresh both Dashboard aggregate data and latest signal data. The aggregate keeps the existing Dashboard contract, while latest signal establishes the same persisted source used by the detail page.
- Convert the latest signal response into the existing Dashboard signal summary shape only for the Dashboard display. The conversion is local to the page and uses the generated response status plus latest signal metadata and positions length.
- Keep failed latest-signal refresh visible as a signal-generation operation error and avoid updating the Dashboard with inconsistent partial state.

## Risks / Trade-offs

- Extra request after generation -> acceptable because generation is user-triggered and the latest endpoint is already required for the detail page.
- Dashboard aggregate and latest endpoint could theoretically disagree if backend behavior changes -> tests will assert both are refreshed from the same generated persisted signal values.
