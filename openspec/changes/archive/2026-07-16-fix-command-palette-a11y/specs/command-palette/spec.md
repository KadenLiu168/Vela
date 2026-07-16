## ADDED Requirements

### Requirement: Modal focus is contained while open
The command palette SHALL keep keyboard focus inside the dialog while the palette is open. Pressing `Tab` or `Shift+Tab` SHALL cycle through focusable elements inside the dialog and SHALL NOT move focus to page content behind the modal.

#### Scenario: Tab does not leave the dialog
- **WHEN** the palette is open
- **AND** keyboard focus is on a focusable element inside `data-testid="command-palette"`
- **AND** the user presses `Tab`
- **THEN** document focus SHALL remain inside `data-testid="command-palette"`
- **AND** focus SHALL NOT move to any focusable element outside the dialog

#### Scenario: Shift Tab wraps within the dialog
- **WHEN** the palette is open
- **AND** keyboard focus is on the first focusable element inside `data-testid="command-palette"`
- **AND** the user presses `Shift+Tab`
- **THEN** document focus SHALL remain inside `data-testid="command-palette"`
- **AND** focus SHALL move to the last focusable element inside the dialog

### Requirement: Active result is exposed to assistive technology
The command palette SHALL expose the active visible result through ARIA while DOM focus remains on the search input. The search input SHALL reference the results list and SHALL set `aria-activedescendant` to the DOM id of the active `role="option"` when an active option exists.

#### Scenario: Arrow navigation updates active descendant
- **WHEN** the palette is open
- **AND** visible results exist
- **AND** the user presses `ArrowDown`
- **THEN** the search input SHALL have an `aria-activedescendant` value
- **AND** an element with that id SHALL exist in the document
- **AND** that element SHALL have `role="option"`
- **AND** that element SHALL have `aria-selected="true"`

#### Scenario: Search input references the result list
- **WHEN** the palette is open
- **AND** visible results exist
- **THEN** the search input SHALL reference the results list with `aria-controls`
- **AND** the referenced element SHALL have `role="listbox"`
