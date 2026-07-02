## Context

Dashboard, Signal Detail, and Backtest Detail each define their own formatting helpers. The same semantic values are shown with different nullable labels (`None`, `Not available`, `n/a`) and slightly different numeric precision rules. COP-114 asks for consistent frontend display and centralized reuse without changing API payloads.

## Goals / Non-Goals

**Goals:**
- Centralize formatting logic in one frontend utility module.
- Use `n/a` for nullable data fields where a value is absent.
- Keep date and timestamp display explicit and stable by normalizing ISO strings to their date portion for date values and preserving timestamp strings for timestamp values.
- Preserve existing meaningful precision for target weights, scores, net values, and backtest metrics.

**Non-Goals:**
- Add localization settings, user preferences, or new dependencies.
- Change backend response shapes, stored Decimal precision, or API validation.
- Redesign page layout or copy beyond value formatting.

## Decisions

1. Use a small shared TypeScript utility module under `apps/web/src/utils`.
   - Rationale: formatting is frontend-only and reused by multiple pages.
   - Alternative considered: keep helpers in each page and align behavior manually. That would satisfy the immediate display output but keep duplication and future drift.

2. Keep formatting functions domain-specific where semantics differ.
   - Rationale: generic helpers like `formatDecimal` can coexist with domain helpers such as `formatRatioAsPercent` and `formatTargetWeight` so call sites remain clear.
   - Alternative considered: one highly configurable formatter. That would add option objects for a small app and make call sites harder to scan.

3. Standardize absent nullable values as `n/a`.
   - Rationale: the issue asks for explicit nullable states; `n/a` is already used by Backtest Detail metric cards and is concise in dense panels/tables.
   - Alternative considered: `Not available`. It is longer and already inconsistent with metric-card behavior.

## Risks / Trade-offs

- Display snapshots change from `None` or `Not available` to `n/a` -> Update focused frontend tests to assert the new contract.
- Date formatting may hide timestamp time components if used incorrectly -> Keep separate `formatDate` and `formatTimestamp` helpers and only apply date formatting to date fields.
