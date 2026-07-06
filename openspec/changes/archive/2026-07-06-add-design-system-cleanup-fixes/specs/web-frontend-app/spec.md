## ADDED Requirements

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
