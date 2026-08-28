# walk-forward-results-ui Specification

## Purpose

TBD: Define the user-facing walk-forward detail results and research-order presentation.

## Requirements

### Requirement: Walk-forward detail presents a Run Header with navigation and run identity
The Walk-forward Detail page SHALL render a Run Header as the first content region of its detail body, immediately following the existing page heading, which continues to carry the run title `Walk-forward #<id>` (visible in every state, including loading and not-found). The Run Header SHALL contain a link back to the Walk-forward history list at `/walk-forwards`, the run status, and a single summary line showing Strategy, test date range, and Window count. The full execution metadata (provenance version, evidence version, started/finished/created timestamps, config checksum, input checksum) SHALL NOT occupy the first screen; it SHALL be presented in the provenance region of the page.

#### Scenario: Header precedes all other content
- **WHEN** a Walk-forward detail page loads
- **THEN** the Run Header appears first within the detail body, immediately after the page heading
- **AND** it provides a navigation link back to the Walk-forward history list targeting `/walk-forwards`
- **AND** it shows the run status and a summary line with Strategy, date range, and Window count
- **AND** the page heading above it carries the run title `Walk-forward #<id>`

#### Scenario: Execution metadata is off the first screen
- **WHEN** a Walk-forward detail page renders its first screen
- **THEN** the provenance version, evidence version, timestamps, and checksums are not shown in the first-screen header
- **AND** they remain available in the provenance region of the page

### Requirement: Walk-forward detail presents an OOS Summary headline region
The Walk-forward Detail page SHALL render an OOS Summary region immediately after the Run Header, sourced entirely from persisted cross-window `evidence` aggregation fields. It SHALL present headline cards for: OOS return (median as primary, mean as secondary), OOS median Sharpe, Max drawdown, Positive Window Rate, Benchmark Outperformance Rate against the Primary Benchmark, and Parameter Transition Rate (the maximum per-parameter transition rate with its parameter name and comparison count). All values SHALL be rendered from existing API fields; the page SHALL NOT compute any new financial metric in the browser.

#### Scenario: Headline cards show OOS aggregate evidence
- **WHEN** a successful Walk-forward detail with persisted evidence loads
- **THEN** the OOS Summary shows cards for median/mean return, median Sharpe, max drawdown, positive window rate, benchmark outperformance rate, and parameter transition rate
- **AND** every card value derives from the existing `evidence.metrics`, `evidence.positive_window_rate`, `evidence.benchmarks`, and `evidence.parameter_stability` fields

#### Scenario: Parameter transition card carries comparison context
- **WHEN** the OOS Summary renders the parameter transition card
- **THEN** it shows the maximum per-parameter transition rate with the name of that parameter
- **AND** it displays the comparison count so a low-comparison base cannot be misread as an unstable parameter

#### Scenario: No benchmark leaves outperformance unavailable
- **WHEN** the Walk-forward evidence contains no benchmark evidence
- **THEN** the Benchmark Outperformance card renders as unavailable rather than fabricating a benchmark

#### Scenario: Pre-terminal runs keep evidence gated
- **WHEN** a Walk-forward run is queued or running and has no persisted evidence
- **THEN** the OOS Summary does not fabricate headline values
- **AND** it shows the existing note that evidence is unavailable until the run reaches a terminal state

#### Scenario: Failed runs state why evidence is unavailable
- **WHEN** a Walk-forward run has status `failed` and no persisted evidence
- **THEN** the OOS Summary does not fabricate headline values
- **AND** it states that evidence is unavailable because the run failed

### Requirement: OOS metrics use backtest-consistent percentage and ratio formatting
The OOS Summary SHALL format return-like metrics as percentages and ratio metrics as ratios, matching the Backtest Detail display semantics. The headline return (median/mean total return) and Max Drawdown SHALL render as percentages. Median Sharpe and the Generalization Gap SHALL render as ratio values, not percentages. Positive Window Rate, Benchmark Outperformance Rate, and Parameter Transition Rate SHALL render as percentages with their fraction counts. Deep-region displays (the Aggregated evidence cards and the per-window table) SHALL keep their existing raw formatting in this change.

#### Scenario: Returns and drawdown render as percentages
- **WHEN** the OOS Summary renders a return or drawdown metric
- **THEN** it is displayed as a percentage (for example a stored value of `0.0234` renders as `2.34%`)

#### Scenario: Ratio metrics keep ratio format
- **WHEN** the OOS Summary renders Median Sharpe or the Generalization Gap
- **THEN** it is displayed as a ratio value without a percent sign

#### Scenario: Rate metrics render with fraction context
- **WHEN** the OOS Summary renders Positive Window Rate, Benchmark Outperformance Rate, or Parameter Transition Rate
- **THEN** it displays the percentage alongside its numerator/denominator or comparison-count context

#### Scenario: Deep regions keep their existing formatting
- **WHEN** the Aggregated evidence cards or the per-window table render metrics
- **THEN** their existing raw decimal formatting is unchanged

### Requirement: Generalization Gap and Evidence Status are presented as explained facts
The OOS Summary SHALL present the Generalization Gap and Evidence Status as factual, explained lines rather than raw metric field dumps. The Generalization Gap SHALL be identified as IS Sharpe minus OOS Sharpe, rendered as a ratio value using its median, and accompanied by an explanation that a positive gap means in-sample selection performed better than out-of-sample and a larger gap indicates weaker generalization. Evidence Status SHALL use the persisted `evidence.metrics.total_return.evidence_status` field (the headline metric family's status; the evidence document has no overall status field) and SHALL be presented with the explanation that `sufficient` requires at least three valid windows.

#### Scenario: Generalization gap is explained
- **WHEN** the OOS Summary renders the Generalization Gap
- **THEN** it shows the gap's median value in ratio format with the IS-minus-OOS-Sharpe meaning
- **AND** it explains the direction so a positive value is read as weaker generalization

#### Scenario: Evidence status is explained
- **WHEN** the OOS Summary renders the Evidence Status
- **THEN** it states whether evidence is sufficient, using the status persisted for the total-return metric family
- **AND** it explains that sufficiency requires at least three valid windows

### Requirement: Walk-forward detail avoids a synthesized verdict
The Walk-forward Detail page SHALL NOT present a synthesized overall score or a simple Pass/Fail judgment. It SHALL present only values and sign-level facts that are directly supported by the persisted evidence. The persisted run status (`success`/`failed`) is a factual state, not a Pass/Fail judgment, and displaying it in the Run Header does not violate this requirement. This deliberately differs from the Backtest Detail decision summary badge; no equivalent badge SHALL be added for Walk-forward runs.

#### Scenario: No synthesized verdict appears
- **WHEN** a Walk-forward detail page renders
- **THEN** no overall score, rating, or Pass/Fail verdict badge is displayed for the run
- **AND** the factual run status remains visible in the Run Header

### Requirement: Walk-forward detail presents sections in the research order
The Walk-forward Detail page SHALL order its content regions top-to-bottom as: Run Header, OOS Summary, Stitched OOS capital path, Aggregated evidence, Window evidence, and Configuration and input provenance. The stitched capital path SHALL be visible after the OOS Summary rather than buried below the evidence regions. The aggregated evidence, window evidence, and provenance regions SHALL retain their existing content and semantics, only their position relative to the first screen changes.

#### Scenario: Sections follow the research order
- **WHEN** a successful Walk-forward detail loads
- **THEN** the Run Header, OOS Summary, Stitched OOS capital path, Aggregated evidence, Window evidence, and Configuration and input provenance regions appear in that DOM and visual order

#### Scenario: Stitched path is above the evidence regions
- **WHEN** a Walk-forward detail has an available stitched capital path
- **THEN** the Stitched OOS capital path renders before the Aggregated evidence region

#### Scenario: Deep evidence remains fully available
- **WHEN** the user scrolls to the Aggregated evidence, Window evidence, or provenance regions
- **THEN** all existing evidence, tables, and configuration content remain present with their current semantics
