## Why

Vela 已能比较策略与两条固定基准的收益差，但仍无法衡量主动收益的稳定程度、下行波动、收益相对回撤的效率或资金处于回撤中的时间。需要在保持现有 CAGR、Sharpe、volatility 和负数 MaxDD 契约不变的前提下，补充精确定义且可审计的主动与下行风险指标。

## What Changes

- 新增相对每条固定基准的 Tracking Error 和 Information Ratio，基于完全对齐的日主动收益并采用 252 交易日年化；统计中间值不量化，仅最终公开 Decimal 量化到六位。
- 新增 Sortino ratio，以每次回测已记录的年化 `risk_free_rate` 作为 MAR，按 `risk_free_rate / 252` 计算日目标收益和总体下行偏差。
- 新增 Calmar ratio，定义为 calendar-time CAGR 除以最大回撤绝对值；零回撤或缺少 CAGR 时返回空值。
- 新增最长回撤持续期，按官方交易日索引间隔计算并保留 peak、trough、可空 recovery 日期；未恢复区间持续到回测结束。
- 所有进入指标阶段的回测都计算策略绝对风险指标；benchmark-enabled normal/partial 与 selected OOS 回测还计算两条基准及对应 TE/IR，隔离的 Walk-forward training trial 只在训练快照中保留策略指标。历史记录不回填，新列保持 `NULL`。
- 在所有上述回测的参数快照中增加固定的 `performance_metric_version`，确保指标语义可追溯；保持当前 `risk_free_rate` 为显式、可复现的固定评价假设，不自动联网更新。
- 将新增指标扩展到回测运行/详情 API、CLI/导出报告、Backtest Detail 和强化后的 Walk-forward OOS 证据报告；不扩展 Dashboard 摘要。
- 明确不增加 Alpha、Beta、capture ratio、VaR/CVaR 或动态无风险利率数据源，也不修改 CAGR 为 252 日口径。

## Capabilities

### New Capabilities

- `active-and-downside-risk-metrics`: 定义 TE、IR、Sortino、Calmar 和最长回撤持续期的输入、公式、边界与版本语义。

### Modified Capabilities

- `strategy-equity-curve`: 从策略日净值曲线计算并返回 Sortino、Calmar 和最长回撤持续期。
- `backtest-benchmark-comparison`: 为两条固定基准计算同口径下行指标，并计算策略相对每条基准的 TE/IR。
- `backtest-execution`: 保留 benchmark 输入的 pre-signal fail-fast，在策略曲线完成后计算主动指标，并在 normal/partial、隔离 training 与 selected OOS 路径中按各自事务边界版本化新增指标。
- `backtest-run-model`: 增加策略和 benchmark 新指标字段，保持历史 run/benchmark 可读且新字段为空。
- `http-api-service`: 在回测运行与详情响应中公开新增策略和 benchmark 指标。
- `cli-database-initialization`: 在回测 CLI 与导出报告中显示新增指标和回撤区间。
- `walk-forward-runner`: 将选中 OOS 的新增风险指标纳入逐窗口和证据聚合，不改变窗口隔离语义。
- `web-frontend-app`: 在 Backtest Detail 中展示新增策略/benchmark 指标及清晰的 252D、MAR 和回撤持续期标签。

## Impact

- 影响 `packages/core` 的指标计算、benchmark、runner、持久化、SQLAlchemy 模型、Alembic migration、Walk-forward 和报告代码；新增不可变指标类型及计算函数沿用现有 `vela_core` 根包公开方式。
- 扩展 FastAPI schema/router、CLI 输出、React API 类型和 Backtest Detail；新增响应字段但不重命名或重算现有字段。
- 历史数据不回填，旧记录新增字段返回 `null`；验证只使用 Alembic 管理的测试数据库，不迁移默认 `vela.db`。
- 不新增第三方依赖，不改变策略交易或基准执行模型。
