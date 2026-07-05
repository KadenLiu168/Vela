## Why

策略的调仓频率目前硬编码为「每周」(每 ISO 周的最后一个交易日),无法在不改代码的情况下调整。对于月度调仓的策略研究、回测和实盘运行,这是一个明显的限制。本次需求新增「每月」作为第二种可选频率,使其可在配置文件中切换。

## What Changes

- 新增 `generate_monthly_rebalance_dates` 函数,与现有 `generate_weekly_rebalance_dates` 平行,语义为「每个自然月取该月最后一个交易日」。
- 在 `packages/core/src/vela_core/rebalance_dates.py` 中新增内部 dispatcher `generate_rebalance_dates(trading_dates, *, frequency)`,按 `frequency` 字段分发到 weekly / monthly 实现。
- 在 `packages/core/src/vela_core/strategy_config.py` 中新增 `RebalanceConfig` Pydantic 模型,`frequency: Literal["weekly", "monthly"]`,默认 `"weekly"`,挂到 `StrategyConfig` 上。
- 在 `config/strategy_v1.yaml` 中新增 `rebalance` 子段,显式声明 `frequency: weekly`(显式优于隐式)。
- `packages/core/src/vela_core/strategy_signal_generation.py` 中的 `generate_historical_strategy_signals` 改用 dispatcher,由 `config.rebalance.frequency` 决定。
- `packages/core/src/vela_core/__init__.py` 导出新函数 `generate_monthly_rebalance_dates`。
- 不引入 biweekly 等其他频率(YAGNI)。
- 不改变现有 `weekly-rebalance-dates` 能力(weekly 行为完全保留)。
- 自动惠及回测链路(回测与信号生成共用同一段调仓日期生成代码,本次改动不会拆出独立的「回测 rebalance 逻辑」)。

## Capabilities

### New Capabilities

- `monthly-rebalance-dates`: 从交易日序列中按「每个自然月最后一个交易日」语义生成月频调仓日期。

### Modified Capabilities

- `strategy-configuration`: 策略配置文件需要支持新增的 `rebalance` 参数组(包含 `frequency` 字段,允许 weekly / monthly,默认 weekly)。
- `strategy-signal-generation`: 历史信号生成步骤需要按 `config.rebalance.frequency` 决定调仓日期序列,而不是硬编码 weekly。

## Impact

- 代码改动:
  - `packages/core/src/vela_core/rebalance_dates.py` — 新增 `generate_monthly_rebalance_dates` 和 `generate_rebalance_dates` dispatcher;保留 `generate_weekly_rebalance_dates` 签名
  - `packages/core/src/vela_core/strategy_config.py` — 新增 `RebalanceConfig` 模型并接入 `StrategyConfig`
  - `packages/core/src/vela_core/strategy_signal_generation.py` — 调用点改用 dispatcher
  - `packages/core/src/vela_core/__init__.py` — 导出新函数
  - `config/strategy_v1.yaml` — 新增 `rebalance` 子段
- 测试改动:
  - `packages/core/tests/test_rebalance_dates.py` — 月频日期生成的边界用例(空、跨年、月初/月末、稀疏交易日)
  - `packages/core/tests/test_strategy_config.py`(若存在) — `RebalanceConfig` 校验场景
  - `packages/core/tests/test_strategy_signal_generation.py` — 验证 dispatcher 按 `config.rebalance.frequency` 工作
- 调用链:
  - 信号生成(CLI / 实时):受配置驱动
  - 回测(`backtest_runner.run_backtest` → `generate_historical_strategy_signals`):自动同步支持月频
- 不破坏向后兼容:旧 yaml 不写 `rebalance` 字段时默认 weekly,行为与现在完全一致。
