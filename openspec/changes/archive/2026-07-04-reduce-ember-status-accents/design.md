## Context

`FeedbackMessage` already centralizes loading, info, success, and error semantics. Existing page code uses `dashboard-alert`, `operation-summary-*`, and `.empty-state` classes for related state presentation. COP-135 made these surfaces tokenized and neutral, but `--feedback-accent-error` still maps to Ember Orange and is used as a 3px rail on page errors and failed operation summaries.

`DESIGN.md` positions Ember as a sparse functional punctuation color for links, highlights, and small accents, not as a broad error color system. COP-142 therefore adjusts CSS tokens/selectors rather than React structure.

## Goals / Non-Goals

**Goals:**

- Make error and failed status surfaces primarily Graphite/Steel/Slate/Mist.
- Keep errors recognizable through a neutral Graphite rail, surface contrast, existing labels, and `role="alert"`.
- Preserve Ember usage for small functional accents such as `.operation-link` underline.
- Keep existing loading, empty, error, not-found, partial, and failed tests passing.

**Non-Goals:**

- Do not rewrite `FeedbackMessage`, `EmptyState`, Dashboard operation rendering, or detail-page status rendering.
- Do not change `role`, `aria-live`, text, API calls, route targets, loading timing, or error categorization.
- Do not introduce red, blue, green, new status tokens, or skeleton loading.

## Decisions

1. Change the error accent token to Graphite.
   - Rationale: `--feedback-accent-error` is the shared source for broad error rails. Moving it to Graphite removes Ember from the error system while preserving a strong neutral signal.
   - Alternative considered: keep Ember but reduce the rail width. Rejected because it still treats Ember as the system error color.

2. Keep `.operation-link` Ember underline unchanged.
   - Rationale: links are explicitly listed in `DESIGN.md` as an appropriate Ember use, and operation links are small functional affordances.
   - Alternative considered: remove all Ember from status areas. Rejected because COP-142 allows retry/detail links to use Ember underline.

3. Keep implementation CSS-only.
   - Rationale: the issue is visual tuning, and existing components already preserve the required ARIA semantics.
   - Alternative considered: add status-specific React props or components. Rejected as outside the issue boundary.

## Risks / Trade-offs

- Error states become less chromatically distinct -> mitigated by Graphite rail, existing error copy, `role="alert"`, and surrounding neutral hierarchy.
- Changing a shared token affects all broad error rails -> mitigated by limiting the token to existing status selectors and preserving tests for text, roles, and classes.
