## ADDED Requirements

### Requirement: Shared frontend status presentation
The web frontend SHALL render shared loading, error, info, success, and empty-state feedback across Dashboard, Signal Detail, and Backtest Detail using tokenized neutral surfaces, borders, typography, spacing, and narrow state accents.

#### Scenario: Shared feedback variants preserve semantics
- **WHEN** loading, info, success, or error `FeedbackMessage` variants render
- **THEN** non-error variants MUST keep `role="status"`
- **AND** error variants MUST keep `role="alert"`
- **AND** each variant MUST use the shared `feedback-message` class plus a variant-specific class

#### Scenario: Empty states use shared tokenized presentation
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders an existing empty-state message
- **THEN** the message uses the shared `.empty-state` tokenized editorial presentation
- **AND** successful empty API responses are not treated as request failures

#### Scenario: Detail and dashboard states avoid broad chromatic blocks
- **WHEN** Dashboard load states, page loading feedback, page error feedback, operation feedback, or empty states are visible
- **THEN** the visible state presentation uses neutral project tokens with narrow Ember, Brass, Graphite, Slate, or Mist accents
- **AND** broad blue, green, or red filled feedback blocks are not used
- **AND** existing API calls, route targets, loading timing, error categorization, and message meaning remain unchanged
