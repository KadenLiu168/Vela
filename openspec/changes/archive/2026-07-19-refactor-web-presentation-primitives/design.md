## Context

`DashboardPage`, `EtfDetailPage`, `SignalDetailPage`, and `BacktestDetailPage` each define the same `Detail` fragment that emits a `<dt>/<dd>` pair. The shared CSS already provides most cross-page visual consistency, but the repeated JSX permits future structural drift and forces Signal Detail to hand-write a linked description value because the current local prop type accepts only strings.

The page modules also contain deterministic presentation formatters. Generic scalar formatters already live in `utils/formatters.ts`, so moving API-shaped page formatters into that file would make a low-level utility module depend on page or API contracts.

ETF Trend already keeps chart dimensions and pure geometry in `etfTrendChart.ts`. Equity Curve has pure calculations, but they remain private to `BacktestDetailPage.tsx`, and its dimensions are repeated in both those calculations and literal SVG attributes. Existing page tests cover rendered chart states, while only ETF hover index resolution has direct pure-function tests.

## Goals / Non-Goals

**Goals:**

- Make one semantic component responsible for description-list item structure across all four pages.
- Allow description values to contain links or other React content without bypassing the shared primitive.
- Separate generic scalar formatting from page-domain presentation formatting and make non-trivial domain formatters directly testable.
- Give Equity Curve one source of truth for dimensions and a pure, framework-independent geometry module.
- Add focused geometry tests without weakening the existing page-level behavior coverage.
- Keep page modules compatible with the React Fast Refresh component-export constraint.

**Non-Goals:**

- Change rendered copy, routes, API calls, CSS selectors, tokens, spacing, typography, or chart appearance.
- Merge `Metric`, `MetricCard`, or `StatusPillBadge`; they do not currently duplicate one another and have different semantics or visual roles.
- Create a generic chart component or generic multi-chart geometry framework.
- Move every trivial one-use helper out of its page module.
- Add a new ETF list page or a third chart.

## Decisions

### D1: Introduce a semantic `DescriptionItem` component

Create `components/DescriptionItem.tsx` with a string label and a `ReactNode` value. It renders only a sibling `<dt>` and `<dd>` fragment and owns no layout wrapper or styling.

All existing `Detail` call sites in the four pages migrate to this component. Signal Detail's manually rendered Backtest `<dt>/<dd>` pair also migrates by passing the link as the value.

This keeps the existing `<dl>` structure and CSS contract intact. A wrapper component that renders its own `<dl>` was rejected because the current pages compose multiple items inside differently styled lists. A configurable `Detail` with variants was rejected because no variants exist.

### D2: Keep specialized metric and status components local

`Metric` uses `div/span/strong` for Dashboard emphasis, while `MetricCard` uses `dt/dd` inside a metric definition list. `StatusPillBadge` is currently used only by Dashboard. They remain local until another real consumer establishes a stable shared contract.

This avoids introducing conditional element selection, style variants, or speculative APIs solely to make the components appear unified.

### D3: Use page-domain pure formatter modules

Keep broadly reusable scalar functions such as dates, nullable values, decimals, percentages, and integer formatting in `utils/formatters.ts`.

Move deterministic domain presentation functions into co-located pure modules:

- `pages/dashboardFormatters.ts` for momentum-window, score-weight, defensive-asset, and failed-symbol presentation.
- `pages/backtestFormatters.ts` for parameter JSON summaries and composite equity-point readouts.

Prefer scalar or small structural arguments over importing whole response types when that keeps the formatter contract independent of API transport shapes. These modules must not import React or access the DOM. Page-specific control flow and operation-error guidance remain in the page because moving them would expand scope without reuse or meaningful isolation.

Direct tests cover the meaningful formatting branches, including empty symbol lists, malformed parameter JSON, valid parameter JSON, and nullable parameter values. Moving every trivial page helper to the global utility module was rejected because it would blur generic and domain-specific responsibilities.

### D4: Extract an Equity Curve chart-model module

Create `pages/equityCurveChart.ts` containing:

- `EQUITY_CURVE_CHART`, the sole width, height, and padding definition.
- chart point and coordinate types.
- API-point normalization that removes null and non-finite net values.
- a pure geometry calculation for a validated series of at least two points.
- path construction and deterministic latest/min/max highlight selection.

The geometry result exposes the coordinates, path, extrema, and highlight coordinates needed by the renderer. `BacktestDetailPage.tsx` remains responsible for empty and single-point states, then invokes the geometry function only for a multi-point validated series.

The SVG `viewBox` and grid-line endpoints derive from `EQUITY_CURVE_CHART` rather than repeating numeric literals. The module must not import React or DOM APIs.

A shared `GenericLineGeometry<T>` abstraction was rejected. ETF Trend and Equity Curve currently differ in dimensions, input representation, hover behavior, axis labels, highlight rules, and readouts. The change standardizes module boundaries, not an unproven generic API.

### D5: Separate pure geometry tests from page integration tests

Add `etfTrendChart.test.ts` and `equityCurveChart.test.ts`.

ETF tests directly cover:

- nearest-point index resolution and clamping;
- two-point, odd-count, and even-count date-axis indexes;
- normal and all-equal price geometry;
- line-path bounds.

Equity tests directly cover:

- null and non-finite input filtering;
- two-point and multi-point coordinates and paths;
- all-equal values centered vertically;
- latest/min/max highlight selection, duplicate suppression, and tie behavior;
- geometry bounds derived from the shared constant.

Move the existing direct `indexFromX` assertions out of `App.test.tsx`. Retain page-level tests for loading/error handling, empty series, single-point series, multi-point rendering, and ETF hover behavior.

## Risks / Trade-offs

- **[Risk] `ReactNode` values permit richer markup than the current string-only contract.** → Keep `DescriptionItem` intentionally structure-only and cover linked-value rendering with a focused component test.
- **[Risk] Moving formatters can accidentally change punctuation or fallback text.** → Characterize current outputs first and preserve them with direct tests before replacing page call sites.
- **[Risk] Geometry extraction can cause subtle coordinate drift.** → Assert current dimensions, paths, extrema, and equal-value behavior before switching the renderer; retain integration assertions after extraction.
- **[Risk] A barrel export can increase coupling or obscure ownership.** → Follow the repository's existing `components/index.ts` convention for consistency; do not add a second aggregation layer.
- **[Trade-off] Two chart-model modules retain some mathematical duplication.** → Accept the small duplication until a third chart provides enough evidence for a stable common abstraction.

## Migration Plan

1. Add focused tests that characterize current formatter and chart geometry behavior.
2. Introduce `DescriptionItem`, migrate all four pages and the linked Signal Detail value, then remove only the four obsolete local `Detail` definitions.
3. Add page-domain formatter modules and switch the corresponding call sites without changing output.
4. Add the Equity Curve chart-model module, replace literal SVG geometry with the shared constant, and remove the page-local geometry helpers made obsolete by the extraction.
5. Move pure ETF geometry assertions to the dedicated test file while retaining page behavior tests.
6. Run frontend tests, type checking, linting, CSS linting, and the production build.

Rollback is a normal source revert: the change has no persisted data, API, dependency, or deployment migration.

## Open Questions

None. A future third chart may trigger a separate proposal to evaluate shared Cartesian geometry primitives using three concrete consumers.
