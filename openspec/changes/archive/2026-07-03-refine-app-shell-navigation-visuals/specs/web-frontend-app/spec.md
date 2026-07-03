## ADDED Requirements

### Requirement: App Shell editorial header navigation
The web frontend SHALL render the App Shell header and navigation with the tokenized editorial visual system while preserving existing navigation semantics and behavior.

#### Scenario: Header uses editorial visual tokens
- **WHEN** a developer inspects the App Shell header implementation and stylesheet
- **THEN** the brand, API metadata, navigation container, and navigation links use dedicated styling hooks
- **AND** their visual styles use the global design token custom properties for typography, neutral colors, spacing, radius, and surfaces

#### Scenario: Navigation remains behaviorally unchanged
- **WHEN** a user activates an App Shell navigation link
- **THEN** the existing client-side navigation behavior is used
- **AND** the link labels, href targets, and active `aria-current="page"` semantics remain unchanged

#### Scenario: Navigation renders as a responsive pill group
- **WHEN** the App Shell renders on desktop or narrow viewport widths
- **THEN** the navigation appears as a warm-gray pill-style group with text-style nav items
- **AND** the group remains readable and can wrap without introducing new routes, dropdowns, or controls
