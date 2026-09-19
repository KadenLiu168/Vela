# walk-forward-results-ui Specification Delta

## MODIFIED Requirements

### Requirement: Walk-forward detail presents a Run Header with navigation and run identity
The Walk-forward Detail page SHALL render a Run Header as the first content region of its detail body, immediately following the existing page heading, which continues to carry the run title `Walk-forward #<id>` (visible in every state, including loading and not-found). The Run Header SHALL contain a link back to the Walk-forward history list at `/walk-forwards`, the run status, and a single summary line showing Strategy, test date range, and Window count. The full execution metadata (provenance version, evidence version, started/finished/created timestamps, config checksum, input checksum) SHALL NOT occupy the first screen; it SHALL be presented in the provenance region of the page.

When the run has not reached a terminal state, the Run Header SHALL additionally state what moves the run forward, so that a pre-terminal page is not a status with nothing behind it. For a `queued` run, that statement SHALL say that queued runs are executed by a separate local worker rather than by the API process, and SHALL name the command that executes them. For a `running` run, it SHALL say that the run is being executed and that the page does not refresh itself. A terminal run SHALL NOT render this statement. This statement SHALL NOT introduce execution metadata onto the first screen.

#### Scenario: Header precedes all other content
- **WHEN** a Walk-forward detail page loads
- **THEN** the Run Header appears first within the detail body, immediately after the page heading
- **AND** it provides a navigation link back to the Walk-forward history list targeting `/walk-forwards`
- **AND** it shows the run status and a summary line with Strategy, date range, and Window count
- **AND** the page heading above it carries the run title `Walk-forward #<id>`

#### Scenario: Execution metadata is off the first screen
- **WHEN** a Walk-forward detail page renders its first screen
- **THEN** the provenance version, evidence version, timestamps, and checksums are not shown in the first-screen header
- **AND** they remain available in the provenance region of the page

#### Scenario: A queued run states what executes it
- **WHEN** the run status is `queued`
- **THEN** the Run Header states that queued runs are executed by a separate local worker rather than by the API process
- **AND** it names the command that executes them

#### Scenario: A running run states that the page does not refresh itself
- **WHEN** the run status is `running`
- **THEN** the Run Header states that the run is being executed and that the page does not refresh itself

#### Scenario: A terminal run carries no next-step statement
- **WHEN** the run status is `success` or `failed`
- **THEN** the Run Header does not state a next step
