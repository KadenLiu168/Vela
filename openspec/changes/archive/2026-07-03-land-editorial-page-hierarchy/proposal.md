## Why

The web dashboard already defines the editorial spacing, display typography, card padding, and asymmetric-card tokens from `DESIGN.md`, but the main pages still render closer to a compact SaaS dashboard. COP-138 lands those existing tokens in the Dashboard, Signal Detail, and Backtest Detail page skeletons without changing local research workflow behavior.

## What Changes

- Connect page-level spacing and primary card padding to the existing `--section-gap` and `--card-padding` tokens while preserving compact density inside data-heavy dashboard panels.
- Promote page headings to a clearer eyebrow -> title hierarchy using `--text-heading-lg` on detail pages and a restrained `--text-display` treatment on the Dashboard.
- Apply the signature `--radius-asymmetric-card` to the first-run guidance block only, keeping ordinary data cards on their existing generic or data-widget radius scale.
- Keep PolySans / heading substitute text at weight 400 and avoid marketing hero structure, CTA clusters, decorative surfaces, or business behavior changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add visual layout requirements for editorial page spacing, title hierarchy, and a restrained asymmetric featured card across the existing research pages.

## Impact

- Affected code: `apps/web/src/styles.css`.
- Affected pages: Dashboard, Signal Detail, and Backtest Detail.
- No API, data model, dependency, route, DOM structure, or test selector changes are planned.
