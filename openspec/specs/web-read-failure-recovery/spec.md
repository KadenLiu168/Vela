# web-read-failure-recovery Specification

## Purpose
Defines how the web client reports and recovers from failed reads against the local API, so that a failure states a cause the user can act on and can be retried in place.

## Requirements

### Requirement: Read failures state an actionable cause
When a list or detail read against the local API fails, the web frontend SHALL render a failure description that is a complete sentence naming the cause and the recovery action, and SHALL NOT expose the internal failure category as the error identifier. A failure caused by the API being unreachable SHALL state that the local API could not be reached and SHALL name confirming that the API service is running as the next step. A failure caused by an error HTTP response SHALL state that the API returned an error response and SHALL include the numeric status code, so that distinct statuses are distinguishable in the interface. A read failure SHALL NOT render fabricated or placeholder data.

#### Scenario: Unreachable API names the cause and the action
- **WHEN** a list or detail read fails because the API could not be reached
- **THEN** the rendered description states that the local API could not be reached
- **AND** it names confirming that the API service is running as the next step
- **AND** it does not contain the internal failure category `http` or `network`

#### Scenario: Error HTTP response reports its status code
- **WHEN** a list or detail read fails with an error HTTP response
- **THEN** the rendered description states that the API returned an error response
- **AND** it contains that response's numeric status code
- **AND** it does not contain the internal failure category `http` or `network`

#### Scenario: Distinct statuses are distinguishable
- **WHEN** the same read fails first with one error status and later with a different error status
- **THEN** the two rendered descriptions differ in the reported status code

#### Scenario: Failure does not fabricate data
- **WHEN** any list or detail read has failed
- **THEN** the page does not render data rows, metric values, or empty-state wording in place of the failed read

### Requirement: Read failures are recoverable in place
Every failed list or detail read SHALL render a retry control alongside its failure description. Activating the retry control SHALL re-issue the same request — the same endpoint with the same parameters, filter, and pagination offset that failed — and SHALL show the page's loading state while that request is in flight. A successful retry SHALL render the normal loaded state for that page. A retry that fails again SHALL restore the failure description and keep the retry control available. The retry control SHALL NOT reload the document, and SHALL carry a `design-system` button variant className.

#### Scenario: Retry re-issues the failed request
- **WHEN** a user activates the retry control on a failed read
- **THEN** the same endpoint is requested again with the same parameters, filter, and pagination offset
- **AND** the page's loading state is shown while the request is in flight
- **AND** the document is not reloaded

#### Scenario: Successful retry renders the loaded state
- **WHEN** a retry request succeeds
- **THEN** the page renders its normal loaded state for the retried request
- **AND** the failure description and retry control are no longer rendered

#### Scenario: Repeated failure keeps recovery available
- **WHEN** a retry request fails again
- **THEN** the failure description is rendered again
- **AND** the retry control remains available

#### Scenario: Retry control declares its variant
- **WHEN** a retry control is rendered
- **THEN** its `className` carries one of the `design-system` button variants

#### Scenario: Retry preserves the selected list context
- **WHEN** a user has selected a Signal source filter or a non-zero pagination offset, that read fails, and the user activates the retry control
- **THEN** the re-issued request carries the same source filter and offset
