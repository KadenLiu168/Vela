# Tasks: improve-navigation-and-recovery-ux

## 1. 路由切换后的朝向感

- [x] 1.1 新增 `RouteTransition`（`App.tsx` 内），挂在 `<Suspense>` 内层、`<Routes>` 外层：挂载时若 `location.hash` 为空则 `window.scrollTo(0, 0)`，随后把焦点移到 `main h1`。实现方式见 `design.md` D1/D3。→ verify: `App.navigation.test.tsx` 覆盖「换路径后滚动复位 + 焦点在 h1」「首次文档加载不移动焦点」「lazy 路由 fallback 期间不抢焦点、内容渲染后焦点在 h1」「第二次导航仍移焦点」。
      **实现偏差**：初次挂载需要与后续导航区分，为此从 `AppContent` 传入一个 `hasNavigatedRef`（lazy 路由在测试环境中总是异步解析，无法仅靠挂载时机区分文档加载与导航）。该 ref 由 `RouteTransition` 在 effect 中翻转。
- [x] 1.2 目的页 `<h1>` 可编程聚焦：焦点目标设 `tabindex="-1"`，并在 `styles.css` 为被聚焦的页面标题关闭 outline（不进入 Tab 序列、不出现焦点框）。→ verify: 测试断言 h1 的 `tabindex` 为 `-1` 且 `document.activeElement` 为 h1；浏览器实测焦点落在 h1；`lint:css` 通过。
- [x] 1.3 **浏览器实测查出的实现缺陷（已修）**：`RouteTransition` 的「是否首次加载」闩锁写在 effect 里，而 `main.tsx` 用 `StrictMode` 挂载应用——StrictMode 会把一次挂载的 effect 调用两次，第一次调用消耗掉闩锁，第二次就被读成「导航」，于是**首次文档加载也会把焦点移到 h1 并复位滚动**，直接违反本变更自己写的「首次渲染不得移动焦点」。jsdom 用例没捕获，是因为它们直接渲染 `<App />` 而没有 StrictMode。
      **修复**：改为每个实例一个 `handledRef` 守卫（StrictMode 的第二次调用落在同一实例上，因此被守卫吞掉；真正的导航会重新挂载组件，实例是新的、守卫为 false），外加 `AppContent` 的挂载计数判断是否首次加载。效果是幂等的，不再依赖「effect 只跑一次」这一脆弱前提。
      → verify: `App.navigation.test.tsx` 改为在 `StrictMode` 下挂载；**用关闭守卫的方式证明该用例确实会失败**（去掉守卫 → `does not move focus on the initial document load` FAIL），再恢复后全绿；真实浏览器探针实测：首次加载 `active=BODY`、`h1tabindex=null`，导航后 `scrollY=0`、`active=H1:Signals`、`h1tabindex=-1`。

## 2. 文档标题

- [x] 2.1 新增 `utils/documentTitle.ts` 的 `useDocumentTitle(pageIdentity)`：设置为 `<page identity> · Vela Research`。→ verify: `documentTitle.test.ts` 3 条断言通过。
- [x] 2.2 八个页面接入：Dashboard、Signals、Backtests、Walk-forward History、Signal Detail `#id`、Backtest Detail `#id`、Walk-forward Detail `#id`（与既有 h1 同文案）、ETF Detail `#id`；`App.tsx` 的 not-found 为 `Page not found`。→ verify: `App.navigation.test.tsx` 断言列表/静态路由标题、标题随导航更新不残留、not-found 标题、详情页标题以 h1 文本开头且含实体 id；**浏览器实测**八个路由的 `<title>` 均为预期值（如 `Signal Detail #307 · Vela Research`）。

## 3. 列表页码 URL 化

- [x] 3.1 抽出共用的 offset 解析纯函数 `utils/listOffset.ts`。→ verify: `listOffset.test.ts` 覆盖 `"0"`、`"40"`、`null`、`""`、`"-1"`、`"1.5"`、`"abc"`、`"20px"`、`" "`。
- [x] 3.2 三个列表页把 offset 改为由 `location.search` 派生，翻页经 Router navigation 写回 URL；`selectSource` 同时删除 `offset`；非法值经 replace 归一化并保留无关参数与 hash。→ verify: 三个列表页各新增「`?offset=` 初始化」「翻页写回且保留无关参数/hash」「非法 offset 归一化」「回到第一页时移除参数」用例；`web-client-routing` 既有 source 场景保持全绿。
- [x] 3.3 往返保持：`BacktestListPage` 用例走到 `?offset=10` → 点进详情 → `navigate(-1)`，断言列表以 offset 10 重新取数。→ verify: `restores the list offset when returning from a detail page` 通过。
- [x] 3.4 **浏览器实测查出的缺口（已修）**：浏览器交互探针显示，翻到第 2 页后打开详情、再点应用**自己的**「← Back to Signals」，URL 变成裸的 `/signals`——页码丢失；而浏览器后退反而保得住。也就是说应用自带的返回入口比浏览器按钮更差，正是本变更要消灭的那类摩擦。
      **修复**：列表行链接带上 `state={{ listHref }}`（当前 `pathname + search`），详情页经 `utils/listReturn.ts` 读取并回退到列表自身路径。直接访问/书签/丢失 state 时回退；非应用内路径（`https://…`、`//host`）一律拒绝并回退。
      → verify: `listReturn.test.ts` 3 条；`App.test.tsx` 两条集成用例（经返回链接回到 `?offset=20` 并重新以 offset 20 取数；直接打开详情时回退到 `/signals`）；真实浏览器探针复验：详情页的返回链接变为 `/signals?offset=20`，点击后 URL 保持 `?offset=20`。

## 4. 详情页返回入口

- [x] 4.1 `SignalDetailPage` → `/signals`、`BacktestDetailPage` → `/backtests`、`EtfDetailPage` → `/`，均为 Router `Link`，位于页面详情内容之前且在**所有加载态**（loading / 失败 / not-found）都渲染；Walk-forward 的既有链接保持在 Run Header 内不动。→ verify: 三个详情页断言链接文本、`href` 与「先于 `.dashboard-panel`」的文档顺序；失败态用例断言返回链接仍在；浏览器实测三个详情页的返回链接与 href 正确。
      **实现偏差**：原计划让四个详情页采用同一种页面级返回链接。实际保留了 Walk-forward 的实现——`WalkForwardDetailPage.test.tsx` 有两处断言 back link 位于 `.run-header` 内，且 `web-frontend-app` 的既有场景锚定了该结构。改动的收益不足以支付这次契约修订，因此 spec 明确写成「Walk-forward 的既有链接 SHALL be preserved」。
      **间距修正**：首版把返回链接放在 `.page-heading` 之后、作为 `.detail-page` 的独立 grid item。浏览器截图显示它与标题、与面板之间各被推入一个 96px 的 section gap，与设计节奏不符。改为一律置于 `.page-heading` 块内（仍是文档顺序上的详情内容之前），使该 grid 的节奏不被额外行破坏；实测标题到面板的距离与改动前一致。

## 5. 读失败可恢复

- [x] 5.1 新增 `utils/readFailure.ts`：纯函数把 `ApiClientError | unknown` 映射为面向用户的成因句。→ verify: `readFailure.test.ts` 5 条（含「全部输出不含内部标记 `http` / `network`」）。
- [x] 5.2 新增 `components/ReadFailure.tsx`：error 变体 `FeedbackMessage` + `Retry`（`button-secondary`）。→ verify: `ReadFailure.test.tsx` 3 条通过。
- [x] 5.3 接入全部八条读路径（Dashboard、三个列表页、Signal Detail、Backtest Detail 主读与 signals 分页读、Walk-forward Detail、ETF Detail），每条加 reload token 重新执行同一请求。→ verify: 各页均有用例断言「失败 → 以同一参数重试 → 渲染正常态」；`BacktestDetailPage` 断言重试后仍以 `("7", 20, 0)` 请求；`WalkForwardListPage` 断言重试后仍以 `(10, 10)` 请求。
- [x] 5.4 更新既有断言旧文案的测试（`App.test.tsx` 六处、`WalkForwardListPage.test.tsx` 一处、`BacktestDetailPage.test.tsx` 一处）。→ verify: 全部改为断言新成因句与状态码差异，且不再断言 `http` / `network` 字面量；`npm run test` 458 passed / 7 skipped。

## 6. 键盘可达性补口

- [x] 6.1 `AppShell` skip link：文档中第一个可聚焦元素，`href="#main-content"`，点击聚焦 `main`（`tabindex="-1"`）；未聚焦时视觉隐藏、聚焦时可见。→ verify: 测试断言首个可聚焦元素为 skip link、`href` 与 `main` 的 id 对应、激活后 `document.activeElement` 为 `main`；浏览器实测 skip link 为文档首个 `<a>`。
- [x] 6.2 `styles.css`：skip link 样式（走既有 token 与 8px 阶梯）；`:where(a, button, input)` 焦点环规则扩展为含 `select`。→ verify: `lint:css` 与 `lint:css:root` 通过。

## 6b. 分页控件的信息量与契约合规

- [x] 6b.1 `Pagination` 改为带 `aria-label` 的 `<nav>`，新增行区间陈述（有总数时 `Showing 21–40 of 137.`，无总数时 `Showing 1–10.`，该 offset 无行时 `No rows at this offset.`），以 `role="status"` 暴露以便翻页被播报。→ verify: `Pagination.test.tsx` 6 条断言通过。
- [x] 6b.2 两个分页按钮补 `button-secondary`：此前**既无变体类也无任何 CSS**（全仓 `list-pagination` 零命中），以浏览器默认样式渲染在深色界面里，同时违反 `design-system` 的 "Buttons declare their variant via className"。新增 `.list-pagination` 布局与 `.list-pagination-position` 样式。→ verify: 测试断言两个按钮带 `button-secondary`；`lint:css` 通过。
- [x] 6b.3 同类违规一并对齐：`EtfDetailPage` 的 horizon 选择器与 `ReturnStabilitySection` 的 rolling metric 选择器改用 `button-secondary` + `aria-pressed`，删除孤立的 `.trend-horizon-button*` 与 `.stability-selector-button*` 规则。依据是 `design-system` 对单选筛选控件的明确要求（视觉必须来自变体类），Signals 的 SOURCE 筛选已按此实现。→ verify: `App.test.tsx` / `ReturnStabilitySection.test.tsx` / `BacktestDetailPage.test.tsx` 全绿；浏览器实测两个控件的选中态与未选中态。

## 6c. 未终止的 Walk-forward 运行

- [x] 6c.1 `WalkForwardRunHeaderSection` 为未终止运行补下一步说明：`queued` 说明由独立本地 worker 执行并点名 `vela walk-forward-worker`；`running` 说明正在执行且本页不自动刷新；终止态不渲染。→ verify: 三条新用例断言 queued 的说明含命令、running 的说明含「does not refresh itself」、success 不渲染该说明——均通过；`walk-forward-results-ui` delta 已补对应场景。
- [x] 6c.2 `EvidenceSection` 未就绪文案改为区块自有说法，去掉与 OOS Summary 的逐字重复。→ verify: 原先钉住「两处重复」的用例改为断言 OOS Summary 的 note 存在且 Aggregated evidence 使用自己的文案；浏览器实测页面语义清晰。

## 6d. 列表查询状态的收敛（腾出预算余量）

- [x] 6d.1 三个列表页各自实现「重建 URL / 归一化非法值 / 翻页写回」——`SignalListPage` 用命名 helper（`withSearch` / `withoutQueryValues`），另两页用内联模板字符串，同一个规则共 8 处两种写法。抽出 `utils/listQuery.ts` 的 `listHrefWith(location, changes)`（`null` 表示删除该参数，即「回到默认」），三页统一调用；原 `listOffset.ts` 随之改名为 `listQuery.ts`（它现在同时持有 offset 解析与查询串改写）。→ verify: `listQuery.test.ts` 6 条（含「替换既有参数保留其位置」「清空后不再输出 `?`」）；三个列表页既有 URL 用例（初始化 / 写回 / 归一化 / 筛选重置 / 往返保持）全绿。
      **实测收益**：lazy 69,964 → **69,446**（−518），total 353,554 → 353,035，余量从 36 字节回到 554 字节。这不是搬移——同一条规则此前被计了三份。
- [x] 6d.2 **评估后不做**：另外两类重复是各页的 `retry` 样板（8 处 × 3 行）与各页的取数 effect（`isCurrent` 守卫 + 404 分支 + 错误分支）。前者是 3 行样板而非逻辑，抽 hook 只省两行却多一层间接；后者的状态机在各页有实质差异（有的有 not-found、有的有 request key、有的同页两个资源），强行套一个泛型会牺牲可读性。按「不强行复用」停在 6d.1。

## 7. 预算与门禁

- [x] 7.1 跑完整前端门禁：`lint` / `lint:css` / `lint:css:root` / `typecheck` / `test`（458 passed）/ `build`。→ verify: 全部通过。
- [x] 7.2 跑 `check:bundle` 取实测并修订预算，新增 `bundle-evidence.md`。→ verify: 修订后 `check:bundle` exit 0、`violations: []`；`dynamicRouteEntries` 仍列出七个 lazy 页面模块。
      **实测**：eager 52,925→54,283（+1,358）；initial 282,112→283,470（+1,358）；lazy 66,781→68,668（+1,887，**未抬升**，仍在 70,000 内）；total 348,893→352,138（+3,245）。修订后：eager 55,000 raw / 16,000 gzip、initial 284,000 raw / 89,000 gzip（gzip 上调后为 88,963，仍在既有 89,000 内，故不动）、total 353,000 raw。
- [x] 7.3 写 `web-route-code-splitting` delta。→ verify: `openspec validate improve-navigation-and-recovery-ux --strict` 通过。
      **注意**：`--strict` 要求 MODIFIED requirement 携带当前 spec 的全部 scenario，首轮因漏抄三个既有 scenario 被拒，已补齐。

## 8. 端到端验证

- [x] 8.1 用 headless Chrome（本机 Google Chrome）对真实 API 与真实数据做端到端验证。API 指向 `sqlite3 .backup` 产生的 `/tmp` 副本；用户真实 `vela.db` 未作为写入目标。结论：
      - 八个路由的 `<title>` 与唯一 `<h1>` 全部正确；详情页标题带实体 id。
      - 三个详情页的返回链接存在且 href 正确，且在文档顺序上先于详情面板。
      - 停掉 API 后，Signals 与 Dashboard 均显示 `... could not be loaded. The API returned an error response (500).` 与 `button-secondary` 的 `Retry` 按钮。
      - **响应式实测**：用同源 iframe 建立真实 390px 视口逐个测量九个路由，`scrollWidth == clientWidth == 390` 全部成立，无页面级横向溢出（宽表格位于既有 `overflow-x: auto` 容器内，符合设计）。
      - **控件外观实测**：分页渲染为 `<nav aria-label="Pagination">` + 两个 `button-secondary` + `role="status"` 的行区间（`offset=290` 时显示 `Showing 291–307.`）；ETF horizon 五个按钮均为 `button-secondary` 且 `1Y` 带 `aria-pressed="true"`，选中态走变体样式，与 Signals 的 SOURCE 筛选一致。
      **两点必须记录的方法局限**：(a) 本机 headless Chrome 的 `--window-size` 未作用于截图布局视口，`--screenshot` 在 390 尺寸下实际按更宽视口排版后裁剪，因此**不以该截图判断响应式**，改用 iframe 探针测量；(b) 无 Playwright/Puppeteer 等可驱动点击的工具，Retry 的**点击恢复**由 jsdom 用例覆盖，浏览器侧只验证了失败态渲染。
- [x] 8.2 既有能力未被破坏：`npm run test` 458 passed；八个路由各恰好一个 `<h1>`（浏览器实测）；Dashboard 的 `Next: Generate signal` 锚点行为由 `ResearchStatusSection.test.tsx` 与 `App.test.tsx` 既有用例覆盖，`RouteTransition` 的 hash 例外保证文档内锚点跳转不被复位打断。→ verify: 既有测试全绿 + 浏览器 DOM 实测。

## 9. 验证过程记录（非任务）

- [x] 9.1 **已向用户报告**（会话中）：验证前的 `sqlite3 vela.db ".backup /tmp/vela-ux-check.db"` 打开了**真实** `vela.db`。SQLite 在关闭时对 WAL 做了 checkpoint：`vela.db` 被重写（md5 `1ec8bc41…` → `0c9e1437…`，mtime 2026-09-19 12:05:31），`vela.db-wal` / `vela.db-shm` 两个 sidecar 文件被合并并删除。
      **完整性核查**：`PRAGMA integrity_check` = `ok`；`strategy_signal` 307 行、`backtest_run` 1 行、`market_price` 29,498 行、`etf_info` 11 行、`walk_forward_run` 1 行；最新信号为 #307 / 2024-12-31 / `backtest`，行情区间 2011-12-09 → 2026-08-07——与浏览器中应用读取到的数据完全一致。checkpoint 只把**已提交**的 WAL 事务并入主文件，不新增、修改或删除任何行。
      **正确做法**：应先用 `cp` 做**文件级**复制（连同 `-wal` / `-shm`）再打开副本，而不是对原库执行 `sqlite3`。该教训已记录，后续步骤已改用文件级复制。
