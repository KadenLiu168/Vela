# Tasks: build-decision-first-research-workbench

## 1. 后端聚合读模型扩展（增量）

- [x] 1.1 在 `packages/core/src/vela_core/dashboard_aggregation.py` 中投影 `latest_signal.positions[]`（exchange/symbol/name/target_weight/rank/score/is_fallback），保持既有 8 个汇总字段不变。→ verify: `packages/core/tests/test_dashboard_aggregation.py` 新增「未排名持仓排最后」「无持仓返回空数组」两条断言通过。
      **实现偏差**：原计划改为复用 `get_latest_strategy_signal_report`。实际保留既有查询并补一个 ETF 名称投影，因为该 report 的 `generated_at` 是字符串、且不含 `status`——复用会引入一次类型转换和一个硬编码的状态常量，代价高于收益。
- [x] 1.2 `_get_recent_backtest_summary` 加载 `BacktestRun.benchmarks` 并投影窄基准条目（key/name/total_return/annualized_return/sharpe_ratio/max_drawdown/total_return_difference/annualized_return_difference），并补 `annualized_return` 到汇总（L3 的 CAGR 卡需要）。→ verify: 新增断言证明差值取自后端计算、legacy run 得到空数组、投影不含净值曲线。
- [x] 1.3 新增 `_get_latest_walk_forward_summary`：按非终态优先、终态按完成时间倒序取当前 strategy 的最新 run；`status == "success"` 时用 `validate_wf_evidence` 校验证据文档并投影窄 OOS 证据（三个指标摘要 + 正收益窗口率 + Generalization Gap + 每个基准的超额率）。→ verify: 单测覆盖 success / failed / 非终态优先 / 其它 strategy / 无 run。
- [x] 1.4 在 `apps/api/src/vela_api/schemas.py` 中新增响应模型并挂到 `DashboardResponse`。→ verify: `uv run --no-sync pytest` 1029 passed；`uv run --no-sync mypy --config-file pyproject.toml` 无 issue。
- [x] 1.5 确认 dashboard 读路径不加载 walk-forward 窗口子表。→ verify: `_project_oos_evidence` 只读 run 行与 evidence 文档（代码审查确认无 `selectinload`、无 `windows` 访问）；该边界与其代价已记录在 `design.md` D5，并由 1.3 的单测以「无窗口子行、仅证据文档」的 fixture 固定下来。
- [x] 1.6 把 walk-forward「最新 run」的排序提取为 `walk_forward_run_ordering()` 并让列表与 dashboard 共用，避免两处各自定义「最新」。→ verify: 既有 `test_walk_forward_query.py` / `test_walk_forward_history.py` 全绿。

- [x] 1.7 把 `_get_recent_backtest_summary` 按当前 `strategy_id`（精确、大小写敏感）限定。原实现完全不限定策略，而 L3 现在与 L2 同处一个决策面、被读作"这个策略的表现"——不限定就会把别的策略的运行说成本策略的表现。config_version **不**过滤：同策略跨版本的运行是可比较的证据，且运行自己的版本会显示出来（见 3.8）。→ verify: 新增 `test_dashboard_summary_ignores_foreign_strategy_backtest_runs`；`test_dashboard_aggregation.py` 13 passed。
      **顺带暴露的既有测试问题**：该文件两处 BacktestRun fixture 用的 strategy_id 是小写 `dual_momentum`，而 `_strategy_summary()` 返回 `Dual_momentum`——也就是说这些 fixture 一直在依赖"不过滤策略"的旧行为。已改成与当前策略一致，并新增 3.8 让版本可见。

## 2. 前端 API 客户端与纯函数

- [x] 2.1 `apps/web/src/api/client.ts` 增补 `DashboardSignalPosition` / `DashboardBenchmark` / `DashboardWalkForwardSummary` 及其证据类型。→ verify: `npm run typecheck`。
- [x] 2.2 Primary Benchmark 选取规则去重：抽出 `PRIMARY_BENCHMARK_KEY`，`resolvePrimaryBenchmark` 泛化为结构化入参。→ verify: `DecisionSummarySection.test.tsx` / `backtestFormatters.test.ts` / `walkForwardFormatters.test.ts` 全绿、行为无变化。
- [x] 2.3 把 `formatSignedPercent` / `formatSignedDecimal` / `formatDrawdownDifference` 从 `DecisionSummarySection.tsx` 的私有函数提升为 `backtestFormatters.ts` 的导出，供 Backtest Detail 与 Dashboard 共用同一套差值显示语义。→ verify: 同上，`DecisionSummarySection.test.tsx` 无改动通过。
- [x] 2.4 新增 `apps/web/src/pages/researchWorkbench.ts`：状态事实推导（日历日差、是否滞后、缺项、唯一下一步动作）、基准差值取值、OOS headline 取值与不可用说明。→ verify: `researchWorkbench.test.ts` 26 条断言通过。

## 3. 前端五层信息架构

- [x] 3.1 新增 `ResearchStatusSection.tsx`（L1）：四类事实 + 至多一个下一步动作（指向既有控件的锚点，secondary 语义，不新增按钮）。→ verify: `ResearchStatusSection.test.tsx` 8 条断言通过。
- [x] 3.2 L2（最新 Signal）与 L3（策略表现）作为 `DashboardPage.tsx` 的局部组件实现（`SignalSummary` 重写为目标持仓表，`BacktestSummary` 重写为四张 headline 卡 + 基准差值行），沿用既有 testid `workflow-panel-signal` / `workflow-panel-backtest`。→ verify: `DashboardPage.test.tsx` 与 `App.test.tsx` 的持仓、差值、标签断言通过。
      **实现偏差**：原计划各自独立成文件并由独立测试覆盖。实际放在页面内，与既有 `SignalSummary` / `BacktestSummary` / `FetchLogSummary` 的既有组织方式一致，避免为只在一处使用的表片段新增两个模块。
- [x] 3.3 新增 `OosRobustnessSection.tsx`（L4）：运行状态/区间/窗口数 + 成功态跨窗口聚合 + Generalization Gap 与充分性说明 + 链接；无证据时按状态说明原因，不渲染任何分值或徽章。→ verify: `OosRobustnessSection.test.tsx` 7 条断言通过。
- [x] 3.4 L5（深度证据）作为 `DashboardPage.tsx` 的局部组件 `EvidenceIndexSection` 实现，链接 `/signals`、`/backtests`、`/walk-forwards` 与 ETF 行情区锚点，不新增路由或导航项。→ verify: `DashboardPage.test.tsx` 的决策路径测试断言三个 href 与五层顺序。
- [x] 3.5 抽出 `panelHeading.tsx`（`PanelHeading` / `StatusPillBadge` / `StatusPill`），使决策层与参考面板共用同一标题原语。→ verify: `typecheck` 与全部相关测试通过（提取，无行为变化）。
- [x] 3.6 重组 `DashboardPage.tsx`：L1→L5 决策路径前置，移除与新层重复的旧 Signal/Backtest 面板，Market data / Strategy / Operations / Fetch history 下移为参考与运维区；panel 标签对齐到 `web-frontend-app` 既有要求（`Market`/`Price data`、`Strategy`/`Parameters`、`Signal`/`Latest result`、`Backtest`/`Latest result`）。→ verify: `DashboardPage.test.tsx`（含新增决策路径 describe 块）与 `App.test.tsx` 全绿。
- [x] 3.7 `styles.css` 增补决策层样式（仅新类，token 化、8px 阶梯、无 acid-lime 背景、line-height 走 token）。→ verify: `lint:css` 与 `lint:css:root` 通过。

- [x] 3.8 L3 增加 `Config version` 行：这一层是对"当前策略表现"的断言，运行若产自更早的 config version，不显示版本就无从判断。→ verify: `DashboardPage.test.tsx` 新增「states which config version produced the shown performance」；浏览器实测显示 `CONFIG VERSION v1`。

## 4. 预算与门禁

- [x] 4.1 跑完整前端门禁：`lint` / `lint:css` / `typecheck` / `test`（412 passed）/ `build`。→ verify: 全部通过。
- [x] 4.2 跑 `check:bundle` 记录实测，按「实测值向上取整到下一个 1,000」修订 `check-bundle.mjs` 与 `web-route-code-splitting` 中 pin 住的数字，并新增 `bundle-evidence.md`。→ verify: 修订后 `check:bundle` exit 0、`violations: []`。
      **实测**：eager 39,964→52,232（+12,268）；initial 269,151→281,419；total 339,146→348,272（+9,126）；lazy 69,995→66,853（**下降 3,142，未抬升**）。修订后：eager 53,000 raw / 15,000 gzip、initial 282,000 raw / 89,000 gzip、total 349,000 raw。
- [x] 4.3 确认路由切分契约未变：七个 lazy 路由入口仍为独立 dynamic entry，Dashboard 仍为 eager。→ verify: `check:bundle` 的 `dynamicRouteEntries` 仍列出全部七个页面模块。

- [x] 4.4 补齐 Signal provenance：后端投影 `latest_signal.source` + `backtest_run_id`，前端 L2 显示 source 徽章，并在 source 为 `backtest` 时说明「这些是模拟持仓、不是当前指令」且链到产出它的回测 run。→ verify: 后端 `test_dashboard_aggregation.py` / `test_dashboard.py` 断言 provenance 投影；前端 `DashboardPage.test.tsx` 新增「backtest-sourced signal 标注为模拟」用例。
      **为什么需要**：`getdashboard` 的 latest-signal 按 `generated_at` 取最新成功 signal，本机上那正是回测 #1 产出的模拟信号。不标注，首屏就把 2024-12-31 的模拟持仓当当前指令呈现。同时把 `SOURCE_LABELS` 抽到 `signalSourceLabels.ts` 供 Dashboard 与 Signals 列表共用，避免两处各自命名 source。
- [x] 4.5 provenance 追加后 eager 超预算 141 字节，先收紧实现（把警告文案与 run 链接合并成一句、去掉对 `legacy` 的推测性警告——`legacy` 只是来源未知而非已知模拟，Signals 列表已有既有说明），再复核：eager 52,925/53,000 通过。initial 因首轮把两个带按同一增量取整而余量不足（原 eager 仅余 36 字节、initial 余 3,849），按最终实测把 initial 从 282,000 调到 283,000，并同步更新 `bundle-evidence.md` 的前后实测与理由。→ verify: `check:bundle` exit 0、`violations: []`。

## 5. 端到端验证

- [x] 5.1 用真实本地数据在浏览器验证 1440x1000 与 390x844：五层顺序正确、滞后事实正确（数据 2026-08-07 / 信号 2024-12-31 → 584 calendar days）、无页面级水平溢出（390px 下 `scrollWidth == clientWidth`）、无 console 错误。→ verify: 截图 + `console` / `errors` 检查。
- [x] 5.2 验证既有能力未被破坏：八个路由（含 not-found）均无 console 错误、每页恰好一个 `<h1>`；Backtest Detail 的 Decision Summary 与基准对照经格式化函数迁移后取值与措辞不变；CommandPalette 仍可由 Meta+K 打开；「Next: Generate signal」锚点确实把焦点移到 `#dashboard-generate-signal` 按钮。→ verify: 浏览器实测 + 既有测试全绿。
- [x] 5.3 验证降级路径：无 signal / 无 backtest / 无 walk-forward run 时各层如实说明且不伪造数值（由单测覆盖；本机真实 walk-forward 记录为 `queued`，页面如实显示「Evidence is unavailable until this queued run reaches a terminal state.」）。→ verify: `ResearchStatusSection.test.tsx`、`OosRobustnessSection.test.tsx`、`researchWorkbench.test.ts`。
- [x] 5.4 `openspec validate build-decision-first-research-workbench --strict` 通过；`git diff --check` 无输出。→ verify: 两者均通过。
- [x] 5.5 端到端跑通工作台的核心闭环，且**不写用户的真实数据**：用 sqlite backup 复制 `vela.db` 到 `/tmp`，临时把 API 指向副本（`uv run python` 小脚本重设 `app.state.database_url`），在浏览器里先点 L1 的 `Next: Generate signal` 锚点（焦点确实落到 `#dashboard-generate-signal`），再点按钮。结果：L2 从 `Signal #307 / 2024-12-31 / SOURCE Backtest` 变为 **`Signal #308 / 2026-08-07 / SOURCE Manual`**，无模拟警告；L1 的滞后事实消失、下一步动作消失。验证后确认真实 `vela.db` 的 md5 与 mtime 均未变化，并清理副本与临时 API。
      **这次真实闭环查出一个我引入的 bug**：动作消失后 L1 显示「Market data, the latest signal and the latest backtest are all current.」，而正上方两行就写着回测区间落后 584 天——文案断言了事实不支持的状态。已改为「Market data and the latest signal are current; no corrective action is needed.」，并把 `research-workbench-ui` 的对应 requirement 收窄为「动作只能由缺数据/缺信号/信号滞后触发；仅回测区间滞后只作为事实呈现」，同时加一条「无动作文案不得声称滞后项为 current」的场景与回归测试。
      **顺带确认 provenance 修复不是装饰**：live 信号 #308 的持仓是 513100 纳指ETF / 513500 标普500ETF，与回测产物 #307 的 588000 科创50ETF / 159915 创业板ETF 完全不同——不标注来源，首屏给的就是两个错的标的。
- [x] 5.6 生成路径的 provenance 钉死：`App.test.tsx` 的 generate 成功用例补上 `source: "manual"` 并断言 L2 显示 `Manual`、且不出现模拟警告。→ verify: `App.test.tsx` 79 passed。
      **已知既有问题（非本次引入）**：`openspec validate --all --strict` 当前 45 passed / 11 failed，失败项全部是既有 spec 的 `## Purpose` 占位符（`git status openspec/specs/` 为空，本次未改动任何主 spec），与本变更无关。
