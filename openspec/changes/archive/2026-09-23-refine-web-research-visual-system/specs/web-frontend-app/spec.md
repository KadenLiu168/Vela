## MODIFIED Requirements

### Requirement: AppShell brand remains subordinate to page research content
The visible `Vela Research` brand MUST remain non-heading text and MUST use the Sans family at approximately 22px, 28px line height, 620 weight, and `-0.035em` tracking. The route's page title MUST remain the primary visual heading.

#### Scenario: Brand and page title preserve hierarchy
- **WHEN** any AppShell route renders
- **THEN** the brand MUST remain smaller than the shared page title (36px above 720px, 28px at or below 720px)
- **AND** the page title MUST remain the document's only page-identity heading

## ADDED Requirements

### Requirement: Research hierarchy preserves evidence and workflow order
The visual refinement MUST retain all five Dashboard decision layers in their existing DOM and visual order, followed by reference and operations. Backtest Overview MUST retain run summary, Decision Summary, Equity Curve, Benchmark Comparison, Deep Analysis and Experiment Config order, including existing disclosure defaults and Signals-tab behavior. Other detail and list pages MUST retain content, field order, route labels, actions and data semantics while applying shared visual roles. Supplemental API connection metadata MUST remain available and visually subordinate to research identity.

#### Scenario: Presentation changes do not drop evidence
- **WHEN** a populated or legacy research fixture renders before and after the refinement
- **THEN** all existing values, source labels, unavailable reasons, units, signs, action targets and evidence links MUST remain available in their owning regions
- **AND** no new score, verdict, operation or business calculation MUST be introduced

### Requirement: Narrow research pages preserve content and interaction
All application routes MUST remain readable and usable at 320, 390, 768, 1024 and 1440 CSS px widths and at the existing breakpoint boundaries. Page-level horizontal overflow MUST be absent. Wide data tables MUST scroll inside labeled keyboard-accessible local regions without hiding essential columns; numeric cells MUST align right and names left. Long language content MUST wrap. Chart ticks and legends MUST reflow without shrinking essential text or changing data geometry calculations. Multiple plotted series MUST have stable text labels and distinguishable line styles as well as colors; exact-value text/table alternatives MUST remain accessible. The palette MUST retain reachable input and results at reduced viewport height.

#### Scenario: Wide evidence on a narrow screen
- **WHEN** a populated comparison table or long mixed Chinese/Latin fixture renders at 320px
- **THEN** users MUST access every value and action through the page or its local scroll region without page-level horizontal scrolling
- **AND** signs, units, meaningful precision and source warnings MUST NOT be clipped or omitted

#### Scenario: Palette under reduced viewport height
- **WHEN** a user searches at a reduced viewport height (390x400)
- **THEN** the input and active result MUST remain reachable within the visible viewport and the result region MUST scroll internally

### Requirement: Accessible research interactions satisfy the AA target
The refined routes and shared components MUST meet applicable WCAG 2.2 A/AA criteria. Normal text MUST reach 4.5:1 contrast, large text 3:1, and required non-text control information 3:1. Keyboard focus MUST be visible and unobscured; modal focus MUST enter, remain within, and return to its opener on dismissal. Forms MUST retain associated labels/errors and asynchronous outcomes MUST be announced without repeated interruption. Content MUST support 200% text resizing and reflow at 320 CSS px. Pointer targets MUST meet 24px minimum size or the standard's spacing/other exceptions; standalone touch buttons and inputs MUST meet the stronger product target of 44px in both dimensions.

#### Scenario: Keyboard completes research navigation
- **WHEN** a user uses only the keyboard through navigation, filters, disclosures and palette
- **THEN** the user MUST reach and activate all controls, perceive focus and selection, close the modal, and resume at its opener without a keyboard trap

#### Scenario: Text enlargement preserves evidence
- **WHEN** text is enlarged to 200% or content reflows to 320 CSS px
- **THEN** text, status information and controls MUST remain available without overlap, truncation or loss of operation

### Requirement: Visual acceptance is reproducible and isolated from persistent data
Acceptance MUST provide a repository-owned executable browser workflow with deterministic API fixtures and checks linked to route, state, viewport and requirement. Unhandled API methods/paths MUST fail the run instead of reaching a real service. Evidence MUST record source revision and dirty-source fingerprint, build and fixture identity, browser version, test results and screenshot paths/hashes. Historical reports or unchecked screenshots MUST NOT count as current acceptance. Manual observations, if any, MUST identify browser/device, steps and outcomes, and MUST be distinguished from automated assertions.

#### Scenario: Unexpected request fails closed
- **WHEN** a tested flow issues an API request without an explicit fixture
- **THEN** the request MUST be blocked and the run MUST fail with the unmatched method/path
- **AND** no default database or real API service MUST be accessed

#### Scenario: Evidence is tied to the reviewed build
- **WHEN** the browser workflow completes
- **THEN** its evidence record MUST identify the tested build and every required result, including failures
- **AND** every passing screenshot reference MUST resolve to an artifact with a recorded hash

