## MODIFIED Requirements

### Requirement: Configuration provenance uses an exact versioned identity
The parent SHALL persist the exact versioned configuration/provenance document and SHA-256 identity. New status-aware executions SHALL identify the resolved-session valuation/tradability policy version. Display paths MAY be retained but SHALL NOT affect identity; equal effective configuration and policy inputs produce equal checksums while repeated executions receive distinct run ids.

#### Scenario: Display path does not change identity
- **WHEN** equal effective configuration and policy input are loaded from different source paths
- **THEN** their effective configuration checksum is equal

#### Scenario: Resolution policy changes identity
- **WHEN** the status-aware valuation/tradability policy version differs
- **THEN** configuration/provenance identity differs even if YAML strategy values match

### Requirement: Input provenance is a compact bounded manifest
New executions SHALL persist `wf_provenance_v2`. Its manifest SHALL retain ordered ETF local ids and canonical identities, fund inception and listing dates, official sessions, following-session sentinel, raw and derived counts/bounds, supported status/source evidence summaries, resolution policy version, and checksum metadata without copying the complete raw price-value table. Query boundaries SHALL continue to accept valid `wf_provenance_v1` without fabricating v2 fields.

#### Scenario: V2 manifest summarizes raw and derived sources
- **WHEN** status-aware input provenance is persisted
- **THEN** per-ETF and global raw/derived counts and bounds reconcile
- **AND** every derived record corresponds to one supported authoritative status

#### Scenario: Manifest excludes complete raw table
- **WHEN** v2 provenance is persisted
- **THEN** the bounded manifest contains no duplicate complete raw price array

#### Scenario: Legacy v1 remains readable
- **WHEN** history contains a valid `wf_provenance_v1` document
- **THEN** queries preserve its original semantics and do not add listing/status claims

### Requirement: Input checksum covers every effective database input
For `wf_provenance_v2`, the canonical input checksum SHALL cover policy version; ETF id/exchange/symbol, fund inception and listing dates; ordered official sessions and following-session sentinel; every effective raw `close_price`/`factor_hfq` row; and every effective status, reason, source, share ratio, resolution, and carried adjusted value. It SHALL exclude generated outputs, pre-listing rows, and future inputs. Valid legacy v1 checksums remain governed by their original contract.

#### Scenario: Raw input drift changes checksum
- **WHEN** an effective raw price or factor changes
- **THEN** the v2 checksum changes

#### Scenario: Temporal evidence drift changes checksum
- **WHEN** listing date, status evidence, share ratio, resolution, or carried adjusted value changes
- **THEN** the v2 checksum changes

#### Scenario: Equal v2 inputs have stable checksum
- **WHEN** two executions have byte-equivalent canonical effective inputs under the same policy version
- **THEN** their input checksums are equal

#### Scenario: Invalid v2 reconciliation fails closed
- **WHEN** raw/derived ownership, ordering, date bounds, source-state exclusivity, carry ancestry, counts, or checksum do not reconcile
- **THEN** persistence and query validation reject the document
