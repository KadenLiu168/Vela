## Context

回测流程（`run_backtest`）：先写信号入库（`persist_strategy_signal`，每条带 `backtest_run_id=null`），再读信号算持仓/净值，最后建 `backtest_run` 行并 link 信号。读取信号在 `portfolio_holdings._latest_successful_signals_by_date`：按 `strategy_id + config_version + signal_date<=through` 取**全局最新**（`generated_at desc, id desc`）。`2026-07-19-add-signal-provenance` 已让 `run_backtest` 在生成后 capture `signal_ids` 列表并 link 到 run，但持仓计算从未使用该列表，仍走全局 latest-wins。重跑会追加新信号行；尤其当本次某个 rebalance 只生成失败信号时，成功信号查询会回读旧 run 在该日期的成功信号，形成跨 run 拼盘，导致 Run1/Run2 差 7pt。

约束：
- 本地 SQLite 库。
- 信号读取是回测**唯一**污染向量：`strategy_equity_curve.calculate_strategy_equity_curve` 内部调用 `calculate_portfolio_holdings` 获取持仓快照，再基于持仓和价格计算净值——净值曲线的正确性同样依赖持仓快照的信号来源。
- 用户将重置数据库，存量脏数据（legacy 重复行、无 link 旧 run）不处理。

## Goals / Non-Goals

**Goals:**
- 持仓计算只认本次 run 的 `signal_ids`。
- `run_backtest` 把 `signal_ids` 传入持仓计算。
- 重跑追加新 run，互不污染。

**Non-Goals:**
- 不改 `strategy_equity_curve` 中的净值计算逻辑（它只消费持仓快照，不直接读信号）——但它的签名和调用方式需要修改以透传 `signal_ids`。
- 不建数据快照（属于另一 change `add-backtest-data-snapshot`）。
- 不暴露 API / CLI / 前端变更。
- 不处理存量脏数据（用户重置库）。
- 不改信号生成 / 打分语义。

## Decisions

### D1: 用 `IN (signal_ids)` 过滤，而非加 `backtest_run_id` 联合查询
修改 `_latest_successful_signals_by_date` 接受 `signal_ids` 参数，查询 `WHERE StrategySignal.id IN (signal_ids)`。理由：`run_backtest` 已 capture 完整 `signal_ids`，直接按 id 过滤最精确、零歧义，无需在查询里再 JOIN `backtest_run_id`（还要处理 null 与多 run 边界）。备选（按 `backtest_run_id == run_id` 过滤）：id 列表已明确，IN 更直接，且避免 link 前信号状态问题。

### D2: `signal_ids` 作为可选参数，保持向后兼容
`calculate_portfolio_holdings` 新增 `signal_ids: Sequence[int] | None = None`。`None` 表示未提供，保留全局 latest-wins（兼容非 run 调用方）；任何提供的集合（包括空集合）都严格按 id 限定。空集合直接返回无信号，而不构造 `IN ()` 或回退全局查询。理由：当前 backtest 调用必传；把空集合解释为“未提供”会让零信号 run 错读其他 run，违背隔离目标。

### D3: `run_backtest` 在已有 `signal_ids` capture 后传入；同时修改 `calculate_strategy_equity_curve` 签名
`run_backtest` 的 `signal_results`（来自 `generate_historical_strategy_signals` 返回）中每个 result 已包含 `strategy_signal_id`。需**在调用 `calculate_strategy_equity_curve` 和 `calculate_portfolio_holdings` 之前**从 `signal_results` 中提取 `signal_ids` 列表，并将该列表传入两个函数。`calculate_strategy_equity_curve` 签名同样新增可选的 `signal_ids` 参数并透传给内部的 `calculate_portfolio_holdings` 调用，使净值曲线使用的持仓快照与持久化的 holdings 来自同一组信号。

## Risks / Trade-offs

- [Risk] 传入空 `signal_ids` 列表（如调用方显式要求计算零信号 run）：若构造 `IN ()` 会产生方言相关行为。 → Mitigation：在查询 helper 中对空集合早返回 `{}`；它表示该 run 没有可用于持仓的成功信号，绝不回退全局查询。
- [Risk] 现有依赖全局 latest-wins 的测试 / 夹具失效。 → Mitigation：默认不传 `signal_ids` 保留原行为；新增按 id 过滤与重跑隔离测试。
- [Risk] `test_backtest_runner.py` 中 monkeypatched 的 `fake_calculate_portfolio_holdings` 和 `fake_calculate_strategy_equity_curve` 不接受新增的 `signal_ids` 参数 → Mitigation：在 mock 函数签名中增加 `signal_ids=None` 参数（不改变 mock 行为，仅接受并忽略）。
- [Trade-off] `signal_ids` 可选意味着若未来回测调用方错误传 `None` 会回退到不隔离旧行为——但当前 `run_backtest` 调用必须传其已验证的列表，且将由 wiring 测试覆盖；保留 `None` 仅为既有非 run 调用兼容。

## Migration Plan

无数据库迁移。纯代码改动 + 测试。部署：随常规发布；回滚：`git revert`。

## Open Questions

None blocking.
