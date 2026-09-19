# Design: build-decision-first-research-workbench

## Context

Dashboard 是 eager 路由（`web-route-code-splitting` 要求它保持 eager），其代码计入 40,000 raw bytes 的 eager 预算。本次实测：eager 39,964、lazy 69,995、initial 269,151、total 339,146——三个带都只剩几十到几百字节。因此本设计的第一约束不是"能不能画出来"，而是"如何在几乎为零的预算余量里把首屏换成决策路径"。

后端侧，`dashboard_aggregation` 已经是"首屏聚合读模型"（`dashboard-aggregation` capability），本次扩展沿用该定位，而不是让前端为每一层各打一次详情接口。

## Goals / Non-Goals

**Goals**

- 首屏按五层顺序回答：数据是否当前 → 该持有什么 → 策略是否有效 → 是否稳健 → 证据在哪。
- 每一层只呈现 API 已发布的值；不在浏览器里做金融计算。
- 既有面板、动作、格式化语义、契约零丢失。

**Non-Goals**

- 不新增路由、不新增导航项（L5 只链接既有路由）。
- 不引入评分、评级、pass/fail、阈值告警。
- 不改动策略/回测/walk-forward 的计算与持久化。
- 不搬迁 Dashboard 上的既有 action（`web-frontend-app` 明确要求它们在 Dashboard）——只调整它们在页面中的顺序。

## Decisions

### D1：决策层放在 Dashboard，而不是新开 `/research` 路由

**选择**：Dashboard 自身重组。

**理由**：Dashboard 是默认落地页；把决策路径放到第二个页面等于承认落地页不是工作台。同时新路由会增加导航项与一个 lazy chunk（lazy 预算仅剩 5 字节），收益为负。

**代价**：需要修订 `web-frontend-app` 中 "Dashboard SHALL remain unchanged by this Change" / "Dashboard has no WF card" 的既有场景。修订方式是显式 delta：Dashboard 允许呈现**紧凑的 OOS 稳健性层**，但保持"完整 walk-forward 证据只在专用列表/详情流中"的实质约束。

### D2：状态事实（L1）在浏览器里只做日期比较，不做数值重算

**选择**：L1 的每一行是"某个 API 日期 + 它与另一个 API 日期的先后/间隔"。

**理由**：判断"信号是否落后于数据"必须比较 `latest_signal.signal_date` 与 `market_data.latest_trade_date`，两者都是 API 已发布的日期。这不是金融计算（`strategy-equity-curve` 等对"浏览器重算"的禁止针对的是收益率/波动/曲线这类派生量）。

**实现约束**：

- 滞后天数是**日历日差**，用于表达"多久之前"，不声称交易日口径；文案必须写成日历日（`N calendar days`）而不是 sessions，避免与项目的交易日语义混淆。
- 不使用 `new Date()` 之外的时钟来源；"今天"只在有 `latest_trade_date` 时用于表达数据滞后。
- 行文只陈述事实与推断出的**动作**（如 "Generate a new signal"），不给出好坏判断。

**替代方案**：让后端返回 `is_stale` 布尔。否决——"多旧算旧"是研究者的判断策略（周频 vs 月频），把它固化到后端会把一个显示口径变成一个金融语义。

### D3：L3 复用既有的 sign-only 差值语义，但不复用 `DecisionSummarySection` 组件

**选择**：在 Dashboard 上渲染四个 headline 指标 + `vs <benchmark>` 差值行，复用 `backtestFormatters` 的纯函数（`parseMetricNumber` / `computeMetricDifference`）。

**理由**：`DecisionSummarySection` 的 CSS 全部 scope 在 `.detail-page` 下（`.detail-page .metric-card`、`.detail-page .decision-summary-section`）。要在 Dashboard 复用它，就必须把这些规则改成全局基类——那会改动 Backtest Detail 的既有渲染，属于"顺手改无关代码"。

**不搬运的部分**：不搬运 `verdict` 徽章。Dashboard 上的第三层只给事实与差值；带 sign 判定的徽章留在 Backtest Detail 的 Decision Summary（那里已经有它自己的说明行）。

**v1 保留**：`resolvePrimaryBenchmark` 泛化为 `resolvePrimaryBenchmark<T extends { key: string }>(benchmarks: T[])`，使 `BacktestBenchmark[]` 与新的 `DashboardBenchmark[]` 共用同一条 Primary 选取规则，不复制优先级逻辑。

### D4：后端投影"窄"到决策层真正显示的字段

**选择**：

```
latest_signal.positions[]  = { exchange, symbol, name, target_weight, rank, score, is_fallback }
recent_backtest.benchmarks[] = { key, name, total_return, total_return_difference,
                                 annualized_return_difference, sharpe_ratio, max_drawdown }
latest_walk_forward = {
  run_id, status, start_date, end_date, window_count, finished_at, error_message,
  oos: null | {
    window_count,
    metrics: { total_return, sharpe_ratio, max_drawdown }   # { median, mean, window_count,
                                                            #   valid_count, evidence_status }
    positive_window_rate: { value, numerator, denominator, window_count, valid_count, evidence_status }
    generalization_gap:   { median, mean, window_count, valid_count, evidence_status }
    benchmarks: { "<key>": { outperformance_rate: {...} } }
  }
}
```

**理由**：

- 复用 `BacktestBenchmarkResponse` 会把 `equity_curve`（数百个点）带进首屏响应，因此必须窄投影。
- `latest_signal.positions` 直接复用既有的 `get_latest_strategy_signal_report`（它已经产出含 `name` 的持仓），从而删掉 dashboard 里那份重复的"只数条数"的查询实现。
- `latest_walk_forward` 不投影 `parameter_stability`：参数迁移率属于 Walk-forward 详情页深挖区，Dashboard 的第四层只保留 5 张卡 + Generalization Gap 说明行。

### D5：`latest_walk_forward` 只加载运行行与证据文档，不加载窗口树

**选择**：`status == "success"` 时用 `validate_wf_evidence(row.evidence_version, row.evidence_json)` 校验证据文档后投影；不调用 `validate_walk_forward_run`，不 `selectinload` windows / OOS backtest / equity curve。

**理由**：`validate_walk_forward_run` 会遍历 `row.windows` 与每个窗口的 OOS run，`get_walk_forward_run` 还要 selectinload 全部净值曲线——这在首屏聚合里代价过高。证据文档自身是 pydantic 模型，独立校验即可保证"投影出去的每个数字都来自一份结构合法的证据文档"。

**已记录的局限**：跨子表一致性检查（窗口数、OOS 归属、基准完备性）不在 Dashboard 路径上执行。若持久化数据在这层不一致，Walk-forward 详情页（权威表面）会抛出契约错误，而 Dashboard 仍会显示运行级事实与证据聚合。因为 Dashboard 只呈现持久化值且始终链接到详情页，这个差异被接受；本地单人只读场景下触发概率极低。

**交叉事实**：运行行的 `window_count` 与证据文档内的 `window_count` 同时呈现，任一方漂移在界面上可见。

### D6：预算按实测修订，不做预留

**选择**：实现完成后跑 `check:bundle`，把 eager / initial / total 的上限改到"实测值向上取整到下一个 1,000"，并在 `bundle-evidence.md` 记录 build identity、逐文件贡献与修订前后数值。同步更新 `web-route-code-splitting` 中 pin 住的数字。

**理由**：`check-bundle` 明确要求"不得静默重新基线化"，所以修订必须是有证据、有 spec delta 的显式动作（该 spec 本身已两次以 "revised budget" / "revised allocation" 的形式修订过）。取整到 1,000 是沿用该文件既有的写法（`70000` / `273000` / `340000`）。

**先尝试降低再修订**：实现时优先复用既有 class 与组件、把旧面板"移动而非复制"，把净增字节压到最小；只有实测确需时才抬升。

### D7：CSS 只新增决策层专属类，不改既有 scope

**选择**：新增 `.research-layer` / `.research-status-*` / `.research-fact-*` / `.oos-robustness-*` / `.evidence-index-*` 等 Dashboard 专属类，样式取自既有 token；表格复用全局的 `.holdings-table` / `.holdings-table-wrap`，面板复用 `.dashboard-panel` / `.panel-heading`，状态复用 `.status-pill`。

**理由**：`design-system` 禁止新增第四个按钮变体、禁止 acid-lime 作为 `background-color`（stylelint 强制）、要求 `line-height` 走 `--leading-*` token、要求 8px 网格间距阶梯。新增类全部遵守这些约束。

**acid-lime 预留**：Bootstrap 仍是本视图唯一的 primary 按钮（`web-frontend-app` 明确要求）。L1 的"下一步动作"按钮使用 `button-secondary`。

### D8：不新增路由 / 不改导航

L5 只是四个指向既有路由的 `.operation-link`。`web-client-routing`、`command-palette`、`web-route-code-splitting` 的路由清单不变。

### D9：决策面上每个 artifact 都必须可归属，且归属必须显示出来

**原则**：五层里任何一处展示某个 artifact 时，用户必须能判断"它是谁的、由哪份配置产生的"。凡是数据支持不了这个判断的展示，都是缺陷。

这条不是先验写下的，而是三次真实缺陷收敛出来的，且三次都在同一类：

| # | 表面 | 缺陷 | 影响 |
|---|---|---|---|
| 1 | L2 | 聚合的"最新成功 signal"可能（本机确实）是回测产出的**模拟产物**，但按当前指令呈现 | 展示的持仓与真实指令完全不同（588000/159915 vs 513100/513500） |
| 2 | L1 | 事实写着回测落后 584 天，文案却断言 "all current" | 文案超出数据支持 |
| 3 | L3 | `recent_backtest` **完全不按策略过滤**，而相邻的 signal 按 strategy_id + config_version 精确过滤 | 可能把别的策略的运行说成本策略的表现 |

**落地规则**：

- **按当前策略限定**：`recent_backtest` 与 `latest_walk_forward` 均按当前 `strategy_id` 限定（精确、大小写敏感），与既有的 `latest_signal` 对齐。`config_version` **不**作为过滤条件——同策略跨版本的运行是可比较的证据。
- **把归属显示出来**：不过滤的维度必须可见。L3 显示运行的 `config_version`；L2 显示 signal 的 source，并在 source 为 `backtest` 时说明是模拟持仓、链到产出它的运行。
- **文案不得超出事实**：无动作提示只能声称它支持得起的状态（见 `research-workbench-ui` 的对应场景）。

**代价**：窄过滤会让聚合更常返回 null（例如刚换 config version 还没跑新回测时 L3 仍显示旧版本运行——这是**有意**的，因为它带着自己的版本号，是可判断的证据而不是被藏起来）。L4 的 `latest_walk_forward` 同理只按 strategy 限定。

**被否的替代方案**：让 L3 也按 `config_version` 精确过滤。否决理由——版本升级后若还没跑新回测，L3 会直接空掉，用户失去"上一版表现如何"这个对照；而显示版本号已经足够让旧版本运行不被误读。

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| 首屏变长，用户要滚动才能到达运维区 | 五层顺序即为优先级；运维/参考区本来就不该在首屏。L1 在首屏给出下一步动作入口（滚动到 Operations 的锚点链接），必要时可一键跳转。 |
| eager 预算抬升削弱既有性能保证 | 先做复用式实现压净增；修订幅度=实测值，并写入 `bundle-evidence.md`；`check-bundle` 的"不得静默重基线"要求由 spec delta 显式满足。 |
| L4 在本机唯一的 walk-forward 记录是 `queued`，无法用真实数据验证成功态 | 成功态由单元测试用固定证据文档覆盖；页面在无证据时渲染如实的不可用说明。 |
| 日历日滞后被误读为交易日 | 文案统一写 `calendar days`，并同时显示两个具体日期。 |
| L4 无法显示 walk-forward 运行对应的配置版本（**已接受的限制**） | walk-forward 运行行只按 checksum 固定 base strategy config，没有 `config_version` 标签（`config_checksum` / `input_data_checksum` 是 64 位摘要，不适合放进紧凑层）。因此 L4 只呈现运行自身的事实（run id、状态、测试区间、窗口数）与证据聚合，不声称它产自当前版本。要按版本判断，走 Walk-forward 详情页的 provenance 区。D9 的"归属可见"在这层通过运行身份而非版本号满足。 |

## Migration / Rollout

无数据迁移。前端与后端同批发布；旧版前端遇到新增字段为可选（`positions` / `benchmarks` / `latest_walk_forward` 都有空值兜底），后端字段为纯增量。`recent_backtest` 的按策略限定会让它更常返回 null——这是修正而非回归：旧行为是把别的策略的运行报成本策略的。

## Open Questions

- 无阻塞项。L1 的"下一步动作"是否需要覆盖 `queued` walk-forward 的情况，留待实现时按测试反馈决定（当前设计为：只有数据/信号缺失或滞后时才给动作）。
