## Context

The web frontend uses a dark palette declared in `apps/web/src/styles/tokens.css`. The current palette values make `--color-smoke` and `--color-ash` suitable for subtle structure but not for normal readable text on the app's dark surfaces:

- `--color-smoke` against `--surface-obsidian` is about 1.6:1.
- `--color-ash` against `--surface-obsidian` is about 3.1:1.
- `--color-fog` against `--surface-obsidian` is about 5.5:1.
- `--color-mist` and `--color-paper` have much larger contrast margins.

The earlier investigation did not find an H3-specific failure: current H3 styles use `--color-paper`. The real issue is lower-priority UI text and metadata that use `ash`/`smoke`, especially status pills and command-palette text. Token values should remain unchanged because they are part of the design-system contract and continue to be useful for decorative structure.

## Goals / Non-Goals

**Goals:**

- Make normal readable UI text on dark surfaces meet WCAG AA 4.5:1 contrast by routing it through `fog`, `mist`, or `paper`.
- Preserve `ash`/`smoke` for non-text decoration such as borders, dividers, chart grid lines, and non-semantic visual separators.
- Fix known low-contrast text call sites without changing the visual hierarchy more than necessary.
- Keep the change local to the web frontend and design-system spec contract.

**Non-Goals:**

- Do not change color token values in `tokens.css`.
- Do not introduce new color tokens.
- Do not redesign the full palette, chart styling, or status accent system.
- Do not treat decorative borders, strokes, or grid lines as readable text.
- Do not change backend, API, data model, or dependency behavior.

## Decisions

### Decision 1: Change consumers, not token values

Keep `--color-ash` and `--color-smoke` unchanged and update text consumers to compliant text colors.

**Rationale:** Changing token values would affect every decorative use and could flatten the dark UI's visual hierarchy. The issue is role misuse, not incorrect palette values.

**Alternative considered:** Raise `ash`/`smoke` globally until they pass text contrast. Rejected because those tokens intentionally serve as subdued structural colors and are already used for borders, strokes, and status accents.

### Decision 2: Use `--color-fog` as the minimum text color

Use `--color-fog` for secondary/meta text that should remain visually quiet, and reserve `--color-mist`/`--color-paper` for more important text.

**Rationale:** `fog` clears 4.5:1 on the app's common dark surfaces while preserving the existing hierarchy. `mist` is safer but would over-emphasize labels and metadata that are intentionally secondary.

**Alternative considered:** Convert all affected text to `mist`. Rejected because it would make low-priority metadata compete with primary content.

### Decision 3: Keep the ETF dot visually decorative

Keep `.etf-row-dot` visually subdued and mark the rendered separator `aria-hidden="true"` rather than treating it as readable content.

**Rationale:** The dot only separates adjacent visual fields; it does not carry information that assistive technology needs. Brightening it to `fog` would add visual noise without improving comprehension.

**Alternative considered:** Change `.etf-row-dot` to `--color-fog`. Acceptable under a strict “no smoke on text nodes” interpretation, but less optimal visually because the separator is decoration.

### Decision 4: Avoid changing `--feedback-accent-empty`

Do not change `--feedback-accent-empty`, even though neutral status pills currently inherit it for text.

**Rationale:** The token is documented as an accent token and resolves to `--color-smoke`. It can remain valid for borders or non-text accents. The fix is to stop using that accent token as the sole text color for `.status-pill-neutral`.

**Alternative considered:** Change `--feedback-accent-empty` to `--color-fog`. Rejected because it changes the accent contract and could unintentionally brighten empty-state decorations.

## Risks / Trade-offs

- **Risk:** `fog` has less contrast margin on lighter dark surfaces like `--color-graphite`. → **Mitigation:** Use `fog` only as the minimum secondary-text token on the existing dark surfaces; use `mist`/`paper` if a call site sits directly on `graphite` or a hover state materially lightens the background.
- **Risk:** Regex-based checks may flag decorative uses of `ash`/`smoke`. → **Mitigation:** The spec distinguishes readable text from decorative borders/strokes/separators; implementation review should inspect semantics, not only raw token occurrence.
- **Risk:** Placeholder text remains lower priority by design. → **Mitigation:** Use `fog` so the placeholder still meets normal-text contrast while staying visually subordinate to actual input text.
- **Risk:** Existing tests may assert class names but not computed styles. → **Mitigation:** Keep class names unchanged and add or update focused tests only where semantics change, such as the decorative ETF separator.
