# command-palette Specification

## Purpose
Defines the web frontend's global command palette, opened via `Cmd/Ctrl+K` or `/`, for fast navigation and actions across the app.
## Requirements
### Requirement: Global keyboard shortcut opens the command palette
The web frontend SHALL open a single global command palette when the user presses `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux). The same palette SHALL also open when the user presses the `/` key while no `input`, `textarea`, `select`, or `contenteditable` element has focus. Pressing the same shortcut again while the palette is open SHALL close it.

#### Scenario: Cmd+K opens the palette
- **WHEN** the user is on any page rendered through `AppShell`
- **AND** the user presses `Cmd+K` (macOS) or `Ctrl+K` (Windows/Linux) on a focused element that is not an `input`, `textarea`, `select`, or `contenteditable`
- **THEN** the `data-testid="command-palette"` element SHALL appear in the DOM
- **AND** the `data-testid="command-palette-input"` element SHALL be the document's active element
- **AND** the input's value SHALL be the empty string

#### Scenario: Slash opens the palette from a non-input focus
- **WHEN** the user is on any page rendered through `AppShell`
- **AND** the focused element is not an `input`, `textarea`, `select`, or `contenteditable`
- **AND** the user presses `/`
- **THEN** the `data-testid="command-palette"` element SHALL appear in the DOM

#### Scenario: Slash inside a text input types a literal slash
- **WHEN** the user is on any page rendered through `AppShell`
- **AND** the focused element is an `input` (e.g. the Dashboard Bootstrap form field)
- **AND** the user presses `/`
- **THEN** the palette SHALL NOT open
- **AND** the input's value SHALL receive the literal `/` character

#### Scenario: Toggling the shortcut closes the palette
- **WHEN** the palette is open
- **AND** the user presses `Cmd+K` (or `Ctrl+K`)
- **THEN** the `data-testid="command-palette"` element SHALL be removed from the DOM
- **AND** document focus SHALL be restored to the element that was focused before the palette was opened

#### Scenario: Escape closes the palette
- **WHEN** the palette is open
- **AND** the user presses `Escape`
- **THEN** the `data-testid="command-palette"` element SHALL be removed from the DOM
- **AND** document focus SHALL be restored to the element that was focused before the palette was opened

### Requirement: Palette row model and data sources
The command palette SHALL surface exactly four row kinds, built from these data sources:
- **page** rows: hard-coded list of the three AppShell `navItems` (`/`, `/signals`, `/backtests`).
- **backtest** rows: the result of `listBacktests(10)` (already exposed in `apps/web/src/api/client.ts`).
- **etf** rows: the `etf_list` field on the response of `getDashboard()` (already exposed in `apps/web/src/api/client.ts`).
- **action** rows: the three dashboard actions (Bootstrap local database, Generate strategy signal, Run backtest) bound to the same code paths the Dashboard buttons call today (`bootstrapLocalDatabase`, `generateStrategySignal`, `runBacktest`).

The palette SHALL also surface the latest signal as a single **backtest**-shaped row (or as a dedicated **signal** row kind if the implementation chooses to introduce one), sourced from `getLatestStrategySignal()`.

#### Scenario: Palette fetches data on open
- **WHEN** the palette transitions from closed to open
- **THEN** the palette SHALL issue a `listBacktests(10)` request
- **AND** the palette SHALL issue a `getLatestStrategySignal()` request
- **AND** the palette SHALL issue a `getDashboard()` request
- **AND** all three requests SHALL be issued in parallel (no serial waterfall)
- **AND** until all three have settled, the `data-testid="command-palette-loading"` element SHALL be present

#### Scenario: API failure surfaces a quiet error row
- **WHEN** the palette is open
- **AND** any of `listBacktests`, `getLatestStrategySignal`, or `getDashboard` rejects
- **THEN** the palette SHALL still render the rows it has
- **AND** it SHALL render a `data-testid="command-palette-error"` row whose text mentions which source failed
- **AND** it SHALL NOT throw an unhandled error to the console for the user

### Requirement: Client-side filter algorithm
The palette SHALL filter rows by case-insensitive substring match against each row's `label` and `keywords`. The filter SHALL be a pure function `filterCommandRows(query, rows): CommandPaletteRow[]` exported from the same module as the component.

#### Scenario: Empty query shows only static pages and actions
- **WHEN** the palette is open
- **AND** the input value is the empty string (or only whitespace)
- **THEN** the visible result list SHALL contain the `page` rows and the `action` rows
- **AND** the visible result list SHALL NOT contain any `backtest` or `etf` row
- **AND** the result list SHALL be capped at 20 rows

#### Scenario: Non-empty query matches label and keywords
- **WHEN** the palette is open
- **AND** the input value is the string `"vti"`
- **THEN** every ETF row whose `label` contains `"vti"` (case-insensitive) OR whose `keywords` contains `"vti"` SHALL be visible
- **AND** rows that match on `label` SHALL be ordered before rows that match only on `keywords`
- **AND** within each band, rows SHALL be ordered alphabetically by `label`
- **AND** across bands, the group order SHALL remain Pages → Backtests → ETFs → Actions
- **AND** the result list SHALL be capped at 50 rows total

#### Scenario: No matches renders an empty row
- **WHEN** the palette is open
- **AND** the input value matches zero rows
- **THEN** a `data-testid="command-palette-empty"` element SHALL be present
- **AND** its text SHALL mention the value the user typed

### Requirement: Selection behavior per row kind
The palette SHALL handle row selection as follows:
- `page` and `backtest` rows: close the palette, restore focus, then call the row's `onSelect(path)`.
- `action` rows: close the palette, then invoke the row's `action()` inside the same try/catch the Dashboard buttons use today. The palette is not responsible for surfacing action errors; the existing `ErrorBoundary` mounted in `App.tsx` catches any thrown error exactly as it does for the Dashboard buttons.
- `etf` rows: do NOT navigate. Toggle an inline info panel inside the palette showing exchange, symbol, category, and name for that ETF. Pressing `Enter` on the same ETF while its info panel is expanded SHALL close the panel.

#### Scenario: Selecting a page row navigates
- **WHEN** the palette is open
- **AND** the user activates a `page` row (mouse click or `Enter` on the active row)
- **THEN** the `data-testid="command-palette"` element SHALL be removed from the DOM
- **AND** the URL's path SHALL change to that page's `path`

#### Scenario: Selecting a backtest row navigates
- **WHEN** the palette is open
- **AND** the user activates a `backtest` row
- **THEN** the `data-testid="command-palette"` element SHALL be removed from the DOM
- **AND** the URL's path SHALL change to `/backtests/{runId}`

#### Scenario: Selecting an action row runs the action
- **WHEN** the palette is open
- **AND** the user activates an `action` row whose id is `action-generate-signal`
- **THEN** the palette SHALL close
- **AND** the `generateStrategySignal()` client function SHALL be invoked exactly once

#### Scenario: Selecting an ETF row expands an inline info panel
- **WHEN** the palette is open
- **AND** the user activates an `etf` row whose id is `etf-arcx-vti`
- **THEN** the palette SHALL remain open
- **AND** a `data-testid="command-palette-etf-info-arcx-vti"` element SHALL appear inside the dialog
- **AND** the URL's path SHALL NOT change
- **AND** pressing `Enter` on the same ETF row again SHALL hide the info panel

### Requirement: In-palette keyboard navigation
The palette SHALL support `ArrowDown`, `ArrowUp`, and `Enter` for moving between and activating visible rows. `ArrowDown` and `ArrowUp` SHALL wrap around the visible list.

#### Scenario: ArrowDown moves the active row
- **WHEN** the palette is open
- **AND** a row is currently the active row (carries `data-testid="command-palette-row-active"`)
- **AND** the user presses `ArrowDown`
- **THEN** the active row SHALL be the next visible row in group-stable order
- **AND** if the active row was the last visible row, the new active row SHALL be the first visible row

#### Scenario: Enter activates the active row
- **WHEN** the palette is open
- **AND** a row is the active row
- **AND** the user presses `Enter`
- **THEN** the active row's `onSelect` SHALL be invoked exactly once
- **AND** the palette SHALL follow the row-kind behavior in the "Selection behavior per row kind" requirement

### Requirement: Backdrop click closes the palette
The palette SHALL render a backdrop element. Clicking the backdrop SHALL close the palette and restore focus. Clicking inside the dialog box itself SHALL NOT close the palette.

#### Scenario: Backdrop click closes the palette
- **WHEN** the palette is open
- **AND** the user clicks on `data-testid="command-palette-backdrop"`
- **THEN** the `data-testid="command-palette"` element SHALL be removed from the DOM
- **AND** document focus SHALL be restored to the element that was focused before the palette was opened

#### Scenario: Dialog click does not close the palette
- **WHEN** the palette is open
- **AND** the user clicks inside the dialog box (e.g. on a row)
- **THEN** the palette SHALL remain open
- **AND** the row's `onSelect` SHALL be invoked

### Requirement: No new design tokens are introduced
The command palette SHALL render using only CSS custom properties already declared in `apps/web/src/styles/tokens.css`. This change SHALL NOT add new tokens to `tokens.css` and SHALL NOT add a `:root { ... }` block to `apps/web/src/styles.css`.

#### Scenario: tokens.css is unchanged
- **WHEN** this change is complete
- **THEN** `apps/web/src/styles/tokens.css` SHALL be byte-identical to its pre-change state in git
- **AND** the new palette CSS rules in `apps/web/src/styles.css` SHALL reference only existing tokens (`--color-paper`, `--color-ink`, `--surface-slate`, `--radius-cards`, `--shadow-elevated`, `--font-berkeley-mono`, and similar already-declared tokens)

### Requirement: Out-of-scope follow-ups are not shipped in v1
The command palette SHALL defer the items in the "Deferred follow-ups" scenario below as out of scope for v1. A future OpenSpec change MAY address each one independently.

#### Scenario: Backend cross-entity search is deferred
- **WHEN** this change is archived
- **THEN** the system SHALL NOT add a `GET /api/search?q=` endpoint
- **AND** the v1 palette SHALL continue to operate on `listBacktests(10)`, `getLatestStrategySignal()`, and `getDashboard()` only
- **AND** the "Fuzzy / typo-tolerant matching" follow-up SHALL be tracked as a separate spec change
- **AND** the "Per-ETF detail route" follow-up SHALL be tracked as a separate spec change
- **AND** the "Persistent recent-palette-queries" follow-up SHALL be tracked as a separate spec change
- **AND** the "User-defined commands / rebindable shortcuts" follow-up SHALL be tracked as a separate spec change
- **AND** a "Focus trap inside the dialog" follow-up SHALL be tracked as a separate spec change (the v1 spec accepts the trade-off that `Tab` may leave the dialog)

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

