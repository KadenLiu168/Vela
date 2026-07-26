## Why

当前权益曲线每天使用信号的 `target_weight` 计算收益，等价于在两个真实信号之间仍每日无成本地再平衡至目标权重。这个隐含行为会路径依赖地扭曲多资产策略的收益、波动、换手和 Sharpe，并会不均匀地污染按 Sharpe 比较 `top_n=1..3` 候选的 walk-forward 选参结果。

## What Changes

- **BREAKING**: 将权益曲线从「每日固定目标权重」改为「归一化持仓价值与现金状态」，使实际权重在两个调仓信号之间随市场收益自然漂移
- 继续让区间起点的实际持仓获得 close-to-close 收益，并仅在 `strategy_signal_id` 变化时按新目标权重执行收盘调仓
- 使用调仓前实际权重计算换手，并在市场收益之后按乘法顺序扣除交易成本
- 让权益曲线点携带实际现金、市场价值和持仓权重，供 backtest runner 持久化同一份计算状态
- 在 `positions_json` 中保留 `target_weight` 并增加 `actual_weight`，同时使 `cash`、`market_value` 和 `total_assets` 反映实际归一化组合状态
- 在回测参数中记录 `equity_model_version: "drift_v1"`，使修正前后的不可比结果可识别
- 保留当前信号生成、T+1 生效、逐区间 forward-adjusted 收益、缺价收益中性和数据库 schema

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `strategy-equity-curve`: 使用持续的持仓价值和现金状态计算自然权重漂移，并基于实际权重、信号边界和正确的成本复合顺序生成净值
- `backtest-execution`: 持久化权益计算产生的实际组合状态和权益模型版本，而不是从每日目标持仓重新构造归一化快照

## Impact

- **核心代码**: `packages/core/src/vela_core/strategy_equity_curve.py`、`packages/core/src/vela_core/backtest_runner.py` 和新增公开状态类型所需的 `packages/core/src/vela_core/__init__.py` 导出
- **公开接口**: `StrategyEquityCurvePoint` 增加可选的 immutable portfolio-state payload；现有仅使用 `trade_date`、`net_value` 和 `daily_return` 的指标调用保持兼容，权益计算产生的点始终携带完整状态
- **测试**: 权益曲线、交易成本、runner 持久化和代表性 backtest/walk-forward 回归测试
- **持久化契约**: 不迁移表结构；`positions_json` 增加实际权重字段，`parameters_json` 增加权益模型版本
- **下游指标**: 总收益、年化收益、波动率、Sharpe 和最大回撤数值可能变化；`top_n=1` 满仓单资产路径应保持等价
- **历史数据**: 旧结果保持不变且不可与 `drift_v1` 直接比较；本 Change 不自动标记、删除或重跑既有数据库记录
