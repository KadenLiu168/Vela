## Context

COP-141 is a second-pass visual refinement for the existing Signal Detail target holdings table. COP-133 already introduced the page-scoped editorial table styling and established that the table can be refined through CSS selectors while preserving `SignalDetailPage.tsx` markup and positions rendering.

The current table already uses `.holdings-table-wrap`, `.holdings-table`, and page-scoped `.signal-detail-page` selectors. The remaining gap is consistency: header hierarchy should read as micro/caption metadata, numeric columns should align with tabular numerals, hairline dividers should remain restrained, and narrow screens should keep horizontal scrolling.

## Goals / Non-Goals

**Goals:**

- Improve Signal Detail holdings table header typography and restrained editorial hierarchy.
- Make target weight, rank, and score columns easier to scan through right alignment and `font-variant-numeric: tabular-nums`.
- Preserve readable left alignment for exchange, symbol, and fallback text columns.
- Keep Mist hairline row dividers and remove only the final row divider.
- Preserve the existing horizontal-scroll wrapper and minimum table width on narrow screens.

**Non-Goals:**

- Do not modify JSX, API calls, routes, formatter behavior, test selectors, or rendered text.
- Do not add sorting, filtering, pagination, controls, or a reusable table component.
- Do not introduce new dependencies, tokens, or broad table styling for unrelated pages.

## Decisions

1. Keep the implementation CSS-only.
   - Rationale: the existing table DOM already exposes stable styling hooks, and COP-141 explicitly asks to keep structure and selectors unchanged.
   - Alternative considered: adding cell/header classes in JSX. Rejected because it changes rendering code without being necessary for acceptance.

2. Continue using page-scoped column selectors for numeric columns.
   - Rationale: COP-133 already uses column selectors for target weight, rank, and score. Extending that pattern is the smallest change and keeps the current table contract intact.
   - Alternative considered: deriving column metadata in TypeScript. Rejected as overengineering for a visual-only refinement.

3. Scope refinements to Signal Detail holdings selectors.
   - Rationale: `.holdings-table` may be shared with other detail surfaces. The stronger typography and alignment adjustments belong to `.signal-detail-page` so unrelated tables are not restyled.
   - Alternative considered: changing global `.holdings-table` defaults. Rejected because COP-141 is limited to Signal Detail target holdings.

## Risks / Trade-offs

- CSS `nth-child` selectors depend on the existing holdings table column order -> mitigated by preserving DOM structure and existing tests that verify column headers and row values.
- Visual quality is partly subjective -> mitigated by mapping changes directly to `DESIGN.md` tokens and the explicit COP acceptance criteria.
