## ADDED Requirements

### Requirement: AppShell brand remains subordinate to page research content
The visible `Vela Research` brand MUST remain non-heading text and MUST use the Sans family at approximately 22px, 28px line height, 620 weight, and `-0.035em` tracking. The route's page title MUST remain the primary visual heading.

#### Scenario: Brand and page title preserve hierarchy
- **WHEN** any AppShell route renders
- **THEN** the brand MUST remain smaller than the 36px page title
- **AND** the page title MUST remain the document's only page-identity heading

### Requirement: Visual redesign preserves application behavior
The Celestial Research migration MUST preserve AppShell skip-link behavior, navigation labeling and `aria-current`, programmatic main focus, route behavior, button `aria-pressed`, chart text legends, reduced motion, and existing data behavior. It MUST NOT change backend APIs, dashboard data logic, or chart geometry algorithms.

#### Scenario: Existing behavior survives visual migration
- **WHEN** the redesigned Web application is exercised through existing navigation, controls, tables, charts, and Command Palette tests
- **THEN** accessibility and behavioral contracts MUST remain unchanged except for the explicitly modified visual semantics

## MODIFIED Requirements

### Requirement: Bootstrap button uses primary visual variant
The Dashboard Bootstrap action MUST remain the rightmost and only prominent primary CTA. It MUST use the shared Celestial Blue primary-button treatment; no other Dashboard element may imitate its filled primary hierarchy. AppShell current navigation MUST use semantic panel, border, text, hover, and interaction roles without an acid-lime underline or a high-saturation filled highlight.

#### Scenario: Bootstrap is the rightmost Dashboard action
- **WHEN** the Dashboard renders its action list
- **THEN** Bootstrap MUST remain the rightmost button and the sole primary variant in that view

#### Scenario: nav-link active state is not an acid-lime fill
- **WHEN** a navigation link carries `aria-current="page"`
- **THEN** it MUST remain programmatically current
- **AND** its visual state MUST use `--text-primary` with a restrained interaction-text, surface, border, or indicator treatment
- **AND** it MUST NOT use acid lime or a high-saturation filled background
