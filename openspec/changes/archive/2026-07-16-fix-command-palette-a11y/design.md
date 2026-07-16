## Context

The command palette currently renders a `role="dialog"` with `aria-modal="true"` and focuses the search input on open. Keyboard handling covers close, active-row movement, activation, and the open shortcut, but it does not trap `Tab` focus inside the dialog. Active rows are represented with `aria-selected` on `role="option"` elements, while DOM focus remains on the input, so assistive technology does not have a reliable active option relationship to announce.

The fix should preserve the existing command palette interaction model: users type in the input, use arrow keys to move a highlighted result, and press Enter to activate the highlighted result.

## Goals / Non-Goals

**Goals:**

- Keep keyboard focus contained inside the command palette while it is open.
- Expose the highlighted result to assistive technology using `aria-activedescendant`.
- Preserve existing arrow-key, Enter, Escape, Cmd+K/Ctrl+K, click, ETF expansion, and focus-restoration behavior.
- Add focused regression tests for the accessibility contract.

**Non-Goals:**

- Replace the command palette with a third-party dialog or combobox library.
- Change filtering, grouping, row ordering, row activation, or data-fetch behavior.
- Add new network APIs or backend behavior.
- Redesign visual styling beyond attributes and focus behavior required for accessibility.

## Decisions

### D1 — Keep focus on the search input and use `aria-activedescendant`

Use the existing input-focused interaction model instead of moving DOM focus to each result row. The input will advertise the active result via `aria-activedescendant`, pointing to the stable DOM id of the active `role="option"`.

Rationale: users can keep typing while navigating results, and the current implementation already treats rows as virtual active descendants rather than tab stops.

Alternative considered: move focus directly to each row on arrow navigation. Rejected because it would interrupt typing, require additional focus-return handling, and diverge from the current command-palette behavior.

### D2 — Add stable input/listbox/option ARIA relationships

Add stable ids for the result list and each option. The input should reference the listbox with `aria-controls` when results exist and reference the active option with `aria-activedescendant` when there is a valid active row. Each option keeps `role="option"` and `aria-selected`.

Rationale: `aria-selected` on an unfocused option is not enough for screen readers to infer the active result. `aria-activedescendant` is the correct bridge when DOM focus stays on the input.

### D3 — Implement a local focus trap inside the component

Add a dialog ref and handle `Tab` / `Shift+Tab` in the existing permanent keydown listener. The handler should collect focusable elements inside the dialog, wrap from last to first and first to last, and prevent focus from leaving the modal. If no focusable child exists, focus the dialog fallback.

Rationale: this avoids adding a dependency and keeps the behavior scoped to the self-contained component. It also supports future focusable elements inside the palette without requiring a rewrite.

Alternative considered: prevent all `Tab` events and always refocus the input. Rejected because it works today only because the input is the sole tab stop; it would become incorrect as soon as the dialog contains another focusable control.

### D4 — Test behavior through DOM focus and ARIA attributes

Add tests that verify `Tab` does not move focus to an outside control and that arrow navigation updates `aria-activedescendant` to an existing selected option.

Rationale: these tests assert the user-observable accessibility contract without coupling to private helper names.

## Risks / Trade-offs

- [Risk] A broad focusable selector may include hidden or disabled elements. → Mitigation: filter disabled, hidden, and `aria-hidden="true"` elements and rely on browser focusability rules where practical.
- [Risk] Generated option ids may contain row ids with characters that are awkward in CSS selectors. → Mitigation: tests should resolve active options with `document.getElementById`, not CSS selector interpolation; implementation can use a deterministic prefix plus the existing row id.
- [Risk] Adding `role="combobox"` incorrectly could conflict with the dialog pattern if not wired fully. → Mitigation: only add roles/attributes that match the implemented behavior; keep the modal dialog on the container and connect the input to the listbox/active option explicitly.
- [Risk] Focus trap can interfere with existing close/focus-restore behavior. → Mitigation: preserve the current open/close lifecycle and add dedicated regression coverage for focus containment rather than changing restoration semantics.
