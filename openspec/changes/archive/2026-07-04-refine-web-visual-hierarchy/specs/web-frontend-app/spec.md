## ADDED Requirements

### Requirement: Dashboard focused first-screen hierarchy
The web frontend SHALL present the Dashboard first screen so local workflow status, key research metrics, and primary operations are discoverable before secondary historical details.

#### Scenario: Dashboard prioritizes key workflow areas
- **WHEN** the Dashboard route renders a successful dashboard aggregate response
- **THEN** the first screen presents the Dashboard load state, market data status, latest signal or signal empty state, and Operations entry point before dense secondary history dominates the page
- **AND** the Dashboard remains a local research workflow surface without marketing hero content, decorative artwork, login, account, hosting, deployment, or production language

#### Scenario: Operations remains discoverable with populated data
- **WHEN** the Dashboard route renders populated market data, strategy, latest signal, recent backtest, and recent fetch log data
- **THEN** the Operations section remains visible near the main workflow summary or reachable without passing through an unbounded history region
- **AND** the market data fetch, full fetch, generate signal, and run backtest controls keep their existing labels and behavior

#### Scenario: Empty workflow states point to matching actions
- **WHEN** the Dashboard route renders missing market data, missing latest signal, or missing recent backtest states
- **THEN** each empty state identifies the matching local Dashboard action or Operations control needed next
- **AND** the matching action remains available from the Dashboard without introducing new routes or remote setup assumptions

### Requirement: Dashboard long-content layout resilience
The web frontend SHALL prevent secondary Dashboard content from stretching unrelated cards or pushing primary workflow actions deep below the first screen.

#### Scenario: Recent fetch history does not stretch sibling cards
- **WHEN** the Dashboard receives multiple recent fetch log summaries or long fetch error text
- **THEN** the Recent fetches area is visually bounded or internally scrollable
- **AND** sibling Dashboard panels in the same layout region do not expand to match the full history height
- **AND** Operations remains positioned as a primary workflow area rather than after an unbounded history block

#### Scenario: Dashboard cards preserve readable density
- **WHEN** Dashboard panel content contains long paths, timestamps, failed symbols, or error summaries
- **THEN** the content wraps, clips, scrolls, or is otherwise contained within the relevant panel without causing horizontal page overflow
- **AND** the implementation does not hide the panel heading or primary value labels needed to understand the content

#### Scenario: Responsive layouts preserve the focused order
- **WHEN** the Dashboard is viewed at desktop, tablet, and mobile widths
- **THEN** status, key metrics, and Operations remain ordered ahead of secondary dense history
- **AND** the layout preserves the existing single-column mobile behavior below `720px`

### Requirement: Minimal visual emphasis system
The web frontend SHALL use a restrained emphasis system where only primary workflow actions and abnormal states receive strong visual weight.

#### Scenario: Primary and secondary dashboard content have distinct weight
- **WHEN** the Dashboard renders populated workflow data
- **THEN** market data status, latest signal state, and Operations controls have stronger visual priority than strategy details and recent fetch history
- **AND** the distinction is achieved with existing typography, spacing, surface, border, and accent tokens rather than new colors or broad chromatic blocks

#### Scenario: Detail pages keep consistent data-card treatment
- **WHEN** Signal Detail or Backtest Detail renders loading, empty, error, or populated states
- **THEN** page surfaces, cards, tables, and feedback states remain visually consistent with the Dashboard token system
- **AND** the pages do not introduce a competing visual palette, new dependency, or unrelated component pattern

#### Scenario: API metadata is visually secondary
- **WHEN** the App Shell renders the API base URL metadata
- **THEN** the metadata remains available but does not compete with the page title, key workflow status, or primary actions for visual attention
