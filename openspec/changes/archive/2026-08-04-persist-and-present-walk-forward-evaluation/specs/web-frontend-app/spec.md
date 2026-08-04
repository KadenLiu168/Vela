## ADDED Requirements

### Requirement: Walk-forward history page lists persisted evaluations
The Web application SHALL add a lazy-loaded `/walk-forwards` page and primary navigation entry. It SHALL request the current-strategy API with fixed page size 10 and render persisted evaluations with run id, finished time, strategy, configured interval, window count, provenance/evidence versions and compact configuration/input checksum identifiers. It SHALL use the exact API total for boundaries and provide loading, error and empty states.

#### Scenario: History rows navigate to detail
- **WHEN** persisted evaluations are returned
- **THEN** each row displays its identifying metadata and compact provenance
- **AND** opens `/walk-forwards/{id}` through client-side navigation

#### Scenario: Pagination uses exact total
- **WHEN** the final page contains fewer than ten runs or total is an exact multiple of ten
- **THEN** Next is disabled at the exact boundary
- **AND** the user cannot navigate to a fabricated empty page

#### Scenario: Empty history explains scope
- **WHEN** the API returns no persisted evaluations
- **THEN** the page explains that only completely successful runs created after history support appear
- **AND** does not infer history from standalone OOS backtests

#### Scenario: History request failure is explicit
- **WHEN** the list request fails
- **THEN** the page renders the existing error-feedback presentation
- **AND** does not render stale rows as current results

### Requirement: Walk-forward detail presents complete structured evidence
The Web application SHALL add a lazy-loaded `/walk-forwards/{id}` page with execution/configuration provenance, evidence sufficiency, OOS summaries, separate dual-benchmark comparisons, IS/OOS gaps, parameter stability and a chronological window table. It SHALL present all `wf_evidence_v1` strategy summaries: total return, CAGR, Sharpe, maximum drawdown, volatility, Sortino, Calmar and longest drawdown duration. Each benchmark section SHALL present return differences, Tracking Error, Information Ratio and outperformance rate. Per-window OOS summaries SHALL preserve strategy/benchmark longest-drawdown peak, trough and nullable recovery dates. Metric values SHALL remain grouped with valid/total counts and evidence status, and the UI SHALL label that status as a minimum-valid-count threshold rather than statistical adequacy or strategy validity.

#### Scenario: Detail preserves evidence semantics
- **WHEN** a successful detail response loads
- **THEN** every strategy and benchmark metric remains grouped with its valid counts and evidence status
- **AND** active/downside metrics retain their benchmark ownership, duration units and completed/ongoing recovery semantics
- **AND** the page does not convert evidence into a composite score, pass or failure

#### Scenario: Provenance distinguishes display paths from identity
- **WHEN** detail contains configuration source paths and checksums
- **THEN** paths are labeled as display metadata
- **AND** `wf_provenance_v1`, configuration checksum, input checksum, manifest bounds/counts and following-session sentinel are visible

#### Scenario: Window table exposes selection audit
- **WHEN** multiple window records load
- **THEN** each chronological row shows train/test bounds, selected parameters, candidate/eligible/skipped counts, fixed skip-reason counts, train Sharpe and OOS id
- **AND** reconciled counts are readable without exposing raw error text

#### Scenario: Detail has no synthetic continuous curve
- **WHEN** multiple adjacent OOS windows are displayed
- **THEN** the page presents them as independent evidence
- **AND** renders no concatenated net-value series or cross-window drawdown, Calmar or duration

#### Scenario: Unknown detail shows not-found state
- **WHEN** the detail API returns 404
- **THEN** the page displays the existing not-found presentation rather than a generic empty report

#### Scenario: Invalid persisted evidence shows error state
- **WHEN** the detail API returns an unexpected-error response for corrupt or unsupported persisted evidence
- **THEN** the page renders its error presentation
- **AND** does not render a partial evidence report

### Requirement: Walk-forward OOS links preserve the complete evidence chain
Every window SHALL link its OOS id to `/backtests/{id}`. A current-strategy OOS run and its signals SHALL remain navigable even when their `config_version` is `wf-*` rather than the currently configured version.

#### Scenario: OOS link opens authoritative cross-version backtest
- **WHEN** the user activates a window's OOS backtest link
- **THEN** client-side navigation opens the existing Backtest Detail for exactly that run id
- **AND** the detail displays its `wf-*` config version instead of a not-found state

#### Scenario: OOS signal chain remains reachable
- **WHEN** the user opens the OOS Backtest Signals tab and activates a linked signal
- **THEN** the paginated signals endpoint succeeds for the `wf-*` run
- **AND** Signal Detail opens for exactly that current-strategy signal regardless of config version

#### Scenario: Other-strategy evidence remains hidden
- **WHEN** a by-id API returns 404 for another strategy's WF, Backtest or Signal id
- **THEN** the corresponding page renders the existing not-found state

### Requirement: Walk-forward pages are responsive and keyboard accessible
History/detail SHALL reuse existing panel, table, Pagination, DescriptionItem, EmptyState and FeedbackMessage primitives plus repository design tokens. Links, navigation and pagination SHALL remain keyboard operable. Dense evidence SHALL remain readable at the supported 1440x1000 desktop and 390x844 narrow viewports without page-level horizontal overflow; a window table MAY use a labeled local horizontal-scroll region when columns cannot reflow accessibly.

#### Scenario: Desktop evidence hierarchy is complete
- **WHEN** detail renders at 1440x1000
- **THEN** execution, provenance, evidence, benchmark and window sections have a clear reading order
- **AND** no required evidence is clipped or hidden

#### Scenario: Narrow viewport contains dense content
- **WHEN** history/detail render at 390x844
- **THEN** the page has no page-level horizontal overflow
- **AND** any locally scrollable table is keyboard reachable and has an accessible label

#### Scenario: Keyboard navigation follows links and pages
- **WHEN** a keyboard user traverses primary navigation, pagination, WF rows and OOS links
- **THEN** every action is focusable, visibly focused and activates the same client-side route as pointer input

### Requirement: Walk-forward presentation does not expand Dashboard
Dashboard SHALL remain unchanged by this Change; WF history and evidence SHALL be available only from the dedicated navigation/list/detail flow.

#### Scenario: Dashboard has no WF summary card
- **WHEN** successful WF history exists
- **THEN** Dashboard does not add a Walk-forward card, score or latest-run summary
