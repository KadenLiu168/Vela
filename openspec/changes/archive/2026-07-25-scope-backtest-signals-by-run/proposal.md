## Why

回测不可复现：同 `config + 区间`，Run1(−19.4%) 与 Run2(−26.4%) 差 7pt。根因之一是持仓计算读取信号时走**全局 latest-wins**（`portfolio_holdings._latest_successful_signals_by_date` 按 `strategy_id + config_version + signal_date` 取最新一条，**不按 backtest_run 过滤**），重跑追加的信号行互相串味，使持仓/净值算出不同 run 信号的拼盘值。`2026-07-19-add-signal-provenance` 已建立 `backtest_run_id` + `link_signals_to_backtest_run()` 钩子，且 `run_backtest` 已 capture `signal_ids`，但读取侧从未使用——本变更接上这缺失的一半。

## What Changes

- 修改 `calculate_portfolio_holdings` 的信号读取：从"全局按 `signal_date` 取最新"改为"**只认本次回测 run 生成的 `signal_ids`**"（`WHERE StrategySignal.id IN (本次 run 的 signal_ids)`）。传入空集合表示该 run 没有可用信号，返回空持仓，绝不回退全局查询。
- 修改 `calculate_strategy_equity_curve` 签名：同样接受可选的 `signal_ids` 并透传给内部 `calculate_portfolio_holdings` 调用，确保净值曲线使用的持仓快照与持久化 holdings 来自同一组信号。
- `run_backtest` 将已 capture 的 `signal_ids`（从 `signal_results` 提取）传入持仓计算和净值曲线计算，使持仓/净值只依赖本 run 的信号。
- 重跑采用**新 run 追加**（不覆盖）：追加的新 run 带自己的 `signal_ids`，与历史 run 互不干扰。
- **不改动** `strategy_equity_curve` 的核心净值计算逻辑（仅修改签名以透传 `signal_ids`，不修改计算细节）。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `portfolio-holdings`: 持仓计算的信号来源须限定在调用方提供的**本次回测 run 的 `signal_ids`** 内，而非全局 latest-wins。
- `backtest-execution`: `run_backtest` 须在调用 holdings/equity 计算之前提取 `signal_ids`，并将本次生成的 `signal_ids` 传递给持仓/净值计算，确保结果仅依赖本 run 信号。

## Impact

- Affected code:
  - `packages/core/src/vela_core/portfolio_holdings.py`（`_latest_successful_signals_by_date` 查询改为按 `id` 过滤；`calculate_portfolio_holdings` 签名新增 `signal_ids: Sequence[int] | None` 参数）。
  - `packages/core/src/vela_core/strategy_equity_curve.py`（`calculate_strategy_equity_curve` 签名新增 `signal_ids: Sequence[int] | None` 参数，透传给 `calculate_portfolio_holdings`）。
  - `packages/core/src/vela_core/backtest_runner.py`（在生成后提取 `signal_ids` 后传入持仓计算和净值曲线计算）。
- Affected tests:
  - 新增"重跑追加 run 互不污染"的回归测试：同 config、同一数据库内两次 run；第二次运行在一个 rebalance 日期生成失败信号时，不能读取第一次运行在该日期的成功信号。
  - 新增按 `id` 过滤和空集合语义的单元测试（传入的 `signal_ids` 外信号不进入持仓；空集合不回退全局）。
- 无 API / CLI / 前端 / 数据库迁移变更。
- 用户将重置数据库，存量重复 / 无 link 的旧信号无需清洗。
