## Context

`vela_core.momentum_scoring` already calculates weighted momentum scores and ranks eligible ETFs deterministically. COP-50 starts from those ranked results and needs a concrete Top N selection contract for strategy signal generation.

## Goals / Non-Goals

**Goals:**

- Provide a simple pure function for selecting configured Top N ETFs from ranked momentum results.
- Return enough information for downstream signal construction: ETF id, rank, score, and target weight.
- Make insufficient-eligible behavior deterministic and testable.

**Non-Goals:**

- No defensive-asset fallback.
- No signal persistence or portfolio rebalance logic.
- No database schema, CLI, config schema, or trend-filter behavior changes.
- No changes to momentum scoring or ranking semantics.

## Decisions

- Add `TopNSelection` as a frozen dataclass in `momentum_scoring.py`.
  - Rationale: existing score and ranking outputs are frozen dataclasses in the same module.
  - Alternative considered: reuse `MomentumRanking` and compute weights elsewhere. That leaves COP-50's required output shape implicit.

- Add `select_top_n_etfs(rankings, config)` as a pure function.
  - Rationale: selection is deterministic and depends only on ranked inputs plus `StrategyConfig.selection.top_n`.
  - Alternative considered: combine ranking and selection in one function. That would blur existing tested ranking behavior and make the change larger.

- Assign equal target weights across the actual selected count.
  - Rationale: COP-50 requires target weight output but does not define a separate weighting model. Equal weight is simple and matches Top N selection without adding portfolio optimization.
  - Alternative considered: divide by configured Top N even when fewer ETFs are available. That would leave unallocated weight without an explicit downstream owner.

## Risks / Trade-offs

- Equal weighting may not be the final portfolio construction policy → keep the helper narrow so later issues can replace or extend weighting without touching scoring.
- Returning fewer than configured Top N can surprise callers → document and test that insufficient candidates return all available eligible ETFs.
