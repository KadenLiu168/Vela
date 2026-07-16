## 1. Accessibility tests

- [x] 1.1 Add a regression test in `apps/web/src/components/CommandPalette.test.tsx` that renders a focusable element outside the palette, opens the palette, presses `Tab`, and verifies document focus remains inside `data-testid="command-palette"` instead of moving to the outside element.
- [x] 1.2 Add a regression test for `Shift+Tab` from the first focusable element inside the palette, verifying focus wraps within the dialog and remains inside `data-testid="command-palette"`.
- [x] 1.3 Add a regression test that presses `ArrowDown` with visible rows, reads the search input's `aria-activedescendant`, verifies the referenced element exists, and verifies it has `role="option"` plus `aria-selected="true"`.
- [x] 1.4 Add a regression test that verifies the search input's `aria-controls` points to an existing `role="listbox"` when visible rows exist.

## 2. Focus containment implementation

- [x] 2.1 Add a dialog ref to `CommandPalette.tsx` and attach it to the `data-testid="command-palette"` dialog element.
- [x] 2.2 Add a small local helper for collecting focusable elements inside the dialog, excluding disabled, hidden, and `aria-hidden="true"` elements.
- [x] 2.3 Extend the existing permanent `keydown` handler to handle `Tab` and `Shift+Tab` while the palette is open: prevent focus from leaving the dialog, wrap from last to first and first to last, and focus the dialog fallback if no focusable child exists.
- [x] 2.4 Give the dialog a fallback `tabIndex={-1}` without adding it to the normal tab order.

## 3. Active descendant implementation

- [x] 3.1 Add stable ids for the result listbox and each rendered option in `CommandPalette.tsx`.
- [x] 3.2 Add `aria-controls` to the search input when visible results exist, pointing to the listbox id.
- [x] 3.3 Add `aria-activedescendant` to the search input when `validActiveRowId` exists, pointing to the matching option id.
- [x] 3.4 Add the matching `id` attribute to each `role="option"` row while preserving existing `aria-selected`, `tabIndex={-1}`, click behavior, and active-row styling.

## 4. Verification

- [x] 4.1 Run the focused command palette test file and verify the new accessibility tests pass.
- [x] 4.2 Run the existing web test command or type-check command normally used for this app if available, and document any pre-existing unrelated failures separately.
- [x] 4.3 Confirm no filtering, row activation, ETF expansion, close, or focus-restoration tests regressed.
