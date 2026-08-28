# Proposal: reorganize-walk-forward-detail

## Why

Walk-forward Detail 当前首屏被 10 行 Execution 技术元数据（Provenance version、Evidence version、Config/Input checksum 等）占据，用户进入页面后无法在几秒内判断本次 Walk-forward 的整体 OOS 表现。页面还缺少运行状态展示、返回列表导航；全部指标以裸小数（`0.0234`）呈现，与 Backtest Detail 的百分比/ratio 展示语义不一致。本次重构**不增加任何计算能力（后端零改动）**，仅按"快速判断整体 OOS 表现 → 查看走势 → 深入证据 → 实验配置"的研究路径重新组织现有信息，并保留全部现有深度研究能力。

## What Changes

- **新增 Run Header 首屏区**：展示 Strategy、运行状态、测试日期范围、Window 数量，并提供返回 Walk-forward 列表的导航链接，取代现有 10 行 Execution 区；Walk-forward ID 标题由现有 page-heading 承担。（Status 为本次补上，当前页面无状态展示。）
- **新增 OOS Summary 首屏区**：6 张 headline metric 卡（Median/Mean Return、Median Sharpe、Max Drawdown、Positive Window Rate、Benchmark Outperformance Rate vs Primary Benchmark、Parameter Transition Rate max），全部来自现有 `evidence` 跨窗口聚合字段，不引入新计算。run 无 evidence 时不伪造数值：queued/running 沿用现有未决提示，failed 明确说明因失败而不可用。
- **Generalization Gap 与 Evidence Status 以事实说明行呈现**：Generalization Gap 使用真实语义"IS Sharpe − OOS Sharpe"（ratio 单位，非百分比），Evidence Status 取 `evidence.metrics.total_return.evidence_status` 并使用真实阈值"≥3 个有效 window 判定 sufficient"；不以卡堆叠底层字段。
- **格式化语义与 Backtest Detail 对齐**：Return / Max Drawdown 百分比化；Median Sharpe / Generalization Gap 保持 ratio 格式；Positive Window Rate / Outperformance Rate / Transition Rate 百分比化。深挖区（Aggregated evidence 卡、per-window 表）保留现有裸小数格式。
- **不增加总评分或 Pass/Fail 徽章**：页面只呈现可被事实支持的符号与数值，与 backtest 详情页的 sign-derived 徽章刻意区分。
- **Stitched OOS 前移**：现有 StitchedOosSection 原样前移至 OOS Summary 之后，首屏可见资本路径。
- **深挖区降级**：Aggregated evidence / Window evidence / Configuration & input provenance 沉底，内容与语义不变；Provenance 区技术字段保留但不再占据首屏。
- **组件拆分**：`WalkForwardDetailPage.tsx`（605 行）拆出 `WalkForwardRunHeaderSection` / `WalkForwardOosSummarySection`，纯函数（Primary Benchmark 选取、transition max 聚合、百分比格式化、Gen Gap 说明文本）放入 `walkForwardFormatters.ts` 便于单测。

## Capabilities

### New Capabilities
- `walk-forward-results-ui`: Walk-forward 详情页的展示需求正式化——Run Header + OOS Summary 首屏信息架构、跨窗口聚合指标的百分比/ratio 格式化语义、Generalization Gap 与 Evidence Status 的事实化呈现、研究路径分区顺序，以及"不设总分/Pass-Fail 徽章"的边界。

### Modified Capabilities

无。walk-forward 详情页 UI 此前无独立 capability；`walk-forward-evaluation-history`（后端持久化/查询）与 `walk-forward-runner`（执行）行为均不变。

## Impact

- **前端页面**：`apps/web/src/pages/WalkForwardDetailPage.tsx` 重排并瘦身（拆出 2 个 section 组件 + 1 个纯函数文件）。
- **新增组件**：`WalkForwardRunHeaderSection.tsx`（Header + 返回列表导航）、`WalkForwardOosSummarySection.tsx`（6 卡 + 事实说明行 + Primary Benchmark 选取）。
- **新增 helper**：`walkForwardFormatters.ts`（`resolvePrimaryBenchmark`、`aggregateTransitionRate`、百分比格式化适配、Gen Gap 说明文本）。
- **复用不改**：`StitchedOosSection`（原样移动）、`EvidenceSection` / `WindowSection` 内部实现（仅调整顺序与标题层级）、`formatRatioAsPercent` 等 `utils/formatters`；`ProvenanceSection` 仅顶部新增 Execution 元数据子区（承接 version/timestamps），其余内容不变。
- **per-window 表**：`WindowSection` 内的格式化本次**不改**（属深挖区，避免范围膨胀）。
- **样式**：`styles.css` 新增少量 class（run-header / oos-summary-grid / fact-line 等），复用 metric-card / holdings-section / run-summary 现有样式。
- **测试**：`WalkForwardDetailPage.test.tsx` 按组件迁移，新增 `WalkForwardOosSummarySection.test.tsx`、`walkForwardFormatters.test.ts`（Primary 回退、transition max 聚合边界与并列规则、queued/running/failed 无 evidence 状态、格式化断言）。
- **明确不改**：后端（API/计算/数据库）零改动；`walk-forward-evaluation-history` / `walk-forward-runner` 能力不动；`backtest-results-ui` 及 `reorganize-backtest-detail` 变更不受影响。
