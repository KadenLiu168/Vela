## MODIFIED Requirements

### Requirement: Card visual roles map to research typography rungs
Ordinary low-priority meta labels MUST map to meta; important supporting date values and evidence counts MUST use at least the 12/16px label role, and status/risk explanations MUST use at least the 13/20px dense role; dense supporting data MUST map to body; primary metrics MUST map to emphasis; detail-page numeric headlines MUST map to display; card titles MUST use the separate card-title role. Descriptions and names MUST remain Sans even when adjacent to Mono data.

#### Scenario: meta label role uses meta rung
- **WHEN** an ordinary low-priority card meta label renders
- **THEN** it MUST use the 11/16px meta role and the documented label weight, except compact-list row labels use the shared 20px row leading defined below

#### Scenario: body value role uses body rung
- **WHEN** dense supporting data renders
- **THEN** it MUST use the 13/20px body/dense role

#### Scenario: emphasis role uses emphasis rung with tabular-nums
- **WHEN** a primary metric renders
- **THEN** it MUST use the 24/30px emphasis role, `--font-mono`, and tabular numerals

#### Scenario: display role uses display rung with Mono
- **WHEN** a detail-page numeric headline renders
- **THEN** it MUST use the 32/36px display role, `--font-mono`, and tabular numerals

#### Scenario: Important evidence remains readable
- **WHEN** a card renders freshness date values, evidence counts, source warnings or unavailability reasons
- **THEN** date values and evidence counts MUST render at least 12/16px and warnings/reasons at least 13/20px
- **AND** compact-list labels MUST retain the shared 11px size and 20px row leading while their values retain 13/20px
- **AND** font family, precision, units and sign MUST remain content-specific
