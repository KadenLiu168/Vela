# web-route-code-splitting Specification

## Purpose
Defines on-demand route module loading, persistent shell behavior, accessible loading and failure states, cache-oriented vendor chunking, and bundle measurement requirements for the web frontend.

## Requirements

### Requirement: Non-default route modules load on demand
The web frontend SHALL keep the Signal list, Signal detail, Backtest list, Backtest detail, and ETF detail page modules outside the Dashboard route's initial static JavaScript dependency graph and SHALL load each page module when its matching route is rendered.

#### Scenario: Dashboard does not preload non-default pages
- **WHEN** a production build is opened on `/` with an empty browser cache
- **THEN** the initial static JavaScript graph MUST NOT include the page modules for `/signals`, `/signals/:id`, `/backtests`, `/backtests/:id`, or `/etfs/:id`
- **AND** the built HTML MUST NOT module-preload those asynchronous page chunks

#### Scenario: Direct route visit loads the matching module
- **WHEN** a user directly opens one of `/signals`, `/signals/{id}`, `/backtests`, `/backtests/{id}`, or `/etfs/{id}`
- **THEN** the frontend MUST load the page module required by that route
- **AND** the route MUST preserve its existing API request, loading, success, empty, and error behavior

#### Scenario: Client navigation reuses a loaded route module
- **WHEN** a user navigates to a non-default route whose page module was loaded earlier in the same application session
- **THEN** the frontend MUST reuse the cached module
- **AND** it MUST NOT request a duplicate copy of the same content-hashed chunk

### Requirement: Dashboard and application shell remain eager
The web frontend SHALL keep React startup, AppShell, shared navigation state, the shared API client, DashboardPage, and CommandPalette in the initial static JavaScript graph.

#### Scenario: Default route renders without a route-module request
- **WHEN** a user opens `/`
- **THEN** AppShell and DashboardPage MUST render from the initial static JavaScript graph
- **AND** rendering DashboardPage MUST NOT wait for a dynamic page-module import

#### Scenario: Command palette remains immediately available
- **WHEN** the user invokes the CommandPalette shortcut after the application is interactive
- **THEN** the frontend MUST open CommandPalette without first fetching a CommandPalette JavaScript chunk

### Requirement: Route loading preserves the shell and exposes accessible status
The web frontend SHALL render route-module loading feedback inside the persistent AppShell main-content area while an asynchronous page module is pending.

#### Scenario: Lazy route is pending
- **WHEN** navigation selects a non-default route and its page module has not finished loading
- **THEN** the AppShell header and navigation MUST remain rendered and usable
- **AND** the main-content area MUST expose a status named `Loading page`
- **AND** the main-content area MUST render a layout-stable Skeleton fallback that is hidden from assistive technologies

#### Scenario: Lazy route finishes loading
- **WHEN** the requested page module resolves
- **THEN** the loading status and Skeleton fallback MUST be removed
- **AND** the requested page MUST retain its existing single page-level `<h1>` contract

### Requirement: Route-module failures are recoverable
The web frontend SHALL handle a rejected route-module import within a route-scoped error boundary without removing AppShell navigation.

#### Scenario: Route chunk fails to load
- **WHEN** a non-default route-module import rejects because its chunk cannot be fetched or evaluated
- **THEN** the main-content area MUST render an explicit page-loading failure message
- **AND** the failure state MUST provide a reload action
- **AND** AppShell navigation MUST remain available

#### Scenario: Navigation resets a route failure
- **WHEN** a route-module failure is displayed and the user navigates to a different route
- **THEN** the route-scoped error boundary MUST reset
- **AND** the newly selected route MUST be allowed to render

### Requirement: React vendor chunk is a cache boundary
The production build SHALL emit React, ReactDOM, and Scheduler runtime code in a targeted `react-vendor` chunk that is a static dependency of the application entry.

#### Scenario: Production build emits targeted vendor chunk
- **WHEN** the production frontend is built
- **THEN** the build output MUST contain a content-hashed `react-vendor` JavaScript chunk
- **AND** that chunk MUST contain React, ReactDOM, and Scheduler runtime modules
- **AND** unrelated future `node_modules` dependencies MUST NOT be assigned to that chunk by a catch-all vendor rule

#### Scenario: Cold-cache accounting includes vendor
- **WHEN** initial JavaScript transfer size is reported
- **THEN** the report MUST include the application entry and every recursively imported static chunk, including `react-vendor`
- **AND** it MUST NOT describe the application entry file alone as the total initial JavaScript payload

### Requirement: Production bundle structure and budgets are verifiable
The web frontend SHALL provide a repeatable production-build check that derives static and dynamic chunk relationships from the Vite manifest and reports raw and gzip JavaScript sizes.

#### Scenario: Dashboard initial graph stays within budget
- **WHEN** the production bundle check evaluates the Dashboard initial static JavaScript graph
- **THEN** the summed raw JavaScript size MUST be no greater than 232,000 bytes
- **AND** the summed gzip JavaScript size MUST be no greater than 72,000 bytes

#### Scenario: Total JavaScript avoids material growth
- **WHEN** the production bundle check evaluates every emitted JavaScript chunk
- **THEN** the summed raw JavaScript size MUST be no greater than 259,541 bytes
- **AND** the report MUST list each asynchronous route entry separately from the initial static graph

#### Scenario: Font and JavaScript results remain separate
- **WHEN** performance results for this change are recorded
- **THEN** JavaScript graph sizes MUST be reported independently from font transfer sizes
- **AND** font-subsetting savings MUST NOT be attributed to route code splitting
