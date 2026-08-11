## MODIFIED Requirements

### Requirement: Walk-forward list page provides run trigger
The Walk-forward list page SHALL expose a "Run walk-forward" action that calls the shared frontend API client's `runWalkForward()` function against `POST /api/walk-forwards/run`, disables itself while an active queued/running record exists, and polls `GET /api/walk-forwards/{run_id}` on a bounded interval to observe durable lifecycle status. The action SHALL be placed on the Walk-forward list page (not the Dashboard) because Walk-forward is a low-frequency research tool outside the daily signal-generation flow. On `status = "queued"` it SHALL show a queued indicator and continue polling; on `status = "running"` it SHALL show a running indicator and continue polling; on `status = "success"` it SHALL navigate to `/walk-forwards/{run_id}` through client-side navigation; on `status = "failed"` it SHALL surface the API-provided bounded `error_message` and re-enable the action. The page SHALL discover an active record from refreshed history after reload, stop polling when the document is hidden and resume when visible. The action SHALL NOT block on run completion synchronously, accept a client-supplied configuration path, create a duplicate request while active work exists, or retry a failed record itself. The run-trigger button SHALL carry a valid `design-system` button variant class (`button-secondary`) and SHALL NOT rely on any style class that is undefined in `styles.css`.

#### Scenario: User triggers a run from the list page
- **WHEN** the user clicks "Run walk-forward" on the Walk-forward list page and no active record exists
- **THEN** the frontend calls `runWalkForward()` against `POST /api/walk-forwards/run`
- **AND** the action enters a disabled in-progress state while the request is pending
- **AND** the action prevents duplicate submissions while the request is pending

#### Scenario: Run trigger button uses a defined variant
- **WHEN** the Walk-forward list page renders the "Run walk-forward" button
- **THEN** the button's className includes `button-secondary`
- **AND** every style class on the button resolves to a rule defined in `apps/web/src/styles.css`
- **AND** the run-trigger container applies the standard list-page spacing below the button (`margin-bottom: var(--spacing-16)`)

#### Scenario: Accepted run shows queued then navigates on success
- **WHEN** the run-trigger request returns HTTP 202 with a `walk_forward_run_id` and `status = "queued"`
- **THEN** the action stays disabled and shows a queued indicator
- **AND** the frontend polls `GET /api/walk-forwards/{run_id}` on a bounded interval through queued and running states
- **AND** when the polled `status` becomes `success`, the page navigates to `/walk-forwards/{run_id}` through client-side navigation

#### Scenario: Reload preserves active-job state
- **WHEN** the list page reloads while the API history contains a queued or running record
- **THEN** the page identifies that record as active, disables the action, and resumes polling its detail
- **AND** it does not issue another POST submission

#### Scenario: Failed run surfaces error and re-enables action
- **WHEN** a polled `status` becomes `failed`
- **THEN** the page stops polling
- **AND** the page surfaces the API-provided `error_message`
- **AND** the "Run walk-forward" action is re-enabled

#### Scenario: Polling pauses when document is hidden
- **WHEN** the document becomes hidden while a record is queued or running
- **THEN** the frontend stops issuing poll requests
- **AND** when the document becomes visible again, polling resumes from the current `status`

#### Scenario: Concurrent-run conflict is surfaced without starting a second run
- **WHEN** the run-trigger request returns HTTP 409 indicating an active queued or running record
- **THEN** the page surfaces the conflict error
- **AND** the frontend does not issue a second `POST /api/walk-forwards/run`
- **AND** the action refreshes history before allowing another submission

#### Scenario: Expected domain error is surfaced without leaving an active record
- **WHEN** the run-trigger request returns HTTP 400 with category `operation_failed` during enqueue preflight
- **THEN** the page surfaces the API-provided error message
- **AND** no `WalkForwardRun` row with `status = "queued"` or `status = "running"` is left visible in the list
- **AND** the "Run walk-forward" action is re-enabled

#### Scenario: Accepted run polls and navigates on success
- **WHEN** the run-trigger request returns HTTP 202 with a `walk_forward_run_id`
- **THEN** the action stays disabled and shows a running indicator
- **AND** the frontend polls `GET /api/walk-forwards/{run_id}` on a bounded interval
- **AND** when the polled `status` becomes `success`, the page navigates to `/walk-forwards/{run_id}` through client-side navigation

#### Scenario: Expected domain error is surfaced without leaving a running record
- **WHEN** the run-trigger request returns HTTP 400 with category `operation_failed` (for example missing market data)
- **THEN** the page surfaces the API-provided error message
- **AND** no `WalkForwardRun` row with `status = "queued"` or `status = "running"` is left visible in the list
- **AND** the "Run walk-forward" action is re-enabled
