# web-frontend-app Specification

## Purpose
Defines the web frontend's Dashboard setup-bootstrap action and its three-step status display, wired to `POST /api/setup/bootstrap`.
## Requirements
### Requirement: Dashboard setup bootstrap action
The web frontend SHALL expose a Dashboard action that triggers the local setup bootstrap endpoint through the shared frontend API client and renders a three-step status display.

#### Scenario: User triggers bootstrap from the Dashboard
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the "Bootstrap / Setup database & data" action
- **THEN** the frontend sends `POST /api/setup/bootstrap` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate submissions while the request is pending

#### Scenario: Dashboard shows three-step status during and after bootstrap
- **WHEN** the bootstrap request returns a response
- **THEN** the Dashboard renders one status row per bootstrap step (`migrate`, `sync_etf_pool`, `fetch_full_market_data`) using the response's `steps` array
- **AND** each status row shows a success or failure indicator matching the step's `status`
- **AND** a failed step row shows the step's `error_message`
- **AND** the Dashboard shows the response's `total_duration_seconds` as a final total once all steps have settled

#### Scenario: Dashboard refreshes aggregate data after successful bootstrap
- **WHEN** the bootstrap request returns a response with `status = "success"`
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed market data status, latest signal status, and recent backtest status are rendered from the latest Dashboard response

### Requirement: Bootstrap button uses primary visual variant
The web frontend SHALL render the "Bootstrap / Setup database &
data" Dashboard action in the primary (filled) button variant
and SHALL place it at the right end of the Dashboard action list.
The acid-lime reservation rule (added to the `design-system`
capability by this change) and the per-button variant className
contract (in `unify-buttons-into-three-variants`) jointly enforce
that no other Dashboard element except this Bootstrap button
renders an acid-lime filled background. Until those companion
changes land, this requirement pins Bootstrap as the designated
primary CTA; the visual enforcement is enforced by the next
OpenSpec change.

#### Scenario: Bootstrap is the rightmost Dashboard action
- **WHEN** the Dashboard renders its action list
- **THEN** the Bootstrap action MUST be the rightmost `<button>`
      element in the rendered list

#### Scenario: nav-link active state is not an acid-lime fill
- **WHEN** the user is on any route rendered through AppShell
- **THEN** the `.app-nav-link[aria-current="page"]` element MUST
      NOT use `var(--color-acid-lime)` as a `background`
- **AND** the active nav-link MAY use the lime as a 2px
      `box-shadow` inset underline or other non-fill decoration
- **AND** its text color MUST be `var(--color-paper)` resting
      and `var(--color-bone)` on `:hover`

### Requirement: Every page in <main> begins with one <h1>
Every page rendered through AppShell MUST expose exactly one document-level `<h1>` element representing the current page identity. The AppShell banner brand MUST render as non-heading text and MUST NOT contribute an additional `<h1>`.

#### Scenario: AppShell brand is non-heading text
- **WHEN** any route rendered through AppShell is displayed
- **THEN** the `Vela Research` brand in the AppShell banner MUST NOT render as an `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, or `<h6>` element
- **AND** the brand MUST remain visible as text in the banner

#### Scenario: Dashboard renders one <h1> in main
- **WHEN** the user navigates to `/` (Dashboard)
- **THEN** the rendered document MUST contain exactly one `<h1>` element
- **AND** that element MUST be the Dashboard page identity heading

#### Scenario: Signal Detail renders one <h1> in main
- **WHEN** the user navigates to `/signals/:id`
- **THEN** the rendered document MUST contain exactly one `<h1>` element
- **AND** that element MUST be the Signal Detail page identity heading

#### Scenario: Backtest Detail renders one <h1> in main
- **WHEN** the user navigates to `/backtests/:id`
- **THEN** the rendered document MUST contain exactly one `<h1>` element
- **AND** that element MUST be the Backtest Detail page identity heading

#### Scenario: Signal list renders the only document-level <h1>
- **WHEN** the user navigates to `/signals`
- **THEN** the rendered document MUST contain exactly one `<h1>` element
- **AND** that element MUST be the Signals page identity heading

#### Scenario: Backtest list renders the only document-level <h1>
- **WHEN** the user navigates to `/backtests`
- **THEN** the rendered document MUST contain exactly one `<h1>` element
- **AND** that element MUST be the Backtests page identity heading

#### Scenario: ETF Detail renders the only document-level <h1>
- **WHEN** the user navigates to `/etfs/:id`
- **THEN** the rendered document MUST contain exactly one `<h1>` element
- **AND** that element MUST be the ETF Detail page identity heading

### Requirement: EmptyAction advertises its variant
The Dashboard's component-level `EmptyAction` function MUST
accept a `variant` prop and MUST render the matching
`.button-{primary,secondary,tertiary}` className on its
inner `<button>` element, satisfying the "Buttons declare
their variant via className" rule in the `design-system`
capability.

#### Scenario: EmptyAction accepts a variant prop
- **WHEN** a developer reads the `EmptyAction` function
      signature in `apps/web/src/pages/DashboardPage.tsx`
- **THEN** its parameter list MUST include a `variant`
      parameter typed as one of the three literal strings
      `"button-primary"`, `"button-secondary"`, or
      `"button-tertiary"`
- **AND** the parameter MUST default to `"button-secondary"`
      so existing call sites without an explicit `variant`
      prop render exactly as they do today

#### Scenario: EmptyAction renders the variant className
- **WHEN** the `EmptyAction` function returns its JSX
- **THEN** the rendered `<button>` element's `className`
      MUST be the value of the `variant` prop (verbatim),
      not the hardcoded literal `"button-secondary"`
- **AND** the rendered DOM MUST therefore carry a variant
      class that satisfies the `design-system` capability's
      "Buttons declare their variant via className"
      Requirement

#### Scenario: existing call sites continue to render a secondary button
- **WHEN** `EmptyAction` is invoked without an explicit
      `variant` prop (the two existing call sites in
      `DashboardPage.tsx`)
- **THEN** the rendered `<button>` carries
      `className="button-secondary"`
- **AND** the visual outcome is byte-identical to the
      pre-change render of those two call sites

### Requirement: PanelHeading 标签语义一致性

The web frontend Dashboard SHALL use semantically consistent PanelHeading label pairs across all workflow cards, eliminating redundant or conflicting eyebrow/title combinations.

#### Scenario: Market card shows domain-content labels

- **WHEN** the Dashboard renders the Market panel
- **THEN** the PanelHeading SHALL display `Market` as eyebrow and `Price data` as title

#### Scenario: Strategy card shows domain-content labels

- **WHEN** the Dashboard renders the Strategy panel
- **THEN** the PanelHeading SHALL display `Strategy` as eyebrow and `Parameters` as title

#### Scenario: Signal card shows contextual result labels

- **WHEN** the Dashboard renders the Signal panel
- **THEN** the PanelHeading SHALL display `Signal` as eyebrow and `Latest result` as title
- **AND** the statusPill SHALL be preserved in its current position

#### Scenario: Backtest card shows contextual result labels

- **WHEN** the Dashboard renders the Backtest panel
- **THEN** the PanelHeading SHALL display `Backtest` as eyebrow and `Latest result` as title
- **AND** the statusPill SHALL be preserved in its current position

### Requirement: Signal history list page
The web frontend SHALL expose a `/signals` route rendering a paginated table of historical successful strategy signals for the current strategy and version, with each row linking to that signal's detail page.

#### Scenario: List renders signal rows
- **WHEN** the user navigates to `/signals` and successful signals exist
- **THEN** the page renders one row per signal showing at least signal id, signal date, config version, result, and generated timestamp
- **AND** each row links to `/signals/{signal_id}`

#### Scenario: List paginates history
- **WHEN** the signal history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Empty signal history
- **WHEN** the user navigates to `/signals` and no successful signal exists
- **THEN** the page renders an empty state directing the user to generate a signal from the Dashboard

### Requirement: Backtest history list page
The web frontend SHALL expose a `/backtests` route rendering a paginated table of historical backtest runs for the current strategy and version, with each row linking to that run's detail page.

#### Scenario: List renders backtest rows
- **WHEN** the user navigates to `/backtests` and backtest runs exist
- **THEN** the page renders one row per run showing at least run id, date range, status, and started timestamp
- **AND** each row links to `/backtests/{run_id}`

#### Scenario: List paginates history
- **WHEN** the backtest history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Empty backtest history
- **WHEN** the user navigates to `/backtests` and no backtest run exists
- **THEN** the page renders an empty state directing the user to run a backtest from the Dashboard

### Requirement: Signal detail page fetches by id
The web frontend SHALL fetch the signal detail for `/signals/:id` by the route's signal id, not by a latest-only API.

#### Scenario: Detail fetches the requested id
- **WHEN** the user navigates to `/signals/{signal_id}`
- **THEN** the frontend calls the by-id signal detail endpoint with that `signal_id`
- **AND** the rendered detail corresponds to that signal id

#### Scenario: Unknown or foreign signal id shows not-found state
- **WHEN** the user navigates to `/signals/{signal_id}` and the API returns 404
- **THEN** the page renders a not-found empty state

### Requirement: Backtest detail page fetches by id
The web frontend SHALL fetch the backtest detail for `/backtests/:id` by the route's run id, and render a not-found state on 404.

#### Scenario: Detail fetches the requested id
- **WHEN** the user navigates to `/backtests/{run_id}`
- **THEN** the frontend calls the by-id backtest detail endpoint with that `run_id`
- **AND** the rendered detail corresponds to that run id

#### Scenario: Unknown or foreign run id shows not-found state
- **WHEN** the user navigates to `/backtests/{run_id}` and the API returns 404
- **THEN** the page renders a not-found empty state

### Requirement: Signal and backtest browse navigation entries
The web frontend SHALL expose nav entries "Signals" pointing to `/signals` and "Backtests" pointing to `/backtests` as the canonical browse entry points.

#### Scenario: Nav offers signal and backtest list entries
- **WHEN** the user inspects the primary navigation
- **THEN** the nav includes a "Signals" entry with href `/signals`
- **AND** the nav includes a "Backtests" entry with href `/backtests`
- **AND** no nav entry points to `/signals/demo-signal`

### Requirement: Signal detail target holdings shows ETF name
The web frontend SHALL render a target holdings table on the Signal Detail page from the by-id signal detail API `positions`, and the table SHALL include an ETF name column populated from each position's `name` field, in addition to the existing exchange, symbol, target weight, rank, score, and fallback columns.

#### Scenario: Signal Detail renders a target holdings table from the by-id API
- **WHEN** the Signal Detail page loads the signal detail for the current route id
- **THEN** the page renders a target holdings table populated from the by-id signal detail API `positions`

#### Scenario: Target holdings table includes a name column
- **WHEN** the Signal Detail page renders the target holdings table
- **THEN** the table includes a "Name" column
- **AND** the Name column is placed immediately after the Symbol column
- **AND** the existing Exchange, Target weight, Rank, Score, and Fallback columns keep their current content and relative ordering, shifting right only to accommodate the new Name column

#### Scenario: Name column is populated from the API name field
- **WHEN** a position in the signal detail API response includes a `name` value
- **THEN** the Name column shows that value for the matching row

