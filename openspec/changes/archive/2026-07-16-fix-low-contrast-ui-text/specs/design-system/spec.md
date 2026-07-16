## ADDED Requirements

### Requirement: Low-contrast palette colors are not readable text colors
The web frontend MUST NOT use `--color-ash` or `--color-smoke` as the sole `color` value for readable text rendered on dark app surfaces. Readable text includes headings, body copy, labels, table text, command-palette text, status-pill text, placeholders, and other text whose characters convey information to sighted users.

Readable secondary or metadata text on dark surfaces MUST use at least `--color-fog`; more important text MUST use a higher-contrast token such as `--color-mist` or `--color-paper`.

`--color-ash` and `--color-smoke` MAY remain in use for decorative or structural roles, including borders, dividers, SVG grid lines, subdued accents, and visual separators that are not the sole carrier of information.

#### Scenario: readable text avoids ash and smoke
- **WHEN** a CSS rule under `apps/web/src/` sets the foreground `color` for readable text on a dark app surface
- **THEN** the value MUST NOT be `var(--color-ash)` or `var(--color-smoke)`
- **AND** the value MUST resolve to `var(--color-fog)`, `var(--color-mist)`, `var(--color-paper)`, or a higher-contrast semantic/status token appropriate to the state

#### Scenario: command palette metadata remains readable
- **WHEN** the command palette renders placeholder text or row-kind metadata
- **THEN** those text roles MUST use a color token that meets WCAG AA normal-text contrast on the palette surface
- **AND** they MUST NOT use `var(--color-ash)` or `var(--color-smoke)` as their foreground text color

#### Scenario: neutral status text remains readable
- **WHEN** a neutral or fallback status pill renders text such as an empty or no-data state
- **THEN** the text color MUST meet WCAG AA normal-text contrast on the pill's rendered surface
- **AND** an empty-state accent token that resolves to `var(--color-smoke)` MUST NOT be used as the sole text color

#### Scenario: decorative uses may stay subdued
- **WHEN** a CSS rule uses `var(--color-ash)` or `var(--color-smoke)` for non-text decoration such as `border-color`, SVG `stroke`, chart grid lines, or a purely visual separator
- **THEN** that use remains conforming
- **AND** if the separator is rendered as a text character in the DOM, it MUST be hidden from assistive technology when it does not convey information
