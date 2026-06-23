## Context

Momentum scoring already calculates scores, ranks eligible ETFs, and selects configured Top N entries. Strategy configuration already validates `defense.asset` as an exchange/symbol identity and ensures that asset exists in the active ETF universe when loaded through the strategy config loader.

## Goals / Non-Goals

**Goals:**

- Apply a defensive asset fallback when ranked ETF candidates cannot satisfy `selection.top_n`.
- Keep existing Top N selection behavior unchanged when enough ranked candidates are available.
- Return enough selection data for later signal generation to identify the defensive asset and target weight.

**Non-Goals:**

- Persist strategy signals or positions.
- Add CLI or API entrypoints.
- Change the strategy configuration schema.
- Resolve the defensive asset identity to a database ETF id.

## Decisions

- Add a separate fallback-aware selection function instead of changing `select_top_n_etfs`.
  - Rationale: COP-50 already specified that insufficient Top N returns all available ranked ETFs. Keeping that function stable preserves the previous contract while COP-51 adds an explicit fallback rule for signal generation.
  - Alternative considered: Change `select_top_n_etfs` directly. Rejected because it would invalidate the existing Top N insufficient-candidate scenario.
- Represent fallback output with a small dataclass carrying exchange, symbol, rank, score, and target weight.
  - Rationale: The configured defensive asset is identified by exchange/symbol, and no current service resolves that identity to an `ETFInfo.id` during selection.
  - Alternative considered: Query `ETFInfo` to resolve the id. Rejected as unnecessary for this issue and inconsistent with the pure list-based Top N selection helper.
- Trigger fallback when `len(rankings) < config.selection.top_n`.
  - Rationale: The Linear issue says fallback applies when optional ETF candidates do not meet conditions; after scoring/ranking, ranked results are the eligible candidates for Top N.

## Risks / Trade-offs

- Defensive selection uses exchange/symbol instead of database id -> later persistence code must resolve it before writing `StrategySignalPosition`.
- Partial risky allocation is replaced by a full defensive allocation when candidates are insufficient -> this matches COP-51 but differs from the COP-50 low-level Top N helper behavior.
