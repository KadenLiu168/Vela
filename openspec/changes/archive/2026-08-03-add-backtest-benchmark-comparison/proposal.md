## Why

Vela 的回测目前只提供策略自身的收益与风险指标，无法回答策略是否优于同一可投资池的等权配置或沪深 300 风险暴露。Walk-forward 现有的等权比较还会继承基础策略频率，不能表达固定的月度等权基准。

## What Changes

- 为每次普通回测新增两个固定且可审计的参考基准：同池等权月度再平衡组合，以及使用 `SSE:510300` 的沪深 300 ETF 买入持有组合。
- 为基准保存日净值曲线和与策略相同口径的总收益、calendar-time CAGR、最大回撤、252D 年化波动率及 Sharpe；输出相对每条基准的总收益和 CAGR 差值。
- 基准首日建仓不计成本，与当前策略一致；等权基准只在后续月末官方交易日调仓并应用当前策略的 `transaction_cost_bps`，买入持有基准不发生后续调仓成本。
- 要求策略及两条基准在整个官方交易日区间具有完整价格；`SSE:510300` 不存在、未激活或缺价时，回测 fail-fast，不缩短比较区间。
- 在回测详情 API、CLI/导出报告和回测详情页面提供双基准结果与三条曲线；不扩展 Dashboard 摘要或回测列表。
- 为每个 Walk-forward OOS 窗口计算并报告双基准比较；训练期参数搜索不计算基准。移除现有可选 equal-weight `baseline` 配置/字段，避免其频率语义与固定月度基准冲突。
- **BREAKING**：Walk-forward 配置不再接受 `baseline`，其结果和文本报告由固定双基准字段替代。

## Capabilities

### New Capabilities
- `backtest-benchmark-comparison`: 为单次回测和 Walk-forward OOS 提供固定双基准、完整日期校验、同口径指标、相对收益比较及持久化读取契约。

### Modified Capabilities
- `backtest-execution`: 回测执行须在普通运行时计算并持久化双基准，且训练期可显式跳过基准。
- `backtest-run-model`: 回测结果持久化与读取须包括每个运行的基准指标和净值曲线。
- `cli-database-initialization`: 回测 CLI 摘要与导出报告须显示双基准及相对收益比较。
- `http-api-service`: 回测运行和详情响应须提供双基准指标、曲线和相对收益差值。
- `walk-forward-runner`: OOS 结果与报告须提供固定双基准比较，而非配置化等权 baseline。
- `web-frontend-app`: 回测详情须显示策略和双基准的比较信息及三条净值曲线。

## Impact

- 影响 `packages/core` 的回测计算、Walk-forward、SQLAlchemy 模型和 Alembic migration；既有历史回测行保持可读取，但不会具有新基准结果。
- 扩展 FastAPI 回测响应、CLI 文本输出、React 回测详情数据类型与图表呈现。
- 不增加第三方依赖、不写入默认 `vela.db` 进行验证，也不引入 TE、Information Ratio、Alpha 或 Beta。
