## ADDED Requirements

### Requirement: Walk-forward Detail presents status-aware input provenance
The Web application SHALL consume the typed v1/v2 input-provenance union. For v2 it SHALL present resolution policy, ETF listing boundaries, reconciled raw/derived counts, confirmed non-trading session evidence, and bounded source links in the existing provenance section. It SHALL label carried values as derived non-trading valuations rather than raw market quotes, preserve all existing performance evidence and navigation, and SHALL NOT turn input status into a score, alert, or pass/fail verdict. For v1 it SHALL retain the existing provenance presentation without fabricated v2 fields.

#### Scenario: V2 provenance distinguishes raw and derived input
- **WHEN** Walk-forward Detail receives valid v2 provenance containing confirmed non-trading sessions
- **THEN** it shows raw and derived counts plus the resolution policy
- **AND** exposes the ETF/date, status reason, and source evidence accessibly
- **AND** does not label a carried value as a traded close

#### Scenario: V1 provenance remains readable
- **WHEN** Walk-forward Detail receives valid v1 provenance
- **THEN** the existing checksum, session bounds, and ETF manifest remain visible
- **AND** no listing/status field is fabricated

#### Scenario: Status-aware provenance remains responsive and accessible
- **WHEN** v2 detail renders at 1440x1000 or 390x844
- **THEN** provenance has no page-level horizontal overflow
- **AND** headings, labels, counts, and source links retain semantic and keyboard access

#### Scenario: Dashboard and routes remain unchanged
- **WHEN** status-aware provenance is available
- **THEN** it appears only in the existing Walk-forward Detail route
- **AND** no Dashboard card, management route, or reference-data edit control is added
