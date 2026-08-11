## MODIFIED Requirements

### Requirement: Non-default route modules load on demand
The web frontend SHALL keep the Signal list, Signal detail, Backtest list, Backtest detail, ETF detail, Walk-forward list, and Walk-forward detail page modules outside the Dashboard route's initial static JavaScript dependency graph and SHALL load each page module when its matching route is rendered.

#### Scenario: Dashboard does not preload non-default pages
- **WHEN** a production build is opened on `/` with an empty browser cache
- **THEN** the initial static JavaScript graph MUST NOT include the page modules for `/signals`, `/signals/:id`, `/backtests`, `/backtests/:id`, `/etfs/:id`, `/walk-forwards`, or `/walk-forwards/:id`
- **AND** the built HTML MUST NOT module-preload those asynchronous page chunks

#### Scenario: Direct route visit loads the matching module
- **WHEN** a user directly opens one of `/signals`, `/signals/{id}`, `/backtests`, `/backtests/{id}`, `/etfs/{id}`, `/walk-forwards`, or `/walk-forwards/{id}`
- **THEN** the frontend MUST load the page module required by that route
- **AND** the route MUST preserve its existing API request, loading, success, empty, and error behavior

#### Scenario: Client navigation reuses a loaded route module
- **WHEN** a user navigates to a non-default route whose page module was loaded earlier in the same application session
- **THEN** the frontend MUST reuse the cached module
- **AND** it MUST NOT request a duplicate copy of the same content-hashed chunk

### Requirement: Production bundle structure and budget bands are verifiable
The web frontend SHALL provide a repeatable production-build check that derives static
and dynamic chunk relationships from a fresh Vite manifest, reports raw and gzip
JavaScript sizes, attributes required runtime separately from eager application code and
non-initial lazy-route JavaScript, evaluates every configured budget band in one run, and
returns a non-zero result when any identity, budget, or graph-ownership requirement fails.

#### Scenario: Bundle evidence comes from the reviewed dependency and source state
- **WHEN** production bundle acceptance is recorded
- **THEN** dependencies MUST be installed from the reviewed npm lockfile before a fresh production build
- **AND** the evidence MUST identify the Node, npm, Vite, and lockfile state that produced the manifest
- **AND** an older `dist/` tree MUST NOT be accepted as evidence for changed source, dependencies, or build tooling

#### Scenario: Reviewed build identity is pinned to the evidence
- **WHEN** production bundle acceptance is recorded
- **THEN** the report MUST identify the Node, npm, Vite, and npm lockfile identity that produced the manifest
- **AND** the identity MUST match the reviewed build identity for this Change
- **AND** a dependency or toolchain identity change MUST be reported as a baseline violation rather than silently accepted

#### Scenario: Required runtime and eager application bands are reported separately
- **WHEN** the production bundle check evaluates the Dashboard initial static JavaScript graph
- **THEN** it MUST report the isolated required React 19 + React Router runtime baseline separately from eager application code
- **AND** the required runtime baseline MUST be `229,187` raw bytes and `73,544` gzip bytes for the reviewed identity
- **AND** eager application code MUST be no greater than `40,000` raw bytes and `12,000` gzip bytes

#### Scenario: Dashboard initial graph stays within the revised budget
- **WHEN** the production bundle check evaluates the Dashboard initial static JavaScript graph
- **THEN** the summed raw JavaScript size MUST be no greater than 273,000 bytes
- **AND** the summed gzip JavaScript size MUST be no greater than 86,000 bytes

#### Scenario: Lazy route graph stays within the revised allocation
- **WHEN** the production bundle check evaluates all emitted JavaScript that is not in the Dashboard initial static graph
- **THEN** the summed raw JavaScript size MUST be no greater than 61,000 bytes
- **AND** the report MUST include asynchronous shared helper chunks in this allocation

#### Scenario: Total JavaScript avoids material growth
- **WHEN** the production bundle check evaluates every emitted JavaScript chunk
- **THEN** the summed raw JavaScript size MUST be no greater than 333,000 bytes
- **AND** the report MUST list each asynchronous route entry separately from the initial static graph

#### Scenario: Every declared lazy route is verified
- **WHEN** the production bundle check evaluates the Vite manifest and built Dashboard HTML
- **THEN** it MUST locate separate dynamic entries for Signal list/detail, Backtest list/detail, ETF detail, Walk-forward list/detail
- **AND** none of those route entries may belong to the Dashboard initial static graph or appear in Dashboard module-preload markup

#### Scenario: One run reports every bundle violation
- **WHEN** identity, required-runtime, eager-application, lazy-route, initial, total JavaScript, or lazy-route ownership exceeds its contract
- **THEN** the checker MUST report every violated condition from that build rather than stopping after the first failure
- **AND** the checker MUST exit non-zero without changing, bypassing, or silently rebaselining the configured thresholds

#### Scenario: Font and JavaScript results remain separate
- **WHEN** performance results for this change are recorded
- **THEN** JavaScript graph sizes MUST be reported independently from font transfer sizes
- **AND** font-subsetting savings MUST NOT be attributed to route code splitting
