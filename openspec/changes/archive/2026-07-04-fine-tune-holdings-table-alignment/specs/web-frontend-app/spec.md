## ADDED Requirements

### Requirement: Signal Detail holdings table numeric alignment
The web frontend SHALL render the Signal Detail target holdings table with report-like typography, numeric alignment, and restrained dividers while preserving the existing table structure and behavior.

#### Scenario: Numeric holdings columns align for scanning
- **WHEN** the Signal Detail page renders target holdings
- **THEN** target weight, rank, and score cells MUST use tabular numerals and right alignment
- **AND** their matching headers MUST align with those numeric cells
- **AND** exchange, symbol, and fallback text columns MUST remain left-aligned and readable

#### Scenario: Holdings table uses restrained header and hairline rhythm
- **WHEN** the Signal Detail target holdings table renders
- **THEN** the header MUST use the existing Slate and micro/caption typography hierarchy
- **AND** body rows MUST use Mist hairline separators with the final row divider removed
- **AND** row padding and line height MUST remain consistent with the editorial data style in `DESIGN.md`

#### Scenario: Holdings table preserves narrow-screen scrolling
- **WHEN** the Signal Detail page is viewed on a narrow viewport
- **THEN** the target holdings table MUST keep horizontal scrolling through `holdings-table-wrap`
- **AND** the implementation MUST preserve existing table DOM structure, rendered text, API calls, route behavior, and test selectors
