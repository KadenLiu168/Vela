## Why

The command palette is declared as a modal dialog, but keyboard focus can leave it with `Tab`, and the visually active result is not exposed to assistive technology. This creates a real accessibility mismatch between the UI's modal semantics and its keyboard/screen-reader behavior.

## What Changes

- Trap `Tab` and `Shift+Tab` focus within the command palette while it is open.
- Keep keyboard focus on the search input while exposing the active result through ARIA relationships.
- Add stable DOM identifiers for the listbox and options so `aria-activedescendant` can point at the active option.
- Add regression tests for focus containment and active-descendant screen-reader exposure.
- No API, route, or data model changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `command-palette`: Adds accessibility requirements for modal focus containment and active option announcement.

## Impact

- `apps/web/src/components/CommandPalette.tsx`: modal focus handling and ARIA attributes.
- `apps/web/src/components/CommandPalette.test.tsx`: accessibility regression coverage.
- `openspec/specs/command-palette/spec.md`: capability contract is extended via this change's delta spec.
