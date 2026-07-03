## Context

`apps/web/src/styles.css` is the active implementation source for the web visual system. It already defines `--section-gap`, `--card-padding`, `--text-heading-lg`, `--text-display`, and `--radius-asymmetric-card`, but the Dashboard, Signal Detail, and Backtest Detail pages mostly use smaller spacing and heading tokens. The relevant pages already expose stable `page-heading`, `dashboard-grid`, `dashboard-panel`, and `first-run-guidance` hooks, so this change can stay CSS-only.

## Goals / Non-Goals

**Goals:**

- Make the three research pages feel closer to the `DESIGN.md` editorial data observatory through spacing, hierarchy, and one asymmetric signature card.
- Reuse existing CSS variables instead of introducing new tokens or hard-coded visual values.
- Preserve dashboard density where the content is operational or data-heavy.
- Keep the Dashboard first screen focused on local research status and operations.

**Non-Goals:**

- No marketing hero, CTA cluster, decorative illustration, copy rewrite, or route behavior change.
- No DOM restructure, data-testid change, or API/client behavior change.
- No broad card-system refactor beyond the selectors required for COP-138.

## Decisions

- Use CSS-only changes. The existing headings already provide eyebrow and title structure, and first-run guidance already provides a suitable featured block, so JSX changes would add risk without improving acceptance coverage.
- Apply `--text-display` only to the Dashboard page title with responsive bounds, while applying `--text-heading-lg` to detail-page titles. This creates a stronger homepage anchor without turning detail pages into marketing pages.
- Use `--section-gap` for primary page-to-content and detail-section rhythm, but keep dashboard panel internals compact. This balances editorial breathing room against the requirement that the Dashboard first screen not be pushed too far down.
- Use `--card-padding` for prominent containers and featured guidance, while keeping dense metric cards and nested lists on tighter padding.
- Apply `--radius-asymmetric-card` only to `.first-run-guidance`. It is semantically a featured setup block and avoids diluting the signature radius across ordinary data cards.

## Risks / Trade-offs

- Increased spacing could reduce above-the-fold density on Dashboard → Mitigation: keep the header-to-main offset modest and use a reduced Dashboard grid gap derived from `--section-gap`.
- Large Dashboard title could collide with status/actions → Mitigation: allow wrapping and use `clamp()` plus existing mobile stacking rules.
- Detail pages could feel too sparse on small screens → Mitigation: override `--section-gap` and card padding in the existing `max-width: 720px` media query.
- CSS-only implementation cannot create a new supporting-context line where none exists → Mitigation: preserve the current eyebrow/title content and rely on typography, spacing, and action alignment for hierarchy clarity.
