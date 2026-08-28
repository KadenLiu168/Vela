# Design: reorganize-walk-forward-detail

## Context

Walk-forward Detail 现状（`apps/web/src/pages/WalkForwardDetailPage.tsx`，605 行）自上而下为：page-heading（仅 "Walk-forward #id"）→ RunSummary（"Execution"，10 行技术元数据，**无 Status**）→ EvidenceSection（Aggregated evidence：8 张 metric-card + positive-window rate + generalization gap + benchmark evidence + parameter stability + tail distribution）→ StitchedOosSection（资本路径，首屏不可见）→ ProvenanceSection（Configuration & input provenance + 3 个 raw JSON 块）→ WindowSection（per-window 表）。

问题：首屏被与技术决策无关的 Execution 元数据占据；无运行状态展示；无返回列表导航；全部指标以裸小数 `toFixed(4)` 呈现（如 `0.0234`），而 Backtest Detail 对 Total return / CAGR / MaxDD 用 `formatRatioAsPercent`（`2.34%`）、Sharpe 用 ratio 格式——两页展示语义不一致。

关键数据约束（来自 `apps/web/src/api/client.ts` 类型 + `packages/core/src/vela_core/walk_forward/report.py`）：
- `evidence.metrics.*` 为跨 window 聚合的 `WalkForwardMetricSummary`（mean/median/min/max/std/valid_count/window_count/evidence_status），覆盖 total_return / annualized_return / sharpe_ratio / max_drawdown / volatility / sortino / calmar / longest_drawdown_duration_sessions。
- `evidence.positive_window_rate` / `evidence.benchmarks[key].outperformance_rate` 为 `WalkForwardRateSummary`（value/numerator/denominator/valid_count/window_count/evidence_status）。
- **Generalization Gap = IS − OOS Sharpe**（`report.py:generalization_gap`，逐 window 的 `train_sharpe - oos_sharpe` 再聚合）——**Sharpe 差值，ratio 单位，不是百分比**；gap 越大 = 选参表现好于样本外越多 = 泛化越弱。
- **Evidence status 阈值**：`valid_count >= 3`（`MINIMUM_EVIDENCE_COUNT=3`，`evidence.py`）→ `sufficient`，否则 `insufficient_evidence`。
- `parameter_stability` 按参数名 keyed（`best_combo` 中出现的参数），每个参数独立 `transition_rate = transition_count/comparison_count`；**comparison_count 仅在参数连续出现于相邻 window 时递增**，不同参数基数不同。
- `stitched_oos.total_return` 为拼接路径的累计收益，`status` 可为 `unavailable_non_contiguous_windows`。
- `run.status`（queued/running/success/failed）与 `run.window_count` 在 `WalkForwardRunSummary` 中可用。
- 现有 spec：walk-forward 详情页 UI 无独立 capability（`walk-forward-evaluation-history` 仅覆盖后端持久化/查询）。

## Goals / Non-Goals

**Goals:**
- 首屏在几秒内回答"整体 OOS 表现怎么样、稳定不稳定、是否优于基准"，信息架构按研究路径重排：Run Header → OOS Summary → Stitched 走势 → 深挖证据 → 实验配置。
- 格式化语义与 Backtest Detail 对齐：Return / MaxDD 百分比，ratio 指标（Median Sharpe / Gen Gap）保持 ratio，rate 指标（Win rate/Outperform/Transition）百分比化。
- Generalization Gap 与 Evidence Status 以事实化、带辅助说明的方式呈现，而非堆叠底层字段。
- 不引入任何后端计算；纯前端信息架构与展示层重构。
- 组件拆分 + 纯函数 helper，保证可测性。

**Non-Goals:**
- 不新增/修改任何后端计算、API 字段、数据库结构。
- 不增加总评分或 Pass/Fail 徽章（与 `reorganize-backtest-detail` 的 sign-derived 徽章刻意区分——walk-forward 只呈现可被事实支持的符号与数值）。
- 不改 `StitchedOosSection`、`EvidenceSection` / `WindowSection` 的内部实现（仅调整顺序与标题层级）。`ProvenanceSection` 唯一允许的变更是顶部新增 "Execution" 元数据子区（承接从首屏迁入的 version/timestamp 字段），其余内容不变。
- **不格式化深挖区指标**——Aggregated evidence 的 MetricCard 与 per-window 表（`WindowSection`）保留裸小数现状，本次避免范围膨胀。
- 不展示策略参数本体（`best_combo` 在 evidence 里有 `selected_parameters`，但 headline 不展示具体参数值本体，只展示 transition 统计）。

## Decisions

### D1: Run Header 取代 Execution 区
新增 `WalkForwardRunHeaderSection`，作为 detail body 的首个内容区（header 语义元素，无独立 h2）。现有 `page-heading` 保持不变，其 h1 继续承载标题 `Walk-forward #id`——标题在 loading/not-found/error 状态下也保持可见，与 backtest detail 的 page-heading 惯例一致。Run Header 包含：
- 返回列表导航：`<Link to="/walk-forwards">← Back to Walk-forward history</Link>`（当前页面无任何返回导航；`/walk-forwards` 路由已由 `web-client-routing` 定义）。
- 一行 run 摘要：复用 backtest detail 的 `.run-summary` 样式：`Strategy · <date range> · <window_count> windows`。
- 状态徽标：`run.status`（success/failed/queued/running），纯展示，复用 `.run-summary-status` 样式。

现有 `panel-primary` 强文本 "Persisted evaluation evidence" 删除：其语义由 Run Header 与 OOS Summary 的标题承担，不重复渲染。

完整 10 项 Execution 元数据不再占据首屏：Strategy / date range / window count 压缩为摘要行；provenance/evidence version、started/finished/created timestamps 迁入 Provenance 区顶部新增的 "Execution" 元数据子区（h3）；config/input checksums 已由 ProvenanceSection 展示，不重复迁入。EvidenceSection / WindowSection 内部实现不变。

**备选**：保留 Execution 区但折叠 —— 首屏仍被折叠标题占据，且用户诉求是"先判断 OOS 表现"，折叠的 Execution 与决策无关，弃用。

### D2: OOS Summary = 6 卡 + 1 事实说明行
`WalkForwardOosSummarySection` 呈现（全部来自现有 `evidence` 字段，无新计算）：

| 卡 | 数据来源 | 格式化 |
|---|---|---|
| Median return（卡内 Median 主 + Mean 副） | `evidence.metrics.total_return` | 百分比 |
| Median Sharpe | `evidence.metrics.sharpe_ratio.median` | ratio（2 位） |
| Max Drawdown | `evidence.metrics.max_drawdown.median` | 百分比 |
| Positive Window Rate | `evidence.positive_window_rate` | 百分比 + `(numerator/denominator)` |
| Benchmark Outperformance | primary benchmark 的 `outperformance_rate` | 百分比 + `(numerator/denominator)` + 基准名 |
| Parameter Transition（max） | `evidence.parameter_stability` | 百分比 + 参数名 + comparison 上下文 |

事实说明行（卡下方，非卡）：
- **Generalization Gap**：`IS Sharpe − OOS Sharpe`，呈现 median 值 + 辅助说明"正值说明选参表现好于样本外，差距越大泛化越弱"（ratio 格式，非百分比）。
- **Evidence Status**：取 `evidence.metrics.total_return.evidence_status`（headline 指标家族代表；evidence 文档没有整体 status 字段，各指标自身的 status 在深挖区仍可见）+ 辅助说明"≥3 个有效 window 判定 sufficient"。
- **无 evidence 状态**：`evidence === null` 时（API 对 queued/running **以及 failed** run 均返回 null evidence，`walk_forward_router.py`）不渲染卡、不伪造数值：
  - queued/running：沿用现有提示 "Evidence is unavailable until this {status} run reaches a terminal state"。
  - failed（terminal）：改为 "Evidence is unavailable because this run failed."——原文案对 failed 状态是错误陈述，随本区提升到首屏必须修正；错误详情 `error_message` 由深挖区 EvidenceSection 继续展示。

### D3: Primary Benchmark 选取（沿用 backtest reorg 的优先规则）
`resolvePrimaryBenchmark(benchmarks)`：`csi_300_buy_hold` key 优先，缺失回退 `evidence.benchmarks` 对象的第一项（以插入序为准），无基准则 Outperformance 卡显示 n/a。封装为纯函数可单测。选取规则与 `backtestFormatters.resolvePrimaryBenchmark` 一致，但输入形状不同（walk-forward 为 `Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>`，backtest 为数组），独立实现；展示名复用现有 `TAIL_OWNER_LABELS` 映射（"CSI 300 buy-and-hold" / "Equal-weight monthly"）。

### D4: 双 Total Return 语义并存且命名区分
- OOS Summary 主卡用 `evidence.metrics.total_return` 的 median/mean（跨 window 聚合族，与 Median Sharpe、Win Rate 同族，语义自洽，且 stitched unavailable 时仍可靠），卡上标注 "median across {window_count} windows"。
- `stitched_oos.total_return` 继续由 StitchedOosSection 原样展示（"Cumulative total return" 标签不变）——前者回答"整条路径走完的结果"，后者回答"典型窗口表现"。两者都首屏可见。

### D5: Generalization Gap 说明文本
纯函数 `generalizationGapText(summary)` 生成辅助说明（不把 `mean/median/min/max/std/valid_count/evidence_status` 原始字符串直接堆给用户，而是呈现 median 值 + 一句人话说明）。文案以 `report.py` 的真实定义（IS − OOS Sharpe）为准。

### D6: 组件拆分
```
apps/web/src/pages/WalkForwardDetailPage.tsx       ← 编排：数据加载 + 状态机 + 组装 section
apps/web/src/pages/WalkForwardRunHeaderSection.tsx ← 新：返回导航 + 状态 + run 摘要
apps/web/src/pages/WalkForwardOosSummarySection.tsx ← 新：6 卡 + 事实行 + primary 选取 + 无 evidence 状态
apps/web/src/pages/StitchedOosSection.tsx           ← 现有：原样移动为独立文件（当前内联在页面中）
apps/web/src/pages/walkForwardFormatters.ts         ← 新：resolvePrimaryBenchmark / aggregateTransitionRate /
                                                        formatPercentNumber / generalizationGapText
```
纯函数放 `walkForwardFormatters.ts` 与组件分离，便于单测。`EvidenceSection`/`WindowSection` 保持页面内函数（不改内部实现）；`ProvenanceSection` 保持页面内函数，仅新增顶部 "Execution" 元数据子区（见 D1）。

### D7: 百分比格式化适配
现有 `formatRatioAsPercent` 接受 `string | null`（backtest 字段为 string），而 `WalkForwardMetricSummary.mean/median` 是 `number | null`。新增 `formatPercentNumber(value: number | null, digits = 2)`：`value * 100` 后 `toFixed(digits)` + `%`，null → `n/a`，不修改现有 `formatRatioAsPercent`。Return/MaxDD 用它；rate 类（win rate/outperform/transition）用 `value * 100` 百分比 + 括号计数。Sharpe/Gen Gap 保持 ratio（`toFixed(2)`，沿用 backtest detail 的 Sharpe 展示精度）。

### D8: 测试策略
- `WalkForwardDetailPage.test.tsx` 瘦身为编排/顺序断言（Header 在前、OOS Summary 次之、Stitched 紧随）。
- 新增 `WalkForwardOosSummarySection.test.tsx`（primary 回退、transition max 聚合、Gen Gap 文本、evidence null 的 queued/running 未决状态与 failed 状态、格式化断言）。
- 新增 `walkForwardFormatters.test.ts`（`resolvePrimaryBenchmark` 回退、`aggregateTransitionRate` 的 count 基数防御、`formatPercentNumber` 边界）。
- 沿用仓库惯例规避 fake timers 坑。

## Risks / Trade-offs

- **[transition max 可能被低比较基数放大误导]** → headline 卡必须带 comparison 上下文（`comparison_count` 数），`aggregateTransitionRate` 返回 `{ rate, parameterName, comparisonCount }`，spec 强制要求展示计数。多个参数并列最大值时按 `parameter_stability` 的插入序取第一个——后端 `parameter_stability()` 以 sorted 参数名构建 dict（`report.py:312`），JSON 插入序确定，行为可测。
- **[双 Total Return 语义可能混淆用户]** → OOS Summary 卡明确标注 "median across N windows"，Stitched 区保留 "Cumulative total return" 标签；spec 用措辞区分。
- **[Gen Gap 是 Sharpe 差值而非百分比，易被格式化语义误伤]** → 保持 ratio 格式 + 专属说明文本，不并入百分比卡；spec 明确其单位语义。
- **[深挖区与首屏格式不一致]** → 本次明确 Non-Goal：Aggregated evidence 的 MetricCard（如 "Median: 0.0234"）与 per-window 表保留裸小数现状；如后续要求全页统一，单独评估（记入 Open Questions）。
- **[walk-forward UI 无既有 spec，本 change 新建完整 spec]** → 以目标状态（重构后）为基线描述需求，场景以可测方式约束顺序与格式化；评审以此为据。

## Migration Plan

纯前端信息架构重构，无数据迁移、无 API 变更。回滚 = revert 对应 commit。实施按 D6 组件拆分顺序推进：先建纯函数 helper + 单测，再建 Run Header 与 OOS Summary，再移动 StitchedOosSection，最后编排页面，每步保持页面可编译、测试通过。

## Open Questions

1. 深挖区（Aggregated evidence 的 MetricCard 与 per-window 表 `WindowSection`）的格式化是否应在后续单独 change 中统一为百分比？本次明确不做。
2. 状态徽标的视觉样式（success 绿 / failed 红）是否需要区分色？现仅计划纯文本/中性样式，避免引入"颜色即结论"的误导。
