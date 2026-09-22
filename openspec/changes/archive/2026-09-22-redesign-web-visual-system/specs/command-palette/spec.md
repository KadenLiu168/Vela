## ADDED Requirements

### Requirement: Command Palette follows semantic visual and typography roles
The dialog MUST use the raised surface, its input the panel surface, and its hover/active row the hover surface. Primary result text uses primary text; metadata uses tertiary text only where contrast remains WCAG AA and MUST promote to secondary text on the hover surface. Numeric and code-like values use Mono; ordinary labels use Sans. Errors use the danger status role and MUST NOT use market-up red.

#### Scenario: Active result remains readable
- **WHEN** a result row is hovered or active
- **THEN** the row MUST use `--surface-hover`
- **AND** readable metadata MUST use at least `--text-secondary`
- **AND** active state MUST remain exposed through the existing ARIA contract

#### Scenario: Palette status and data roles stay distinct
- **WHEN** the palette renders an API error and quantitative ETF metadata
- **THEN** the error MUST use `--status-danger`
- **AND** quantitative metadata MUST use `--font-mono`
- **AND** neither role may use a market-direction token

## REMOVED Requirements

### Requirement: No new design tokens are introduced
**Reason**: The historical implementation constraint names removed legacy tokens and incorrectly requires `tokens.css` to remain byte-identical during a repository-wide token migration.
**Migration**: The palette consumes the shared semantic tokens defined by `design-system` without declaring palette-specific tokens or another `:root` block.
