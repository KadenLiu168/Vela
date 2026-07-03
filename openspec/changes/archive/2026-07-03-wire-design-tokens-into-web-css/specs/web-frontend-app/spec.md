## ADDED Requirements

### Requirement: Web global design token foundation
The web frontend SHALL expose the provided design token foundation through CSS custom properties in `apps/web/src/styles.css`, covering core colors, typography, spacing, layout, radius, and surface tokens from the project design reference.

#### Scenario: Global stylesheet defines design tokens
- **WHEN** a developer inspects `apps/web/src/styles.css`
- **THEN** the stylesheet defines CSS custom properties for the provided core colors, font families, type scale, spacing scale, layout values, border radii, and surface values
- **AND** those properties are available from the global `:root` scope

#### Scenario: Base page styles use design tokens
- **WHEN** the web frontend renders any route
- **THEN** the base document typography, text color, and page background are driven by the global design token custom properties
- **AND** the rendered route structure, API calls, and business behavior remain unchanged

#### Scenario: Token wiring avoids new build dependencies
- **WHEN** a developer validates the frontend package
- **THEN** the design token foundation is available without adding a token build pipeline, UI framework, or new runtime dependency
