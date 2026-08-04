## Why

Vela 的 Walk-forward 报告目前只聚合 OOS CAGR 和 Sharpe，无法系统回答收益是否稳定、最差窗口风险如何、参数选择是否频繁漂移，以及策略在多少个 OOS 窗口真正跑赢两条固定基准。第一阶段需要形成可审计的证据报告，而不是用未经产品验证的阈值自动输出 `pass/fail`。

## What Changes

- 补全每个 OOS 窗口的策略 total return、CAGR、Sharpe、maximum drawdown 和 volatility，并对每项指标报告有效样本数及描述统计。
- 增加 OOS 正收益窗口比例，以及分别相对同池月度等权和 CSI 300 买入持有基准的跑赢窗口比例。
- 将每条基准的相对 total return/CAGR 汇总从仅有均值扩展为完整描述统计、总窗口数、有效窗口数和证据状态。
- 增加 `train_sharpe - oos_sharpe` 泛化差值，以及每个搜索参数的取值频数、相邻窗口切换次数和切换率。
- 当任一结论性统计少于三个有效 OOS 窗口时标记 `insufficient_evidence`，但仍生成完整报告；`sufficient` 仅表示达到最低样本数，不代表窗口独立、统计结论充分或策略通过。
- 修正 Walk-forward 主规格中已经失效的可选 `baseline` 用语，使事务和报告要求与现有固定双基准契约一致。
- 增加使用测试自有真实小型数据库执行完整参数搜索和 OOS 计算的集成契约测试，减少现有报告/runner 测试对 mock 指标的依赖。
- 明确不连续拼接 OOS 净值曲线；不模拟跨窗口持仓、现金或参数切换交易成本。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `walk-forward-runner`: 扩展逐窗口字段、OOS 聚合、双基准胜率、IS/OOS 泛化差值、参数稳定性和证据充分性契约，并移除规格中残留的旧 baseline 语义。

## Impact

- 影响 `packages/core/src/vela_core/walk_forward/` 的报告数据结构、聚合逻辑、文本输出和 runner 结果映射。
- 影响 Walk-forward 核心测试及测试自有 SQLite 集成数据；不写入或迁移默认 `vela.db`。
- 不新增数据库表或迁移，不改变普通回测 API/Web，不持久化 Walk-forward 报告，也不增加第三方依赖。
