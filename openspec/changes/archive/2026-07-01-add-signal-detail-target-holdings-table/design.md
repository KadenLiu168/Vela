## Context

COP-101 connected the Signal Detail page to `GET /api/strategy-signals/latest` and renders latest signal metadata. The shared API client already exposes `LatestStrategySignalPosition` with the position fields required by COP-102, so this change can stay in the frontend page layer.

## Goals / Non-Goals

**Goals:**

- Render target holdings on the Signal Detail page from the latest signal API response.
- Show exchange, symbol, target weight, rank, score, and fallback status for each position.
- Format target weight as a percentage while preserving meaningful precision from the API decimal string.
- Keep rank and score readable without inventing data when the API returns `null`.

**Non-Goals:**

- No backend API, database model, or API client endpoint changes.
- No filtering, sorting controls, pagination, or editable holdings.
- No candidate ranking diagnostics beyond the persisted target position fields required by COP-102.

## Decisions

- Render the holdings as a native HTML table on `SignalDetailPage`.
  - Rationale: the data is tabular and static; a native table is simpler and more accessible than custom grid markup.
- Keep formatting local to `SignalDetailPage`.
  - Rationale: the formatting is page-specific and there is no shared formatting module in the frontend yet.
- Format `target_weight` by converting the API decimal string to a percentage with up to four fractional digits, trimming only trailing zeroes.
  - Rationale: values such as `0.333333` display as `33.3333%`, while `0.500000` displays as `50%`. This is clear and avoids losing key precision for common strategy weights.
- Render `rank` and `score` as `None` when the API value is `null`.
  - Rationale: fallback positions can have no rank or score, and the UI should not imply a value exists.

## Risks / Trade-offs

- Decimal-to-number formatting could lose precision for extremely long decimal strings. The latest signal API currently returns practical strategy decimals; four percentage decimals preserves the precision relevant to target weights in this UI.
- A table can overflow on narrow screens. CSS will wrap the table in a horizontally scrollable region rather than compressing columns into unreadable text.
