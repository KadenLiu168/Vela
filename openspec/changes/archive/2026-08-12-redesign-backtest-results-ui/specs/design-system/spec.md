# design-system Specification

## ADDED Requirements

### Requirement: Categorical multi-series color palette
The design-system SHALL provide six categorical series tokens in `apps/web/src/styles/tokens.css`: `--color-series-1: var(--color-acid-lime)`, `--color-series-2: var(--color-signal-teal)`, `--color-series-3: #4f8cff`, `--color-series-4: var(--color-coral-red)`, `--color-series-5: #f2b84b`, and `--color-series-6: #d96bd8`. The leading token catalog SHALL list the categorical series group. The current supported keys SHALL map `"strategy"` to series 1, `"equal_weight_monthly"` to series 2, and `"csi_300_buy_hold"` to series 3 in both the equity-curve and rolling-stability chart consumers. Series 4–6 SHALL be reserved deterministic fallback roles and SHALL NOT imply backend support for additional benchmarks.

#### Scenario: Palette declares exact controlled tokens
- **WHEN** the categorical palette is introduced
- **THEN** all six specified tokens and values are declared in the single `tokens.css` `:root` block
- **AND** the leading catalog comment lists the categorical series group

#### Scenario: Series color maps stably by key
- **WHEN** an equity-curve or rolling-stability chart resolves a current supported series key
- **THEN** the color is derived from the explicit key mapping rather than array position
- **AND** the same key always resolves to the same token in both chart consumers even when another series has no plottable points
- **AND** strategy, equal-weight, and CSI-300 resolve to three distinct colors

#### Scenario: Direct-label colors remain readable
- **WHEN** a series color is used for direct-label text on `--surface-obsidian`
- **THEN** the resolved foreground/background pair meets WCAG AA normal-text contrast
- **AND** series identity is also present as text in the swatch legend rather than communicated by hue alone

#### Scenario: Tokens stay in the single canonical file
- **WHEN** the categorical color tokens are introduced
- **THEN** they live only inside the `tokens.css` `:root` block
- **AND** no duplicate declaration is introduced in another CSS file
