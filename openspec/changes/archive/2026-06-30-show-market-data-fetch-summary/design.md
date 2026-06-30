## Context

COP-93 added `POST /api/market-data/fetch?mode=incremental|full` and COP-94 wired the Dashboard incremental fetch button. The current Dashboard calls the endpoint, prevents duplicate submissions, and refreshes Dashboard data, but it discards successful response bodies and only shows a generic request error for failed HTTP/network requests.

## Goals / Non-Goals

**Goals:**

- Render the latest market data fetch response in the Dashboard operations area.
- Show fetched, inserted, and updated row counts for successful responses.
- Show failed symbols and an error summary for `partial` and `failed` API statuses.
- Provide local retry/source/data-state guidance without changing the API contract.
- Cover the behavior with focused frontend tests plus the existing real API integration path.

**Non-Goals:**

- Add a full fetch UI.
- Change the backend market data fetch endpoint or response contract.
- Rework Dashboard layout beyond the operation summary area.

## Decisions

- Store the latest `MarketDataFetchResponse` in Dashboard component state.
  - Rationale: the existing fetch handler already receives the response, and this keeps the change local to the operation UI.
  - Alternative considered: reload and infer results from aggregate Dashboard state. That would not expose failed symbols or backend error summaries.
- Treat `status` as display data for successful HTTP responses.
  - Rationale: COP-93 returns `success`, `partial`, or `failed` in the response body; partial/failed still carry useful counts and failure details.
  - Alternative considered: throw client errors for non-success statuses. That would hide row counts and failed symbols behind generic error handling.
- Keep HTTP/network failures separate from workflow result summaries.
  - Rationale: transport failures need retry/API availability copy, while workflow failures need source/local data guidance.

## Risks / Trade-offs

- `status` strings are currently typed as `string`, so unexpected values could render as a neutral result. Mitigation: copy focuses on known `success`, `partial`, and `failed` statuses, with counts still shown for other successful responses.
- A long failed symbol list could crowd the operations panel. Mitigation: render symbols as wrapped inline text within the existing panel.
