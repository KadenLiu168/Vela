## Purpose

Defines the web client's cross-page orientation contract: what the user is shown, focused on, and can return to after moving between the application's declared routes.

## ADDED Requirements

### Requirement: Route transitions reset the reading position and focus the page identity
On an in-application navigation from one declared path to a different declared path, the web frontend SHALL reset the window reading position to the top of the document and SHALL move focus to the destination page's document-level `<h1>`. The destination `<h1>` SHALL be programmatically focusable without entering the sequential tab order, and SHALL NOT display a visible focus indicator when focused this way. The initial render of the application SHALL NOT move focus. A navigation whose target location carries a non-empty hash SHALL NOT reset the reading position, so that in-document anchor targets remain honored.

#### Scenario: Navigating to another path lands at the top of that page
- **WHEN** a user activates an internal link to a different declared path
- **THEN** the window reading position is at the top of the document
- **AND** focus is on the destination page's document-level `<h1>`

#### Scenario: Lazy destination is focused once its content has rendered
- **WHEN** the destination path's route module has not been loaded yet, so a loading fallback renders first
- **THEN** after the destination page's content has rendered, the reading position is at the top and focus is on the destination page's `<h1>`
- **AND** focus is not left on the loading fallback

#### Scenario: First render does not steal focus
- **WHEN** the application renders a declared path as its initial document load
- **THEN** the application does not move focus

#### Scenario: In-document anchor navigation is not cancelled
- **WHEN** a user activates an in-document anchor link on the current page, such as a Dashboard next-action link to a form control
- **THEN** the reading position is not reset to the top of the document

#### Scenario: The focused heading is not a tab stop
- **WHEN** a user traverses the document with the Tab key after a route transition
- **THEN** the page's `<h1>` is not part of the sequential tab order

### Requirement: Document title identifies the current route
The document title SHALL identify the currently rendered route as `<page identity> · Vela Research`. The page identity SHALL begin with the visible text of that route's document-level `<h1>`. On a detail route the page identity SHALL additionally contain the route's entity identifier, so that two open detail routes of the same kind are distinguishable. The title SHALL be updated on every in-application route change and SHALL NOT be left over from the previously rendered route.

#### Scenario: Static and list routes title themselves
- **WHEN** the user opens `/`, `/signals`, `/backtests`, or `/walk-forwards`
- **THEN** the document title is `Dashboard · Vela Research`, `Signals · Vela Research`, `Backtests · Vela Research`, or `Walk-forward History · Vela Research` respectively

#### Scenario: Detail routes title themselves with their identifier
- **WHEN** the user opens `/signals/{id}`, `/backtests/{id}`, or `/etfs/{id}`
- **THEN** the document title begins with that page's `<h1>` text
- **AND** the document title contains the requested identifier
- **AND** the document title ends with ` · Vela Research`

#### Scenario: Unmatched route titles itself
- **WHEN** the user opens a path outside the declared route tree
- **THEN** the document title is `Page not found · Vela Research`

#### Scenario: Title does not leak from the previous route
- **WHEN** a user navigates from one declared path to another declared path
- **THEN** the document title reflects the destination route
- **AND** the previous route's identity is not retained

### Requirement: List pagination is addressable through the URL
The Signal, Backtest, and Walk-forward history pages SHALL reflect a non-zero pagination offset in the URL query as `offset`, while the first page SHALL omit the parameter, matching the existing convention that an unset default query value is absent. A valid `offset` value present on entry SHALL initialize the list at that offset. An invalid `offset` value SHALL be normalized through Router replacement navigation that removes only `offset` while preserving unrelated query parameters and the hash, and the list SHALL load from the first page. Changing page SHALL update `offset` in the URL while preserving unrelated query parameters and the hash. Changing the Signal source filter SHALL remove `offset` so that the list returns to the first page. Following a row's detail link and returning to the list through browser Back SHALL restore the same offset.

#### Scenario: Valid offset on entry initializes the list page
- **WHEN** the user opens `/signals?offset=40`
- **THEN** the list request uses offset 40
- **AND** the pagination controls reflect that earlier pages exist

#### Scenario: Invalid offset is normalized
- **WHEN** the user opens a list path with an `offset` value that is not a non-negative decimal integer
- **THEN** the list loads from the first page
- **AND** Router replacement navigation removes only `offset` while preserving unrelated query parameters and the hash

#### Scenario: Paging updates the URL
- **WHEN** the user activates the pagination control for the next page
- **THEN** the list requests the next offset
- **AND** the URL query carries that offset
- **AND** unrelated query parameters and the hash are unchanged

#### Scenario: Returning to the first page drops the parameter
- **WHEN** the user activates the pagination control that returns the list to offset zero
- **THEN** the list requests offset zero
- **AND** the URL query no longer carries `offset`

#### Scenario: Source filter selection returns to the first page
- **WHEN** the user changes the Signal source filter while the URL carries a non-zero `offset`
- **THEN** the next request uses offset zero
- **AND** the URL no longer carries `offset`
- **AND** the existing behavior of preserving unrelated query parameters and the hash is unchanged

#### Scenario: Returning from a detail page restores the list page
- **WHEN** a user pages a history list to a non-zero offset, follows a row's detail link, and then uses the browser Back control
- **THEN** the list renders at the same offset it showed before the detail page was opened

### Requirement: Pagination states the rows it covers and follows the button contract
Each paginated list SHALL render its pagination controls as a labeled navigation region that states which rows of the list are currently on screen. When the endpoint reports a total count, the statement SHALL include that total; when it does not, the statement SHALL state the range alone. When the current offset has no rows, the statement SHALL say so rather than stating an empty range. The statement SHALL be exposed as a status region so that a page change is announced. The Previous and Next controls SHALL each carry exactly one `design-system` button variant className, so the paging controls are rendered by the variant contract rather than by browser defaults.

#### Scenario: Range and total are stated together
- **WHEN** a paginated list renders a page at a non-zero offset with a known total
- **THEN** the pagination region states the first and last row numbers on screen and the total count

#### Scenario: Absent total still yields a range
- **WHEN** a paginated list renders and the endpoint does not report a total count
- **THEN** the pagination region states the range without a total

#### Scenario: An offset with no rows says so
- **WHEN** a paginated list renders at an offset whose response contains no rows
- **THEN** the pagination region states that there are no rows at that offset
- **AND** it does not render a range with no rows in it

#### Scenario: Page changes are announced
- **WHEN** the user moves to another page
- **THEN** the range statement is exposed as a status region

#### Scenario: Paging controls carry a button variant
- **WHEN** the pagination controls render
- **THEN** each control's `className` carries exactly one `design-system` button variant

### Requirement: Detail pages link back to their originating list
Each detail route SHALL render a Router link back to the list it was reached from, placed before the page's detail content in document order. The link SHALL NOT cause a document reload. Signal Detail SHALL link to `/signals`, Backtest Detail SHALL link to `/backtests`, and ETF Detail SHALL link to Dashboard `/`. Signal Detail, Backtest Detail, and ETF Detail SHALL render that link in every load state, including a loading, failed, or not-found state, so a detail page that could not be read is not a dead end. Walk-forward Detail's existing back link inside its Run Header SHALL be preserved.

A history-list row SHALL record the list location it was clicked from, including that list's pagination offset and filter, and the destination detail page's back link SHALL return to that recorded location. The app's own back link SHALL therefore preserve the same list context that the browser's Back control preserves. When no location was recorded — a direct visit, a bookmark, or a reload that lost the state — the back link SHALL fall back to the list's own path. A recorded location that is not an in-application path SHALL be ignored in favour of the fallback.

#### Scenario: Signal and Backtest detail offer their list
- **WHEN** the user opens `/signals/{id}` or `/backtests/{id}`
- **THEN** the page renders a link to `/signals` or `/backtests` respectively
- **AND** the link precedes the page's detail content

#### Scenario: Back link returns to the recorded list page
- **WHEN** a user pages a history list to a non-zero offset, opens a row's detail page, and activates that detail page's back link
- **THEN** the destination is the list location the row was clicked from, including its offset
- **AND** the list requests that offset again

#### Scenario: Back link falls back without a recorded location
- **WHEN** a detail page is opened directly, without a row recording where it came from
- **THEN** its back link targets the list's own path with no query

#### Scenario: A non-application recorded location is refused
- **WHEN** a recorded list location is not an in-application path
- **THEN** the back link targets the list's own path instead

#### Scenario: ETF detail offers Dashboard
- **WHEN** the user opens `/etfs/{id}`
- **THEN** the page renders a link to `/`
- **AND** the link precedes the page's detail content

#### Scenario: Failed detail pages still offer the way back
- **WHEN** a Signal, Backtest, or ETF detail read is loading, has failed, or reports a not-found identifier
- **THEN** the page still renders its back link

#### Scenario: Back link navigates without reloading the document
- **WHEN** the user activates any detail page's back link
- **THEN** the destination route renders through Router navigation
- **AND** the document is not reloaded

### Requirement: AppShell provides a keyboard skip link
AppShell SHALL render a skip link as the first focusable element of the document, targeting the main content region. The skip link SHALL be visually hidden while unfocused and visible while focused. Activating it SHALL move focus into the main content region without a document reload.

#### Scenario: Skip link is the first focusable element
- **WHEN** a user presses Tab as the first keyboard interaction of a document load
- **THEN** the skip link receives focus
- **AND** it is visible while focused

#### Scenario: Skip link moves focus into main content
- **WHEN** the user activates the skip link
- **THEN** focus moves into the main content region
- **AND** the document is not reloaded
