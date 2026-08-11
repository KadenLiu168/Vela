# web-frontend-app Specification

## Purpose
Defines the web frontend's Dashboard setup-bootstrap action and its three-step status display, wired to `POST /api/setup/bootstrap`.
## Requirements
### Requirement: Walk-forward history page lists persisted evaluations
The Web application SHALL add a lazy-loaded `/walk-forwards` page and primary navigation entry, request the current-strategy API with fixed page size 10, render persisted run metadata and compact provenance, and use the exact API total for pagination with loading, error and empty states.

#### Scenario: History rows navigate to detail
- **WHEN** persisted evaluations are returned
- **THEN** each row displays identifying metadata and opens `/walk-forwards/{id}` through client-side navigation

### Requirement: Walk-forward detail presents complete structured evidence
The Web application SHALL show execution/configuration provenance, evidence sufficiency, all eight strategy summaries, separate dual-benchmark comparisons, IS/OOS gaps, parameter stability, chronological independent OOS windows, and one stitched OOS capital-path section from the typed API response. When `stitched_oos.status` is `available`, the section SHALL render a chronological equity-curve chart, ending net value, and cumulative total return; SHALL visibly identify window-start reset boundaries in the chart or its accessible companion content; and SHALL explain that the series compounds separately initialized OOS segments without synthesizing seam return, holdings continuity, turnover, or transaction cost. When status is `unavailable_non_contiguous_windows`, the section SHALL explain that gap/overlap windows cannot form one chronological capital path and SHALL preserve every other detail section. It SHALL not convert evidence into a score or pass/fail decision and SHALL not label the stitched series as one continuously held or directly tradable portfolio.

#### Scenario: Detail preserves evidence semantics
- **WHEN** a successful detail response loads
- **THEN** metric counts/status, benchmark ownership, duration units and recovery semantics remain visible without changing their window-local aggregation
- **AND** the stitched OOS section shows the API-provided ending net value and cumulative total return without recalculating financial values in the browser

#### Scenario: Chart discloses OOS reset boundaries
- **WHEN** the stitched response contains points from multiple windows
- **THEN** the rendered chart or its accessible companion identifies every window start by ordinal and date
- **AND** nearby explanatory text states that no seam return, holdings carry, turnover, or transaction cost was synthesized

#### Scenario: Stitched path remains responsive and accessible
- **WHEN** Walk-forward detail renders at 1440x1000 or 390x844
- **THEN** the cumulative summary, chart, reset-boundary information, and existing evidence remain readable without page-level horizontal overflow
- **AND** the chart has a programmatic label and a textual empty/failure-safe fallback consistent with existing chart presentation primitives

#### Scenario: Non-contiguous status does not hide evidence
- **WHEN** the detail response reports `unavailable_non_contiguous_windows`
- **THEN** the page explains why no stitched curve is shown
- **AND** execution, provenance, aggregate evidence, parameter stability, and independent OOS windows remain visible

### Requirement: Walk-forward OOS links preserve the complete evidence chain
Every window SHALL link its OOS id to `/backtests/{id}`; current-strategy OOS runs and signals SHALL remain navigable when their `config_version` is `wf-*`, while other-strategy ids remain 404.

#### Scenario: OOS detail link opens across versions
- **WHEN** a user activates a current-strategy `wf-*` OOS link
- **THEN** the existing Backtest Detail route opens for that exact run id

### Requirement: Walk-forward pages are responsive and keyboard accessible
History/detail SHALL reuse existing presentation primitives and design tokens, remain keyboard operable, and remain readable at 1440x1000 and 390x844 without page-level horizontal overflow. A dense window table MAY use a labeled local scroll region.

#### Scenario: Narrow evidence view has no page overflow
- **WHEN** detail renders at 390x844
- **THEN** the page has no horizontal overflow outside any labeled local table region

### Requirement: Walk-forward presentation does not expand Dashboard
Walk-forward history and evidence SHALL be available only through the dedicated navigation/list/detail flow; Dashboard SHALL remain unchanged by this Change.

#### Scenario: Dashboard has no WF card
- **WHEN** successful Walk-forward history exists
- **THEN** Dashboard does not add a Walk-forward card or score

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

### Requirement: Backtest metric labels disclose annualization conventions
Every Web surface that presents annualized return, volatility, or Sharpe for a backtest SHALL visibly distinguish calendar-time CAGR from 252-trading-day return statistics without changing the underlying API field names or values.

#### Scenario: Backtest Detail labels metric conventions
- **WHEN** the Backtest Detail page renders its performance metric cards
- **THEN** `annualized_return` is labeled `CAGR (calendar-time)`
- **AND** `volatility` is labeled `Annualized volatility (252D)`
- **AND** `sharpe_ratio` is labeled `Sharpe (daily returns, 252D)`

#### Scenario: Dashboard completed-run summary labels metric conventions
- **WHEN** the Dashboard renders the completed result of a backtest operation
- **THEN** `annualized_return` is labeled `CAGR (calendar-time)`
- **AND** `volatility` is labeled `Annualized volatility (252D)`
- **AND** `sharpe_ratio` is labeled `Sharpe (daily returns, 252D)`

#### Scenario: Dashboard latest-backtest summary labels Sharpe convention
- **WHEN** the Dashboard renders the latest-backtest summary
- **THEN** its `sharpe_ratio` is labeled `Sharpe (daily returns, 252D)`

#### Scenario: Values and null formatting remain unchanged
- **WHEN** the clarified labels are rendered
- **THEN** percentage, decimal, and unavailable-value formatting continue to use the existing metric values and formatters
- **AND** the frontend does not derive Sharpe from the displayed CAGR and volatility values

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
The web frontend SHALL expose a `/signals` route rendering a paginated table of historical successful strategy signals for the current strategy and version, with each row linking to that signal's detail page. The page SHALL provide a SOURCE filter button group (All / Manual / Scheduled / Backtest / Legacy) that drives server-side filtering via the API `source` parameter. The filter buttons SHALL use the `button-secondary` variant; the active non-All option SHALL render with the variant's pressed state (inverted fill via `aria-pressed="true"`). The active non-All filter SHALL be reflected in the URL query as `?source=<value>`, while All SHALL omit the parameter. Changing the filter SHALL reset pagination to the first page.

#### Scenario: List renders signal rows
- **WHEN** the user navigates to `/signals` and successful signals exist
- **THEN** the page renders one row per signal showing at least signal id, signal date, config version, result, source, and generated timestamp
- **AND** each row links to `/signals/{signal_id}`

#### Scenario: List paginates history
- **WHEN** the signal history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Source filter narrows the list
- **WHEN** the user selects the Backtest filter button
- **THEN** the frontend requests the first page with `source=backtest`
- **AND** the table shows only entries returned for that source
- **AND** the URL query includes `source=backtest`

#### Scenario: All removes only the source query
- **WHEN** the user selects All while the URL contains `source=backtest` plus other query parameters or a hash
- **THEN** the next request omits `source`
- **AND** the URL removes only `source` while preserving the other query parameters and hash

#### Scenario: Valid source initializes the filter
- **WHEN** the user opens `/signals?source=scheduled`
- **THEN** Scheduled is active
- **AND** the first list request includes `source=scheduled`

#### Scenario: Invalid source URL is normalized
- **WHEN** the user opens `/signals` with an unknown, empty, or literal `null` source value
- **THEN** All is active and the list request omits `source`
- **AND** the invalid source parameter is removed from the URL without removing unrelated query parameters or the hash

#### Scenario: Empty signal history
- **WHEN** the user navigates to `/signals` and no successful signal exists
- **THEN** the page renders an empty state directing the user to generate a signal from the Dashboard

#### Scenario: Selected source has no results
- **WHEN** a valid non-All SOURCE filter returns no signals on its first page
- **THEN** the page renders an empty state naming or otherwise identifying the active filter

#### Scenario: Filter buttons use the secondary variant with a pressed state
- **WHEN** the user navigates to `/signals`
- **THEN** every SOURCE filter button MUST carry the `button-secondary` variant className
- **AND** the active option MUST carry `aria-pressed="true"` and render with the inverted fill

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
The web frontend SHALL fetch the backtest detail for `/backtests/:id` by the route's run id, render a not-found state on 404, and organize the detail into two tabs: an Overview tab (run metadata, metrics, equity curve, parameters) shown by default, and a Signals (N) tab whose count comes from the detail response's `signal_count`. Users SHALL be able to inspect Overview content without first traversing the run's signal list. The Signals tab SHALL load paginated summary data only when activated and only when `signal_count > 0`.

#### Scenario: Detail fetches the requested id
- **WHEN** the user navigates to `/backtests/{run_id}`
- **THEN** the frontend calls the by-id backtest detail endpoint with that `run_id`
- **AND** the rendered detail corresponds to that run id

#### Scenario: Overview tab is visible by default
- **WHEN** the backtest detail loads
- **THEN** Overview is selected
- **AND** run metadata, metrics, equity curve, and parameters are in its tabpanel
- **AND** the Signals table is not rendered ahead of those sections

#### Scenario: Signals tab label reflects signal_count
- **WHEN** the backtest detail loads
- **THEN** the Signals tab label displays the detail response's `signal_count`

#### Scenario: Unknown or foreign run id shows not-found state
- **WHEN** the user navigates to `/backtests/{run_id}` and the detail API returns 404
- **THEN** the page renders a not-found empty state

#### Scenario: Route id change resets local detail state
- **WHEN** the mounted detail page changes from one `run_id` to another
- **THEN** Overview becomes active with Signals offset zero
- **AND** stale signal-page responses from the previous run do not render for the new run

### Requirement: Signal and backtest browse navigation entries
The web frontend SHALL expose nav entries "Signals" pointing to `/signals` and "Backtests" pointing to `/backtests` as the canonical browse entry points.

#### Scenario: Nav offers signal and backtest list entries
- **WHEN** the user inspects the primary navigation
- **THEN** the nav includes a "Signals" entry with href `/signals`
- **AND** the nav includes a "Backtests" entry with href `/backtests`
- **AND** no nav entry points to `/signals/demo-signal`

### Requirement: Backtest detail tabs are keyboard accessible
The Backtest detail tabs SHALL implement an automatically activated two-tab interface using the ARIA tab pattern. Each tab SHALL identify and control one tabpanel; only the active tab SHALL be in the normal tab order.

#### Scenario: Tab semantics are connected
- **WHEN** the Backtest detail tabs render
- **THEN** their container has `role="tablist"`
- **AND** each tab has `role="tab"`, `aria-selected`, `aria-controls`, and a stable id
- **AND** each `role="tabpanel"` references its tab with `aria-labelledby`

#### Scenario: Keyboard changes the active tab
- **WHEN** focus is on a tab and the user presses ArrowLeft, ArrowRight, Home, or End
- **THEN** focus moves to the corresponding tab
- **AND** that tab becomes active

### Requirement: New signal and backtest UI follows existing presentation language
The SOURCE filter, Backtest tabs, and signals table SHALL reuse the existing panel, table, Pagination, DescriptionItem, EmptyState, and FeedbackMessage implementations where applicable, plus the design tokens in `tokens.css`. Because the repository has no existing general Tab or segmented-control primitive, those controls MAY use minimal page-scoped token-based styles. The implementation SHALL NOT duplicate existing primitive CSS or introduce a new general-purpose component abstraction for these single use cases.

#### Scenario: Source filter adds only necessary control styling
- **WHEN** the Signals list renders its SOURCE filter
- **THEN** the results panel and table reuse existing primitives
- **AND** any new segmented-control styles are page-scoped and use existing tokens

#### Scenario: Backtest tabs reuse existing content primitives
- **WHEN** the Backtest detail renders its tabs and signals table
- **THEN** tab content reuses the existing panel, table, Pagination, DescriptionItem, EmptyState, and FeedbackMessage implementations
- **AND** any new tab styles are minimal and token-based
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

### Requirement: Signals list shows a Source column

The web Signals list SHALL render a "Source" column for each signal, derived from the API `source` field, using a distinct visual badge per value.

#### Scenario: Source badges are distinguishable
- **WHEN** the Signals list renders signals
- **THEN** a `manual` signal shows a neutral badge labeled "Manual"
- **AND** a `scheduled` signal shows an info badge labeled "Scheduled"
- **AND** a `backtest` signal shows an accent badge labeled "Backtest"
- **AND** a `legacy` signal shows a muted badge labeled "Legacy"
- **AND** the legacy badge exposes accessible explanatory text that the signal predates provenance tracking

#### Scenario: Existing columns preserved
- **WHEN** the Signals list renders
- **THEN** the existing columns (Signal, Signal date, Config version, Result, Generated at) remain
- **AND** pagination behavior is unchanged

### Requirement: Signal detail shows source and backtest link

The Signal detail view SHALL display the signal `source` and, when `source` is `backtest` and `backtest_run_id` is present, SHALL render a link to `/backtests/{backtest_run_id}`.

#### Scenario: Backtest signal links to its run
- **WHEN** a user opens a signal whose `source` is `backtest` with a non-null `backtest_run_id`
- **THEN** the detail view shows a link to the producing backtest run
- **AND** activating the link navigates to that backtest's detail

#### Scenario: Live signal shows no backtest link
- **WHEN** a user opens a `manual` or `scheduled` signal
- **THEN** the detail view shows the source without a backtest link

### Requirement: Backtest detail lists its signals
The Backtest detail Signals tab SHALL render a compact table with columns Signal #, Signal date, Result, and an action link to each signal detail. It SHALL consume `GET /api/backtests/{run_id}/signals` using page size 20 and SHALL use detail `signal_count` to determine pagination boundaries. Because every linked signal has source `backtest`, the tab SHALL NOT present a source column, source filter, or source distribution. The tab SHALL show loading and error states using existing presentation primitives, and an explicit empty state when `signal_count` is zero.

#### Scenario: Signals tab shows a compact paginated table
- **WHEN** the user activates Signals for a run whose `signal_count` is greater than zero
- **THEN** the frontend requests offset zero from the paginated endpoint
- **AND** renders columns Signal #, Signal date, Result, and an action link
- **AND** renders pagination controls using `signal_count` as the known total

#### Scenario: Signals tab loads lazily
- **WHEN** the backtest detail loads with Overview active
- **THEN** the frontend does not request the backtest signals endpoint
- **AND** the first positive-count request occurs only after Signals is activated

#### Scenario: Zero-count tab avoids an unnecessary request
- **WHEN** the user activates Signals for a run whose `signal_count` is zero
- **THEN** the tab renders the no-linked-signals empty state
- **AND** does not request the paginated signals endpoint

#### Scenario: Pagination uses exact total boundaries
- **WHEN** the user views the final page and `signal_count` is an exact multiple of 20
- **THEN** Next is disabled
- **AND** the user cannot navigate to an empty page beyond the known total

#### Scenario: Signals tab has no source categorization
- **WHEN** the Signals tab renders
- **THEN** it contains no source column, source filter, or source distribution

#### Scenario: Signals tab loading and error states
- **WHEN** the paginated signals request is in flight or fails
- **THEN** the tab renders a loading or error `FeedbackMessage`
- **AND** a stale response for an earlier offset or run id does not replace the current state

### Requirement: Backtest detail shows benchmark comparison
The Backtest Detail Overview SHALL render the strategy's existing metrics together with separately labeled metric groups for "Equal-weight monthly rebalanced portfolio" and "CSI 300 buy-and-hold". Each benchmark group SHALL show its five metrics and strategy-minus-benchmark total-return and CAGR differences.

#### Scenario: Detail renders two benchmark groups
- **WHEN** a benchmark-enabled backtest detail loads
- **THEN** the Overview renders one labeled group for each fixed benchmark
- **AND** each group shows its metrics and the two relative-return differences

#### Scenario: Legacy detail has no fabricated benchmark group
- **WHEN** a legacy backtest detail has an empty benchmark collection
- **THEN** the existing strategy metrics and curve remain visible
- **AND** the page does not present fabricated benchmark values

### Requirement: Backtest detail compares three net-value curves
For a benchmark-enabled run, the Backtest Detail Overview SHALL render strategy, equal-weight monthly, and CSI 300 buy-and-hold net-value series on one accessible chart with a distinguishable legend. The chart SHALL retain its existing empty and single-strategy-curve states for legacy data.

#### Scenario: Three-series chart is distinguishable
- **WHEN** all three curve series are available
- **THEN** the chart renders all three series with a visible legend and distinguishable styling
- **AND** every series is plotted against its ordered trade dates

### Requirement: Backtest Detail presents expanded risk metrics with explicit semantics
Backtest Detail SHALL display persisted strategy Sortino, Calmar and longest drawdown duration. Each fixed benchmark group SHALL display its own Sortino, Calmar and duration plus strategy-relative Tracking Error and Information Ratio. Labels SHALL be `Sortino (rf MAR, 252D)`, `Calmar (calendar CAGR / |MaxDD|)`, `Tracking error (252D)`, and `Information ratio (252D)` or semantically equivalent text that exposes the same conventions.

#### Scenario: New run shows expanded metric groups
- **WHEN** a benchmark-enabled detail response contains expanded values
- **THEN** the Overview presents strategy and benchmark values under their correct semantic labels
- **AND** makes clear that TE/IR compare the strategy with the named benchmark

#### Scenario: Ongoing drawdown is explicit
- **WHEN** longest drawdown duration has a null recovery date
- **THEN** the detail shows duration sessions, peak and trough dates
- **AND** labels recovery as ongoing

#### Scenario: Legacy nulls do not fabricate metrics
- **WHEN** a legacy detail response has null expanded fields
- **THEN** the page renders the existing unavailable-value treatment
- **AND** does not derive values from the displayed curve

#### Scenario: Expanded groups remain readable across supported viewports
- **WHEN** Backtest Detail renders expanded strategy and benchmark groups at supported desktop and narrow viewport widths
- **THEN** metric labels, values and duration dates remain visible, correctly grouped and unclipped
- **AND** existing keyboard navigation and semantic ownership remain intact

### Requirement: Dashboard scope remains unchanged
The Dashboard summary SHALL continue to expose only its existing metric set and MUST NOT add expanded risk cards as part of this Change.

#### Scenario: Expanded detail does not expand Dashboard
- **WHEN** the Web application renders a newly completed run on Dashboard
- **THEN** no Sortino, Calmar, duration, Tracking Error or Information Ratio field is added there

### Requirement: Backtest Detail presents proxy CAPM and capture evidence
Backtest Detail SHALL show Monthly Up Capture and Monthly Down Capture with selected-month counts inside both named benchmark groups. It SHALL show annualized Alpha, Beta, R-squared, and daily CAPM observation count only in the CSI 300 group, label Alpha as `CSI 300 ETF proxy Alpha (252D compounded)` or semantically equivalent text, label capture as a non-annualized monthly geometric ratio, and never present equal-weight results as CAPM.

#### Scenario: New detail distinguishes benchmark meanings
- **WHEN** a benchmark-enabled detail response contains calculable benchmark-regime metrics
- **THEN** both benchmark groups display their own monthly capture ratios and selected-month counts
- **AND** only the CSI 300 group displays proxy-qualified CAPM fields

#### Scenario: Null evidence is not fabricated
- **WHEN** a new field is null for a legacy or mathematically undefined result
- **THEN** the UI renders the established unavailable placeholder and available observation count
- **AND** does not display zero, NaN, Infinity, or a synthetic ratio

### Requirement: Walk-forward Detail presents regime aggregates as evidence
Walk-forward Detail SHALL display per-window and aggregate proxy Alpha/Beta/R-squared and named-benchmark monthly capture evidence with explicit daily-session versus selected-month count units, metric-local valid counts, and `insufficient_evidence`. It SHALL preserve existing evidence, navigation, and terminal states and SHALL NOT add a score, threshold, ranking, or pass/fail result.

#### Scenario: Evidence statuses remain metric-local
- **WHEN** a Walk-forward response contains different valid counts across regime metrics
- **THEN** each displayed aggregate uses its own count and status
- **AND** existing OOS, benchmark, generalization, parameter, and navigation evidence remains available

### Requirement: Expanded metric groups remain accessible and responsive
The added Backtest and Walk-forward content SHALL use semantic headings/labels, expose benchmark identity and observation counts to assistive technology, support keyboard access, and avoid page-level horizontal overflow at the project's required 1440x1000 and 390x844 viewports.

#### Scenario: Desktop and narrow layouts preserve meaning
- **WHEN** the expanded detail pages render at both required viewports
- **THEN** proxy and benchmark group ownership remains visually and programmatically clear
- **AND** all existing actions remain reachable without page-level horizontal overflow

### Requirement: Backtest Detail provides selectable rolling diagnostics
Backtest Detail SHALL present a Stability section with an explicit 63-session window label and a selector for Rolling Return, Rolling Volatility, and Rolling Sharpe. The selected view SHALL compare strategy and available fixed benchmarks using API-provided values, identify window dates and entity names accessibly, and provide a semantic tabular/text alternative. It MUST NOT calculate values in the browser or mix differently scaled metrics on one axis.

#### Scenario: User switches rolling metric without recomputation
- **WHEN** a user selects Return, Volatility, or Sharpe
- **THEN** the chart and accessible value representation use the corresponding API series unchanged
- **AND** retain distinguishable strategy and benchmark identities

#### Scenario: Short or legacy run explains unavailability
- **WHEN** rolling status is insufficient or Sharpe status lacks risk-free-rate evidence
- **THEN** the UI explains the specific unavailable scope
- **AND** continues to show every available stability metric and existing Backtest Detail content

### Requirement: Backtest Detail presents monthly and yearly returns
The Stability section SHALL provide monthly and yearly views with an entity selector for strategy and available fixed benchmarks. Every visible and accessible period value SHALL expose its period, compounded return, observation count, and requested-scope partial marker using the exact API result. The UI MUST NOT describe that marker as proof of complete official-session evidence.

#### Scenario: Requested-scope partial periods remain visible and distinguishable
- **WHEN** calendar return data includes partial boundary buckets
- **THEN** those buckets remain visible with a clear requested-period partial label
- **AND** are not silently dropped or presented as complete periods

### Requirement: Stability presentation is responsive and accessible
Rolling controls, charts, tables/heatmaps, entity selection, empty/error states, and existing Backtest Detail tabs/actions SHALL be keyboard accessible and programmatically labeled. The page SHALL avoid page-level horizontal overflow and retain readable hierarchy at 1440x1000 and 390x844.

#### Scenario: Required viewports preserve analysis and navigation
- **WHEN** stability content renders at either required viewport
- **THEN** users can reach selectors, inspect exact values and partial states, and use existing Backtest Detail actions
- **AND** the page has no page-level horizontal overflow

### Requirement: Walk-forward parent does not present stitched stability
Walk-forward Detail SHALL NOT show rolling or calendar-period metrics derived from `stitched_oos`. Existing links to selected OOS Backtest Detail pages SHALL remain the path for inspecting each independent window's stability series.

#### Scenario: Available stitched curve retains reset-only semantics
- **WHEN** Walk-forward Detail renders an available stitched OOS curve
- **THEN** it shows no stitched Rolling Sharpe, Volatility, Return, monthly return, or yearly return
- **AND** linked OOS Backtest Detail pages remain navigable

### Requirement: Backtest Detail presents historical distribution risk explicitly
Backtest Detail SHALL present strategy and each fixed benchmark's `Historical VaR 95% (1D loss)`, `Historical CVaR 95% (1D loss)`, `Skewness`, and `Excess kurtosis (normal = 0)` with effective/tail observation counts and evidence status. It SHALL use exact API values, show positive losses as loss magnitudes, distinguish insufficient/legacy/undefined nulls, and make no forecast or regulatory-capital claim. When evidence is insufficient, it SHALL explain that a displayed tail count is the cardinality implied by the fixed 5% rank rule while publication of the metrics still requires at least 100 effective observations.

#### Scenario: Sufficient evidence displays exact semantics
- **WHEN** a detail response contains sufficient calculable distribution metrics
- **THEN** each owning group displays exact API values, counts, confidence, horizon, historical method, and excess-kurtosis baseline

#### Scenario: Null reason remains visible
- **WHEN** metrics are null because evidence is insufficient, history is legacy, or distribution shape is constant
- **THEN** the UI presents the corresponding unavailable explanation and available counts
- **AND** does not display zero, NaN, Infinity, a threshold verdict, or a fabricated metric

#### Scenario: Insufficient tail count does not imply a published metric
- **WHEN** a detail response contains 99 effective observations, a tail count of 5, and null distribution metrics
- **THEN** the UI identifies the five observations as the fixed-rank tail cardinality
- **AND** explains that the metrics remain unavailable because the 100-observation publication requirement is not met

### Requirement: Walk-forward Detail presents distribution evidence without scoring
Walk-forward Detail SHALL display per-window and aggregate strategy/fixed-benchmark distribution evidence from v3 with metric-local valid counts and statuses, preserve all existing v2 and stitched-OOS content, and SHALL NOT add scoring, ranking, alerts, or pass/fail conclusions. It SHALL label aggregate values as descriptive statistics across independent per-window metric estimates and MUST NOT present them as VaR/CVaR or shape statistics of a combined or stitched strategy return distribution.

#### Scenario: Mixed evidence remains owner and metric specific
- **WHEN** v3 contains different valid counts across owners and metrics
- **THEN** each displayed aggregate retains its own owner, count, nulls, and status
- **AND** existing benchmark-regime, OOS, generalization, parameter, stitched, and navigation evidence remains available

#### Scenario: Aggregate explanation rejects a combined-distribution interpretation
- **WHEN** Walk-forward Detail displays aggregate VaR, CVaR, Skewness, or Excess Kurtosis evidence
- **THEN** the aggregate section explains that it summarizes independent window estimates
- **AND** does not claim to measure the tail or shape of one combined strategy return distribution

### Requirement: Expanded risk groups remain accessible and responsive
The added Backtest and Walk-forward risk content SHALL use semantic headings/labels, expose counts/statuses to assistive technology, retain keyboard access and existing actions, and avoid page-level horizontal overflow at 1440x1000 and 390x844.

#### Scenario: Required viewports preserve risk meaning
- **WHEN** the expanded pages render at either required viewport
- **THEN** strategy/benchmark ownership, historical loss semantics, counts, and null states remain readable and programmatically clear
- **AND** no existing action becomes unreachable or causes page-level horizontal overflow

### Requirement: Walk-forward list page provides run trigger
The Walk-forward list page SHALL expose a "Run walk-forward" action that calls the shared frontend API client's `runWalkForward()` function against `POST /api/walk-forwards/run`, disables itself while an active queued/running record exists, and polls `GET /api/walk-forwards/{run_id}` on a bounded interval to observe durable lifecycle status. The action SHALL be placed on the Walk-forward list page (not the Dashboard) because Walk-forward is a low-frequency research tool outside the daily signal-generation flow. On `status = "queued"` it SHALL show a queued indicator and continue polling; on `status = "running"` it SHALL show a running indicator and continue polling; on `status = "success"` it SHALL navigate to `/walk-forwards/{run_id}` through client-side navigation; on `status = "failed"` it SHALL surface the API-provided bounded `error_message` and re-enable the action. The page SHALL discover an active record from refreshed history after reload, stop polling when the document is hidden and resume when visible. The action SHALL NOT block on run completion synchronously, accept a client-supplied configuration path, create a duplicate request while active work exists, or retry a failed record itself. The run-trigger button SHALL carry a valid `design-system` button variant class (`button-secondary`) and SHALL NOT rely on any style class that is undefined in `styles.css`.

#### Scenario: User triggers a run from the list page
- **WHEN** the user clicks "Run walk-forward" on the Walk-forward list page and no active record exists
- **THEN** the frontend calls `runWalkForward()` against `POST /api/walk-forwards/run`
- **AND** the action enters a disabled in-progress state while the request is pending
- **AND** the action prevents duplicate submissions while the request is pending

#### Scenario: Run trigger button uses a defined variant
- **WHEN** the Walk-forward list page renders the "Run walk-forward" button
- **THEN** the button's className includes `button-secondary`
- **AND** every style class on the button resolves to a rule defined in `apps/web/src/styles.css`
- **AND** the run-trigger container applies the standard list-page spacing below the button (`margin-bottom: var(--spacing-16)`)

#### Scenario: Accepted run shows queued then navigates on success
- **WHEN** the run-trigger request returns HTTP 202 with a `walk_forward_run_id` and `status = "queued"`
- **THEN** the action stays disabled and shows a queued indicator
- **AND** the frontend polls `GET /api/walk-forwards/{run_id}` on a bounded interval through queued and running states
- **AND** when the polled `status` becomes `success`, the page navigates to `/walk-forwards/{run_id}` through client-side navigation

#### Scenario: Reload preserves active-job state
- **WHEN** the list page reloads while the API history contains a queued or running record
- **THEN** the page identifies that record as active, disables the action, and resumes polling its detail
- **AND** it does not issue another POST submission

#### Scenario: Failed run surfaces error and re-enables action
- **WHEN** a polled `status` becomes `failed`
- **THEN** the page stops polling
- **AND** the page surfaces the API-provided `error_message`
- **AND** the "Run walk-forward" action is re-enabled

#### Scenario: Polling pauses when document is hidden
- **WHEN** the document becomes hidden while a record is queued or running
- **THEN** the frontend stops issuing poll requests
- **AND** when the document becomes visible again, polling resumes from the current `status`

#### Scenario: Concurrent-run conflict is surfaced without starting a second run
- **WHEN** the run-trigger request returns HTTP 409 indicating an active queued or running record
- **THEN** the page surfaces the conflict error
- **AND** the frontend does not issue a second `POST /api/walk-forwards/run`
- **AND** the action refreshes history before allowing another submission

#### Scenario: Expected domain error is surfaced without leaving an active record
- **WHEN** the run-trigger request returns HTTP 400 with category `operation_failed` during enqueue preflight
- **THEN** the page surfaces the API-provided error message
- **AND** no `WalkForwardRun` row with `status = "queued"` or `status = "running"` is left visible in the list
- **AND** the "Run walk-forward" action is re-enabled

#### Scenario: Accepted run polls and navigates on success
- **WHEN** the run-trigger request returns HTTP 202 with a `walk_forward_run_id`
- **THEN** the action stays disabled and shows a running indicator
- **AND** the frontend polls `GET /api/walk-forwards/{run_id}` on a bounded interval
- **AND** when the polled `status` becomes `success`, the page navigates to `/walk-forwards/{run_id}` through client-side navigation

#### Scenario: Expected domain error is surfaced without leaving a running record
- **WHEN** the run-trigger request returns HTTP 400 with category `operation_failed` (for example missing market data)
- **THEN** the page surfaces the API-provided error message
- **AND** no `WalkForwardRun` row with `status = "queued"` or `status = "running"` is left visible in the list
- **AND** the "Run walk-forward" action is re-enabled

### Requirement: Dashboard market data fetch supports full mode
The web frontend SHALL expose an independent full market-data fetch entry point in the Dashboard Operations action list, wired to the existing `handleMarketDataFetch("full")` handler path and the existing `fetchFullMarketData` client function, which issues `POST /api/market-data/fetch?mode=full`. The pre-existing incremental fetch entry point SHALL remain unchanged and SHALL continue to issue `POST /api/market-data/fetch?mode=incremental`. Both entry points SHALL share the existing `activeOperation` lock (key `"marketDataFetch"`), the existing `marketDataFetchMode` state, and the existing `MarketDataFetchSummary` and `OperationErrorSummary` result and error surfaces. The change SHALL introduce no new component, no new API client function, no new API type, and no new application state.

#### Scenario: Full fetch button triggers the full mode request
- **WHEN** the Dashboard has loaded and the user clicks the "Fetch full" action in the Operations action list
- **THEN** the frontend issues `POST /api/market-data/fetch?mode=full` through the shared API client
- **AND** no `POST /api/market-data/fetch?mode=incremental` request is issued as a side effect of that click

#### Scenario: Incremental fetch button preserves the incremental request
- **WHEN** the user clicks the pre-existing "Fetch market data" action in the Operations action list
- **THEN** the frontend issues `POST /api/market-data/fetch?mode=incremental` through the shared API client
- **AND** the request URL does not contain `mode=full`

#### Scenario: Active operation lock disables the sibling fetch action
- **WHEN** a market-data fetch of either mode is in flight (the `activeOperation` lock is held as `"marketDataFetch"`)
- **THEN** both the incremental and the full fetch buttons are disabled
- **AND** clicking the disabled sibling does not issue a second fetch request

#### Scenario: Each fetch button shows its own in-progress label
- **WHEN** the incremental fetch is in flight
- **THEN** the incremental fetch button displays its in-progress label and the full fetch button displays its idle label
- **WHEN** the full fetch is in flight
- **THEN** the full fetch button displays its in-progress label and the incremental fetch button displays its idle label

#### Scenario: Full fetch result renders through the shared summary
- **WHEN** a `POST /api/market-data/fetch?mode=full` request returns a successful `MarketDataFetchResponse`
- **THEN** the Dashboard renders the `MarketDataFetchSummary` component populated with that response
- **AND** the rendered summary is the same component used for the incremental fetch result
- **WHEN** the request fails with an `ApiClientError`
- **THEN** the Dashboard renders the `OperationErrorSummary` component for the `"marketDataFetch"` operation

#### Scenario: Full fetch refreshes aggregate dashboard data
- **WHEN** a full fetch request returns a response with `status = "success"`
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed market data status reflects the updated price row count and coverage

