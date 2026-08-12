# Proposal: reorganize-backtest-detail

## Why

Backtest Detail Overview 当前顺序为 run 元数据 → hero 卡 → 19 行比较矩阵 → 分布风险 → 收益稳定性 → CAPM → Equity Curve → Raw Parameters。Equity Curve 埋在 Metrics 之后，首屏看不到走势；19 行矩阵一屏放不下，核心指标淹没在 TE/IR/capture 等细节中；首屏被 7 行 run 元数据占据。用户无法在约 10 秒内判断一次 Backtest 是否值得继续研究。

本次重构**不增加任何回测计算能力**（后端零改动），仅按"快速判断结果 → 查看走势 → 比较 Benchmark → 深入风险分析 → 查看实验配置"的研究路径重新组织现有信息，并保留全部现有深度研究能力。

## What Changes

- **新增 Decision Summary 首屏区**：基于现有数据，强化 Strategy 相对 Primary Benchmark（`csi_300_buy_hold` 优先，缺失回退数组第一个）的 CAGR、Sharpe、Max Drawdown、Total Return 四项差异；CAGR/Total Return 差异直接使用后端已有的 `annualized_return_difference`/`total_return_difference` 字段，Sharpe/MaxDD 差异为前端展示层纯减法（`strategy.x - benchmark.x`），不引入任何新计算。
- **Decision Summary 结论徽章**：纯前端符号规则（≥2 项有效差异时判定），输出 Outperforming / Underperforming / Mixed，不加权重不算分；有效差异不足时降级为纯数字呈现。
- **Equity Curve 前移**：现有 EquityCurveChart 组件原样前移至 Decision Summary 之后，多曲线能力（Strategy + 全部 benchmark）复用。
- **Benchmark Comparison 拆分两级**：核心指标表（Total return / CAGR / Max drawdown / Volatility / Sharpe / Sortino / Calmar）保持展开；Advanced Metrics（最长回撤时长/峰谷/恢复、Tracking Error、Information Ratio、Up/Down Capture、两行 difference）折叠于 disclosure 内。Best 标记逻辑复用。
- **Deep Analysis 分区**：Distribution Risk（Strategy + 每只 benchmark）、Return Stability、CSI-300 CAPM 三个既有 disclosure 移入独立分区，各自保持 collapse，内容与语义不变。
- **run 元数据压缩**：首屏仅保留一行摘要（Strategy · 日期范围 · Status），完整 7 项详情沉入 Experiment Config 区。
- **Experiment Config 区**：`parameters_json` 由 raw JSON 改为人类可读键值（key → 标签 + 格式化，如 `risk_free_rate` 0.02 → "2.0%"），并保留 Raw Parameters 折叠展示原始 JSON。
- **组件拆分**：BacktestDetailPage.tsx（686 行）拆出 DecisionSummarySection / BenchmarkComparisonSection / DeepAnalysisSection / ExperimentConfigSection 四个独立组件文件，页面只做编排。

## Capabilities

### New Capabilities

无新增能力，全部为现有能力的需求变更。

### Modified Capabilities

- `backtest-results-ui`: Backtest Detail Overview 由"hero 四卡 + 单一大矩阵 + 三折叠 disclosure 平铺"重组为"Decision Summary 首屏 + Equity Curve 前移 + 两级 Benchmark Comparison + Deep Analysis 分区 + Experiment Config 收尾"；hero 四卡被 Decision Summary 取代，比较矩阵从"一个语义表"拆为"核心表 + Advanced 折叠"；run 元数据压缩为一行摘要；Parameters 区改为人类可读配置 + Raw 折叠。

## Impact

- **前端页面**：`apps/web/src/pages/BacktestDetailPage.tsx` 重排并瘦身（拆出 4 个 section 组件，各独立文件）。
- **新增组件**：`DecisionSummarySection.tsx`（含 primary 选取、差异计算、徽章判定）、`BenchmarkComparisonSection.tsx`（核心/Advanced 拆分）、`DeepAnalysisSection.tsx`（三 disclosure 组装）、`ExperimentConfigSection.tsx`（人类可读参数 + Raw 折叠）。
- **复用不改**：`EquityCurveChart`（`equityCurveChart.ts`）、`ComparisonMatrix` 的 Best 标记（`comparisonMatrix.ts`）、`DistributionRiskSection`、`ReturnStabilitySection`、`CapmSection`、`seriesColor`。
- **formatters**：`backtestFormatters.ts` 新增人类可读参数映射；`formatParameterSummary` 保留给 Raw 区。
- **样式**：`styles.css` 新增少量 class（run-summary / decision-summary / config-list 等），复用 metric-card / disclosure / comparison-matrix 现有样式。
- **测试**：`BacktestDetailPage.test.tsx`（1063 行）按组件迁移拆分，新增各 section 的测试覆盖（Decision Summary 徽章规则、primary 回退、Advanced 折叠、参数人类可读化）。
- **明确不改**：后端（API/计算/数据库）零改动；Signals tab 不动；`backtest-benchmark-comparison` 能力（后端基准计算语义）不动。
