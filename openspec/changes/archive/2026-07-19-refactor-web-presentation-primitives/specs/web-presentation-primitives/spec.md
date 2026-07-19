## ADDED Requirements

### Requirement: Description lists use one canonical item primitive

The web frontend MUST provide one shared `DescriptionItem` component that renders a sibling `<dt>/<dd>` pair without adding a layout wrapper. Its value contract MUST accept React content, and Dashboard, ETF Detail, Signal Detail, and Backtest Detail MUST use it for description-list items instead of defining page-local equivalents.

#### Scenario: Text values retain canonical description semantics

- **WHEN** any of the four affected pages renders a text-valued description item
- **THEN** the label is rendered as `<dt>` and the value is rendered as its sibling `<dd>`
- **AND** no extra wrapper changes the existing description-list layout

#### Scenario: Linked values use the same primitive

- **WHEN** Signal Detail renders the Backtest link for a backtest-sourced signal
- **THEN** the link is rendered inside the `DescriptionItem` value `<dd>`
- **AND** the page does not hand-write a separate `<dt>/<dd>` pair for that value

### Requirement: Formatter modules preserve generic and domain boundaries

The web frontend MUST keep domain-independent scalar formatting in `utils/formatters.ts` and MUST place extracted Dashboard-specific and Backtest-specific presentation formatting in co-located pure modules. Extracted formatter modules MUST NOT import React or access DOM APIs, and their meaningful nullable, invalid, and structured-input branches MUST have direct unit tests.

#### Scenario: Dashboard domain formatting is directly testable

- **WHEN** momentum windows, score weights, defensive assets, or failed symbols are formatted for Dashboard presentation
- **THEN** the output is produced by a Dashboard-domain pure formatter module
- **AND** direct tests verify the existing output and empty-list fallback behavior

#### Scenario: Backtest structured values are directly testable

- **WHEN** Backtest parameters or an equity-curve point are converted to display text
- **THEN** the output is produced by a Backtest-domain pure formatter module
- **AND** direct tests cover valid JSON, malformed JSON, nullable JSON, and the composite date/net-value readout

#### Scenario: Page modules retain component-only exports

- **WHEN** presentation formatters are extracted for direct testing
- **THEN** they are exported from pure formatter modules rather than from React page modules
- **AND** each affected page module continues to export only React components

### Requirement: Each chart owns framework-independent geometry

ETF Trend and Equity Curve MUST each keep dimensions and pure geometry logic in a dedicated non-React module. Equity Curve MUST use one exported chart-dimensions constant as the source of truth for coordinate calculations, SVG viewBox dimensions, and grid-line bounds.

#### Scenario: Equity Curve dimensions stay synchronized

- **WHEN** the Equity Curve renderer creates its SVG frame and calculates point coordinates
- **THEN** both operations derive width, height, and plot bounds from `EQUITY_CURVE_CHART`
- **AND** the renderer does not repeat independent numeric literals for the same geometry

#### Scenario: Geometry modules remain framework-independent

- **WHEN** ETF Trend or Equity Curve geometry is imported by a unit test
- **THEN** its calculations run without rendering React components
- **AND** the module does not require DOM layout APIs

#### Scenario: A generic chart framework is not introduced

- **WHEN** the two chart modules are reorganized by this change
- **THEN** ETF Trend retains its hover and axis-specific geometry contract
- **AND** Equity Curve retains its extrema-highlight geometry contract
- **AND** no generic multi-chart component or generic geometry framework is required

### Requirement: Pure geometry has focused boundary coverage

The frontend test suite MUST directly test ETF Trend and Equity Curve pure geometry separately from page integration behavior. It MUST retain page-level coverage for empty, single-point, and multi-point rendering and for ETF hover behavior.

#### Scenario: ETF geometry boundaries are verified directly

- **WHEN** ETF Trend geometry tests run
- **THEN** they verify nearest-index clamping, date-axis index selection, normal value ranges, all-equal values, and line-path plot bounds

#### Scenario: Equity geometry boundaries are verified directly

- **WHEN** Equity Curve geometry tests run
- **THEN** they verify invalid-point filtering, multi-point coordinates and paths, all-equal values, extrema highlight selection, duplicate suppression, and tie behavior

#### Scenario: Refactoring preserves rendered behavior

- **WHEN** the page integration suite runs after the extraction
- **THEN** Dashboard, ETF Detail, Signal Detail, and Backtest Detail retain their existing rendered copy and states
- **AND** ETF Trend retains its hover readout behavior
- **AND** Equity Curve retains its empty, single-point, and multi-point behavior
