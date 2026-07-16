## MODIFIED Requirements

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
