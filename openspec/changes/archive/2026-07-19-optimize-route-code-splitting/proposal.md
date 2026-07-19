## Why

The web frontend currently places Dashboard, all five non-default route pages, and CommandPalette in one 247.18 KB production JavaScript file (74.52 KB gzip), so every visit downloads and parses code that the initial Dashboard route does not render. Introducing route-level code splitting now prevents the initial dependency graph from growing linearly as new pages are added, while preserving the Dashboard as the default eager route.

## What Changes

- Load the Signal list, Signal detail, Backtest list, Backtest detail, and ETF detail page modules only when their routes are rendered.
- Keep AppShell, shared routing state, the shared API client, Dashboard, and CommandPalette in the initial application graph.
- Render an accessible route-loading fallback inside the persistent AppShell while an asynchronous page module loads.
- Route lazy-module failures through a recoverable route-scoped error boundary.
- Split React runtime dependencies into a targeted, stable vendor chunk for repeat-visit cache reuse without claiming it reduces the cold-cache total.
- Add production-bundle verification that measures the complete initial static JavaScript graph, dynamic route chunks, and total JavaScript independently.
- Preserve all existing route URLs, navigation behavior, page data loading, API contracts, and visible page content.

## Capabilities

### New Capabilities

- `web-route-code-splitting`: Defines on-demand route module loading, persistent shell behavior, accessible loading and failure states, cache-oriented vendor chunking, and bundle measurement requirements.

### Modified Capabilities

None.

## Impact

- Affected frontend routing and boundaries: `apps/web/src/App.tsx` and shared frontend components used for loading and error feedback.
- Affected build configuration: `apps/web/vite.config.ts`.
- Affected tests: route rendering/navigation tests and production bundle-structure checks under `apps/web`.
- No backend, HTTP API, database, URL, or runtime dependency changes are required.
- The existing `subset-inter-variable-font` change remains independent; font and JavaScript transfer improvements must be measured separately.
