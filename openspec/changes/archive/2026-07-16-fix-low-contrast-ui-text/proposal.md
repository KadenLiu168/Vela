## Why

Several UI text roles currently use `--color-ash` or `--color-smoke`, whose contrast against the web app's dark card and overlay surfaces falls below WCAG AA's 4.5:1 threshold for normal text. Headings already use high-contrast colors, but status text, command-palette metadata, and placeholder text need the same accessibility boundary between readable text and decorative color roles.

## What Changes

- Require readable UI text on dark surfaces to use `--color-fog` or a higher-contrast text color such as `--color-mist`/`--color-paper`.
- Reserve `--color-ash` and `--color-smoke` for non-text decoration such as borders, dividers, chart grid lines, and status accents that are not the sole readable text color.
- Update low-contrast call sites in the web stylesheet, including neutral status pills, command-palette placeholder/kind text, and default status-pill fallback color.
- Treat the ETF row dot separator as decorative rather than meaningful text by hiding it from assistive technology while preserving its subdued visual treatment.
- No API, route, data model, dependency, or token value changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `design-system`: Adds an accessibility contract for palette token usage: readable text must not use `--color-ash` or `--color-smoke` on dark surfaces; those tokens are limited to decorative/non-text roles.

## Impact

- `apps/web/src/styles.css`: update low-contrast text color declarations to compliant text tokens while preserving decorative uses of `ash`/`smoke`.
- `apps/web/src/pages/DashboardPage.tsx`: mark the ETF row dot separator as decorative if it remains visually subdued.
- `openspec/specs/design-system/spec.md`: extend the design-token usage contract via this change's delta spec.
- No backend behavior, database schema, HTTP API, or package dependency changes.
