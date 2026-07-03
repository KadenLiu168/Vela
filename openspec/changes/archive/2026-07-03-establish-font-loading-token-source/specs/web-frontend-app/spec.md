## ADDED Requirements

### Requirement: Web frontend font loading baseline
The web frontend SHALL load Inter for body and UI text and SHALL provide a non-system PolySans substitute for heading, navigation, and button typography until licensed PolySans assets are self-hosted.

#### Scenario: Frontend document loads configured web fonts
- **WHEN** a developer inspects the web frontend HTML entrypoint
- **THEN** it includes a font loading source for Inter weights used by the CSS tokens
- **AND** it includes a font loading source for the configured PolySans substitute
- **AND** the font loading source uses a swap strategy so text does not remain invisible while fonts load

#### Scenario: PolySans stack preserves future self-hosting priority
- **WHEN** a developer inspects `apps/web/src/styles.css :root`
- **THEN** `--font-polysans` keeps `"PolySans"` before the substitute family
- **AND** it includes the current substitute before system font fallbacks

#### Scenario: Body text uses Inter stack
- **WHEN** a developer inspects the global web frontend CSS
- **THEN** body and root typography use `--font-inter`
- **AND** `--font-inter` includes `"Inter"` before system font fallbacks

### Requirement: Web frontend token source documentation
The repository SHALL document that `apps/web/src/styles.css :root` is the current web frontend implementation token source, while `tokens.json` and `variables.css` are design references that do not directly drive the build.

#### Scenario: Implementation token source is marked
- **WHEN** a developer inspects `apps/web/src/styles.css :root`
- **THEN** the file identifies the root custom properties as the current implementation token source

#### Scenario: Reference token artifacts are marked
- **WHEN** a developer inspects the design token reference documentation or root CSS reference file
- **THEN** it states that `tokens.json` and `variables.css` are design references
- **AND** it states that they are not direct build inputs for the web frontend

#### Scenario: Token documentation records implementation-only additions
- **WHEN** a developer inspects the token source documentation
- **THEN** it records any current token values in `apps/web/src/styles.css :root` that are implementation additions beyond the DESIGN.md reference scale
