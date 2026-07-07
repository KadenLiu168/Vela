# web-frontend-app Specification

## Purpose
TBD - created by archiving change 2026-07-05-add-setup-bootstrap-endpoint. Update Purpose after archive.
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
Every page rendered inside the AppShell's `<main>` landmark MUST
contain exactly one `<h1>` element representing the page identity.
The existing `<h1>Vela Research</h1>` in the AppShell `<header>`
(banner landmark) MAY remain; multiple `<h1>`s across distinct
landmarks is permitted.

#### Scenario: Dashboard renders one <h1> in main
- **WHEN** the user navigates to `/` (Dashboard)
- **THEN** the page body inside `<main>` MUST contain exactly one
      `<h1>` element
- **AND** that element MUST be the page identity
      (`Workflow Dashboard` or whatever the current title becomes)

#### Scenario: Signal Detail renders one <h1> in main
- **WHEN** the user navigates to `/signals/:id`
- **THEN** the page body inside `<main>` MUST contain exactly one
      `<h1>` element

#### Scenario: Backtest Detail renders one <h1> in main
- **WHEN** the user navigates to `/backtests/:id`
- **THEN** the page body inside `<main>` MUST contain exactly one
      `<h1>` element

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

### Requirement: Card heading 左右反转

The Dashboard card heading SHALL place the title (white, larger type) on the left as the primary reading anchor and the eyebrow (gray, smaller type) on the right as a secondary classification label.

The `PanelHeading` component SHALL make `eyebrow` optional; cards without an eyebrow SHALL render only the title and optional statusPill on the left.

#### Scenario: Market card heading is reversed

- **WHEN** the Dashboard renders the Market panel
- **THEN** the PanelHeading SHALL display `Market data` as the left-aligned title and `Price` as the right-aligned eyebrow

#### Scenario: Strategy card heading is reversed

- **WHEN** the Dashboard renders the Strategy panel
- **THEN** the PanelHeading SHALL display `Strategy` as the left-aligned title and `Config` as the right-aligned eyebrow

#### Scenario: Signal card omits eyebrow

- **WHEN** the Dashboard renders the Signal panel
- **THEN** the PanelHeading SHALL display `Latest signal` as the title with no eyebrow
- **AND** the statusPill SHALL remain adjacent to the title

#### Scenario: Backtest card omits eyebrow

- **WHEN** the Dashboard renders the Backtest panel
- **THEN** the PanelHeading SHALL display `Latest backtest` as the title with no eyebrow
- **AND** the statusPill SHALL remain adjacent to the title

#### Scenario: Fetches card omits eyebrow

- **WHEN** the Dashboard renders the Fetches panel
- **THEN** the PanelHeading SHALL display `Data fetches` as the title with no eyebrow
- **AND** the statusPill SHALL remain adjacent to the title

### Requirement: Market data card internal layout

The Market data card (`.market-panel`) SHALL render its content in the following order from top to bottom:

1. **Metric row** — two `.metric` tiles in a 2-column grid: "Price rows" (total row count) and "Covered ETFs" (number of ETFs with data).
2. **Coverage timeline** — a horizontal layout with earliest trade date on the left, a graphite connector bar in the middle, and latest trade date on the right. Each date endpoint shows a label (uppercase "Earliest" / "Latest") above the date in monospace.
3. **ETF list** — ETFs rendered as a flat single-column list with no category grouping.

#### Scenario: Coverage timeline shows date range

- **WHEN** the Dashboard renders the Market panel with non-null `earliest_trade_date` and `latest_trade_date`
- **THEN** a `.coverage-timeline` element SHALL appear between the metric row and the ETF list
- **AND** it SHALL display `Earliest` label above the earliest date on the left and `Latest` label above the latest date on the right
- **AND** a `.coverage-timeline-bar` SHALL connect the two endpoints

#### Scenario: Coverage timeline omitted when dates are null

- **WHEN** `earliest_trade_date` or `latest_trade_date` is null
- **THEN** NO `.coverage-timeline` SHALL be rendered

#### Scenario: ETF list renders as flat single-column grid

- **WHEN** the Dashboard renders the Market panel with a non-empty `etf_list`
- **THEN** each ETF SHALL render as an `.etf-row` directly inside `.etf-row-list` with no category grouping
- **AND** `.etf-row-list` SHALL use a single-column CSS grid (`grid-template-columns: 1fr`)
- **AND** each ETF row SHALL show a colored accent bar, the symbol in monospace, `·`, the full name, and the `earliest_trade_date` at the right end
- **AND** rows SHALL NOT have border-top separators; hover SHALL show `background: var(--surface-slate)`

#### Scenario: Empty ETF list renders nothing

- **WHEN** `etf_list` is empty
- **THEN** no `.etf-row-list` container SHALL be rendered
- **AND** the card content SHALL stop after the coverage timeline (or metric row if timeline is also absent)

