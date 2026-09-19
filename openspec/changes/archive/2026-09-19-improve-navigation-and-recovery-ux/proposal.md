# Proposal: improve-navigation-and-recovery-ux

## Why

上一轮变更（`build-decision-first-research-workbench`）把 Dashboard 重组成决策优先的五层研究路径，解决了"首屏不回答研究问题"。但它解决的是**单页内**的信息架构；**跨页移动**时的体验仍是空白，而且缺陷是可复现的：

- **每个标签页标题都一样。** `index.html` 的 `<title>` 是静态 `Vela Web`，全应用没有一处更新它。浏览器历史里八条记录同名，开两个标签就无法分辨哪个是 Backtest、哪个是 Walk-forward。
- **滚动位置被跨路由继承。** 应用没有任何滚动重置代码。在长 Dashboard 上滚到 ETF 清单，点进一条 Signal，落地页停在 Signal Detail 的中段——用户看不到页面标题，只能自己往上滚。
- **路由切换不移动焦点。** 除 CommandPalette 与 Backtest tab 外，全应用没有 `focus` 调用。键盘与读屏用户在一次 SPA 导航后不知道页面已经变了。
- **列表页码不进入 URL。** 三个列表页的 `offset` 都是组件内 `useState`。在 `/signals` 翻到第 3 页点进一条记录，浏览器后退回来页码归零。Signal 列表的 `source` 筛选反而在 URL 里（`web-client-routing` 明确要求），同一个页面上两种状态两种命运。
- **详情页没有返回入口。** Signal / Backtest / ETF Detail 都没有返回列表的链接（只有 Walk-forward Detail 有 `← Back to Walk-forward history`）。
- **失败无法就地恢复，且原因不可读。** 所有读失败的文案是 `` `X API unavailable: ${error.kind}` ``，而 `kind` 的取值是字面量 `"http"` 或 `"network"`——用户看到的是 "Signal history API unavailable: network"。同时没有任何重试控件：唯一的恢复手段是重新加载整个页面（`window.location.reload()` 只存在于路由级 ErrorBoundary 里）。对本地单用户工具来说，API 进程没起来是最常见的失败，而界面既说不清也救不回。

这些缺陷都不影响金融语义，也不改变任何 API 请求、计算或持久化；它们全部是"用户在哪里、怎么回来、失败后怎么办"的问题。

## What Changes

### 1. 路由切换后的朝向感（前端）

- **滚动重置**：路径变化时把阅读位置复位到页首；带 hash 的导航不重置（让浏览器锚点行为生效）。
- **焦点移动**：路径变化时把焦点移到该页的 `<h1>`，使键盘与读屏用户直接落在页面身份上。
- **文档标题**：每个路由把 `document.title` 设为该页身份，详情页带实体 id（`Signal Detail #307 · Vela Research`），使标签页与历史记录可区分。

这三项与既有"每个页面恰好一个 `<h1>`"的契约一致：焦点落在已有的 h1 上，不新增标题元素。

### 2. 可寻址的列表页码（前端）

`/signals`、`/backtests`、`/walk-forwards` 的当前页进入 URL 查询（`?offset=`），与既有的 `source` 筛选同等对待：合法值初始化、非法值经 Router replacement 归一化、与其它查询参数和 hash 互不破坏。从详情页返回时页码保留。

### 3. 详情页返回入口（前端）

Signal / Backtest / ETF Detail 增加与 Walk-forward Detail 同形的返回链接。ETF Detail 从 Dashboard 的行情区进入，因此返回 Dashboard。

**列表行记录来处**：浏览器交互探针发现，翻到第 2 页后打开详情、再点应用**自己的**返回链接，URL 会变成裸的 `/signals`——页码丢失；而浏览器后退反而保得住。应用自带的返回入口比浏览器按钮更差，正是本变更要消灭的摩擦。因此列表行链接带上 `state={{ listHref }}`，详情页的返回链接回到该位置，无 state 时回退到列表自身路径。

### 4. 读失败可恢复（前端）

- **可操作的失败说明**：区分"本地 API 无法连接"与"API 返回了错误响应（状态码）"，不再向用户暴露 `http` / `network` 这类内部标记。
- **就地重试**：所有列表与详情的读失败都提供重试控件，以同一请求（同样的筛选与页码）重新发起，成功后正常渲染，不需要刷新文档。

### 5. 键盘可达性补口（前端）

- AppShell 增加跳转链接（跳到主内容），使键盘用户不必逐项穿过导航。
- 全局 `:focus-visible` 规则补上 `select`（`ReturnStabilitySection` 的区间选择器目前落在规则之外，只有浏览器默认焦点环）。

### 6. 分页控件的信息量与契约合规（前端）

- **分页说明当前覆盖的行**：分页控件目前只有 `Previous` / `Next` 两个按钮，用户无从判断自己在列表的什么位置、列表有多长。改为一个带标签的导航区，并陈述当前屏覆盖的行区间（有总数时一并给出，主页满页时如实说明该 offset 无行），以 status 区域暴露以便翻页被播报。
- **分页按钮补上按钮变体**：`Pagination` 的两个按钮在此之前**既没有变体 className、也没有任何 CSS**（全仓搜索 `.list-pagination` 无结果），因此以浏览器默认样式渲染在深色界面里。`design-system` 的 "Buttons declare their variant via className" 要求 `apps/web/src/` 下每个 `<button>` 都带三者之一的变体类，这两个按钮一直违反该要求。
- **顺带修掉同类违规**：同一轮排查发现 ETF 详情的 horizon 选择器（`.trend-horizon-button`）与 Backtest 详情的 rolling metric 选择器（`.stability-selector-button`）各自引入了一套 bespoke 分段样式（acid-lime 描边、iris-violet 填充），而 `design-system` 明确要求单选筛选控件"其视觉必须来自变体类，而不是 bespoke 分段样式"——Signals 的 SOURCE 筛选早已按该要求改成 `button-secondary`。本变更把这两个控件也对齐到 `button-secondary` + `aria-pressed`，并删除随之孤立的 CSS。这是把实现拉回既有要求，不是新增视觉。

### 7. 未终止的 Walk-forward 运行不再是死路（前端）

浏览器实测本机库里唯一那条 walk-forward 记录（`queued`）时发现：详情页从上到下是四个大空白带，其中「OOS summary」与「Aggregated evidence」**渲染逐字相同的句子**，而整页没有一处说明这条运行由谁执行、为什么不推进、用户能做什么。`queued` 恰恰是运行未启动时的常态，也就是真实会看到的形态。

- Run Header 为未终止的运行补一句下一步：`queued` 说明它由**独立的本地 worker 而非 API 进程**执行，并点名 `vela walk-forward-worker`（沿用应用既有约定——首屏引导已经会写 `Run vela init-db to ...`）；`running` 说明它正在执行且**本页不会自动刷新**。终止态不渲染该说明。
- `Aggregated evidence` 的未就绪文案改为该区块自有的说法，不再与 OOS Summary 逐字重复。`walk-forward-results-ui` 只对 OOS Summary 的未就绪说明有要求，该区块的文案未被任何 spec 固定；区块的存在性与"如实说明未就绪"的语义保持不变。

## Capabilities

### New Capabilities

- `web-navigation-ux`：路由切换的滚动/焦点/文档标题契约、列表页码的 URL 可寻址性、分页的位置陈述与按钮变体合规、详情页返回入口、AppShell 跳转链接。
- `web-read-failure-recovery`：读失败的成因表述与就地重试契约。

### Modified Capabilities

- `web-client-routing`：该 capability 的既有场景要求每个页面"retains its existing API request, loading, success, empty, **error**, and valid-id API-not-found behavior"。新增重试控件与改写失败文案会改变 error 呈现，因此需要显式修订该子句：请求/加载/成功/空态/not-found 行为保持不变，error 呈现允许增加重试与可读成因。
- `walk-forward-results-ui`：Run Header 的 requirement 列举了它承载的内容（返回链接、状态、单行摘要），本变更新增了未终止运行的下一步说明，属于首屏内容的扩展，因此显式修订该 requirement 并补三条场景（queued / running / terminal）。
- `web-route-code-splitting`：滚动/焦点/标题逻辑位于 eager 的 `App.tsx`，必然增加 eager 与 initial 体积；按实测值修订 pin 住的预算带上限，并新增 `bundle-evidence.md`。

## Impact

- **前端**：`App.tsx`（路由切换组件、文档标题、not-found 标题、reload 按钮变体）、`components/AppShell.tsx`（跳转链接）、`components/Pagination.tsx`（行区间陈述 + 按钮变体）、新增 `components/ReadFailure.tsx` 与 `utils/readFailure.ts`、新增 `utils/listOffset.ts` 与 `utils/documentTitle.ts`；`pages/` 下三个列表页（页码 URL 化）、四个详情页（返回链接 + 标题 + 重试）、`DashboardPage.tsx`（标题 + 重试）、`EtfDetailPage.tsx` 与 `ReturnStabilitySection.tsx`（分段控件对齐变体契约）；`styles.css`（分页布局与行区间、跳转链接、返回链接、重试行、h1 焦点、`select` 焦点环；删除两个孤立的 bespoke 分段样式）。
- **后端**：无。本变更不触碰任何 API、计算或持久化。
- **契约与门禁**：`check-bundle.mjs` 预算值与 `web-route-code-splitting` spec 同步修订；新增 `bundle-evidence.md` 记录实测。
- **明确不改**：路由表与路径含义、API 请求形状、列表列、金融数值与格式化语义、`research-workbench-ui` 的五层结构、CommandPalette 行为、所有后端代码。
