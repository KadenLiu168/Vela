# web-frontend-app Specification Delta

## RENAMED Requirements

- FROM: `### Requirement: Walk-forward presentation does not expand Dashboard`
- TO: `### Requirement: Walk-forward evidence stays in the dedicated flow and Dashboard adds no walk-forward score`

## MODIFIED Requirements

### Requirement: Walk-forward evidence stays in the dedicated flow and Dashboard adds no walk-forward score
The dedicated navigation/list/detail flow SHALL remain the only surface for complete Walk-forward evidence: per-window records, parameter stability, benchmark-regime metrics, distribution evidence, the stitched out-of-sample capital path, and provenance. The Dashboard SHALL remain free of a walk-forward score, ranking, threshold alert, or pass/fail result, and SHALL NOT reproduce any of those complete-evidence sections or add a Walk-forward entry to its reference and operations region. The Dashboard MAY present one compact OOS-robustness decision layer inside its decision-layer sequence, as defined by the `research-workbench-ui` capability, that states the latest run's status, test range, and window count and, for a successful run, the cross-window aggregate headline values with their sufficiency statement, together with links into the Walk-forward flow. That layer SHALL present persisted evidence values only and SHALL NOT compute any walk-forward value in the browser.

#### Scenario: Dashboard has no WF card
- **WHEN** successful Walk-forward history exists
- **THEN** the Dashboard's reference and operations region does not add a Walk-forward card
- **AND** the Dashboard does not render a walk-forward score, ranking, threshold alert, or pass/fail result

#### Scenario: Dashboard OOS layer stays compact
- **WHEN** the Dashboard renders its OOS-robustness decision layer for a successful run
- **THEN** it shows only the run's status, date range, window count, the cross-window aggregate headline values, the generalization-gap and sufficiency statements, and links into the Walk-forward flow
- **AND** it does not render per-window records, parameter stability, benchmark-regime evidence, distribution evidence, stitched capital path, or provenance

#### Scenario: Detailed evidence stays in the dedicated flow
- **WHEN** a user wants the complete walk-forward evidence for a run
- **THEN** the Dashboard layer links to the existing Walk-forward list or detail route
- **AND** the dedicated detail page remains the only surface for per-window, stitched, provenance, and deep-risk evidence

#### Scenario: OOS detail links remain navigable
- **WHEN** the Dashboard OOS layer renders a link to `/walk-forwards` or `/walk-forwards/{id}`
- **THEN** activating it opens the existing Walk-forward list or detail route through client-side navigation
