## ADDED Requirements

### Requirement: Shared status states use restrained Ember accents
The web frontend SHALL keep empty, error, and operation status surfaces primarily achromatic, reserving Ember Orange for small functional accents rather than broad error presentation.

#### Scenario: Error surfaces avoid broad Ember rails
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders page-level error feedback
- **THEN** the error surface MUST use neutral project tokens for its primary border, text, and background treatment
- **AND** it MUST NOT rely on an Ember Orange rail or filled chromatic block as the main error identifier
- **AND** existing `role="alert"`, `aria-live`, and error message text MUST remain unchanged

#### Scenario: Operation failed states remain recognizable without Ember as the status color
- **WHEN** Dashboard operation feedback renders failed or partial-failure summaries
- **THEN** the summary surface MUST remain visually distinct using neutral borders, text hierarchy, and existing status copy
- **AND** Ember Orange MAY be used only for small functional punctuation such as operation link underlines
- **AND** existing operation result text, guidance, and route behavior MUST remain unchanged

#### Scenario: Empty and non-error states stay visually unified
- **WHEN** loading, empty, success, info, not-found, partial, or failed states render
- **THEN** they MUST continue to use the shared tokenized status presentation
- **AND** the implementation MUST NOT introduce red, blue, green, new status color systems, skeleton loaders, or feedback component rewrites
