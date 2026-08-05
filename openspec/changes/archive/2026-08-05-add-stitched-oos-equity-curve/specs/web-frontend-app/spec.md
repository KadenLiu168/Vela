## MODIFIED Requirements

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
