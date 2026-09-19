# Design: improve-navigation-and-recovery-ux

## Context

本变更全部落在 `apps/web`，后端零改动。三条既有约束塑造了设计：

1. **Dashboard 是 eager 路由，eager 预算仅剩 75 原始字节**（实测 52,925 / 53,000）。路由切换逻辑只能放在 eager 的 `App.tsx`，因此每一条新增逻辑都要按字节计价。
2. **七个列表/详情页都是 lazy 路由**，其代码不计入 eager 预算。因此"每页各自的标题"和"每页各自的重试"应当留在各页内部，只有跨页共用的最小原语进入 eager。
3. **仓库中已有一个完成但未归档的变更**（`build-decision-first-research-workbench`），它同样修订 `web-route-code-splitting` 的预算带。本变更的实测基线是包含该变更的当前工作树；归档顺序必须是它在前，本变更为后。

## Goals / Non-Goals

**Goals**

- 任何一次跨路由移动之后，用户都知道"这是哪一页"（焦点、标题、滚动位置三者一致）。
- 任何一次读失败之后，用户都能就地重试，并读懂失败成因。
- 列表浏览的上下文（页码、筛选）在往返详情页时保持。

**Non-Goals**

- 不改路由表、不新增路由或导航项。
- 不改任何 API 请求形状、列表列、金融数值与格式化语义。
- 不引入浏览器滚动位置"恢复"（只做复位，见 D3）。
- 不改 CommandPalette 的既有焦点管理（它已经完整）。

## Decisions

### D1：路由切换副作用挂在 Suspense 边界**之内**的组件上

**选择**：新增 `RouteTransition`，渲染在 `<Routes>` 外层、`<Suspense>` 内层。它在挂载时执行滚动复位与焦点移动。

**理由**：焦点目标是页面的 `<h1>`，而 `<h1>` 由 lazy 页面渲染。如果副作用挂在 Suspense **之外**（例如直接挂在 `AppContent` 的 `useEffect(location.pathname)` 上），冷加载某路由时副作用会在 Suspense fallback 阶段触发，此时 DOM 里还没有 `<h1>`，焦点无处可落；等 chunk 解析完页面挂载时又不会再触发一次。

把组件放在 Suspense 内层后，它的挂载时机自动等价于"该路由的内容已经渲染"：chunk 已在内存时与页面同一次 commit 挂载，冷加载时等 chunk 解析后才挂载。配合既有的 `<ErrorBoundary key={location.pathname}>`（已按路径重挂载整棵子树），`RouteTransition` 每次导航都会重新挂载，`useEffect(..., [])` 恰好每次导航触发一次。

**替代方案**：在 `AppContent` 里对 `location.pathname` 起 effect 再用 `requestAnimationFrame` 轮询等待 `<h1>` 出现。否决——用轮询去猜测 React 的提交时机，比让 React 自己决定挂载时机更脆弱。

**代价**：`RouteTransition` 只包一层，不改变路由匹配；`<Routes>` 仍是路径的唯一所有者。

### D2：文档标题由各页自己声明，不从 `<h1>` 反推

**选择**：新增 `useDocumentTitle(title)` 小 hook，各页调用。列表页/静态页传页面身份（`Signals`），详情页传带实体 id 的身份（`Signal Detail #307`）。hook 负责拼上 ` · Vela Research` 后缀。

**理由**：从渲染出的 `<h1>` 反推标题可以零成本覆盖全部页面，但详情页的 `<h1>` 是不带 id 的（`Signal Detail`），而标签页与历史记录里最有价值的信息恰恰是 id——同一策略下会同时存在多个 Backtest 详情。`WalkForwardDetailPage` 的 `<h1>` 已经是 `Walk-forward #{runId}`，说明"标题里带 id"在本项目已有先例；本设计把该先例推齐到其余详情页的**标题**，同时**不改**它们的 `<h1>`（`web-frontend-app` 的 h1 契约与既有测试都锚定了当前文本）。

**约束**：标题必须以该页 `<h1>` 的可见文本开头，避免标题与页面身份漂移。该约束由 spec 断言、由测试固定。

**代价**：8 处调用点。`useDocumentTitle` 会被 eager 的 Dashboard 引用，因此模块本身计入 eager 预算（约百字节级）。

### D3：滚动只做复位，不做恢复

**选择**：路径变化时 `window.scrollTo(0, 0)`；`location.hash` 非空时跳过，交给浏览器锚点行为。

**理由**：SPA 的 `pushState` 不会重置滚动，这是本变更要修的问题。反向的"后退时恢复滚动位置"需要 `history.scrollRestoration = "manual"` 加自建的位置记账，而浏览器在 `pushState` 条目上的滚动恢复本来就不可靠；引入后还要与 D1 的复位逻辑互斥判断，复杂度换来的收益是"后退时少滚一次"。本项目的列表是有页码的表格，后退落在当前页顶部是可预测且可接受的。

**hash 例外**：`ResearchStatusSection` 的下一步动作与 Dashboard 的行情区链接都是 `<a href="#id">`，若在 hash 变化时复位滚动，锚点跳转会被立刻抹掉。

### D4：页码用 `?offset=`，与 `source` 同构

**选择**：三个列表页把当前 offset 写入 URL 查询；非法值（非十进制、负数、超出）经 Router `replace` 归一化后按 0 处理，归一化只删除 `offset`，保留其它查询参数与 hash。

**理由**：与既有 `source` 的处理完全同构（`web-client-routing` 已经为 `source` 定下"合法初始化 / 非法经 replace 归一化 / 保留无关参数与 hash"的契约），复用同一套语义意味着一个心智模型而不是两个。

**替代方案**：用 `?page=2`。否决——API 用 limit/offset，页面用 page 就要在两处做换算，而换算点是 bug 的常见来源；offset 是服务端已经使用的量。

**已知取舍**：URL 中会暴露 `offset=20` 这样的实现量。对本地单用户研究工具这不构成问题，换来的是"后退保留页码"这一可直接感知的收益。

### D5：重试用 reload token，不引入数据层

**选择**：每个读路径在错误态渲染一个重试控件；点击后把该路径的 `reloadToken` state 自增，既有的取数 effect 把 token 列入依赖而重新执行同一请求（同样的筛选与页码）。

**理由**：取数逻辑已经是"effect + 依赖数组"，token 只是把依赖数组从"offset/source"扩展到"offset/source/token"，改动是局部的、不需要把取数提出组件、也不需要引入缓存或查询库。重试的是**同一个请求**，因此失败时用户已经选好的筛选与页码不会丢。

**代价**：8 个读路径各加一个 state 与一个控件。这是重复，但重复的是三行样板，而不是语义；抽成通用 hook 需要把各页不同的取数函数、依赖与状态形状一起参数化，抽象成本高于收益。

### D6：失败成因是纯函数，文案区分两类

**选择**：新增 `utils/readFailure.ts` 导出纯函数，把 `ApiClientError | unknown` 映射为面向用户的成因句：

- `kind === "network"` → 说明本地 API 无法连接、需要确认服务在运行。
- `kind === "http"` → 说明 API 返回了错误响应，并带上状态码。

**理由**：现状把 `kind` 的字面量（`http` / `network`）直接拼进句子，用户读到的是 "Signal history API unavailable: network"。`network` 才是本地工具最常见的真实故障（API 进程没起），它值得一句能指向动作的话；而 `http` 必须带状态码，否则 500 与 422 在界面上无法区分。

**约束**：成因句不得包含 `http` / `network` / `unavailable` 这类内部标记（避免以改写为名把原问题留下），由测试对全部 `ApiClientError` 取值断言。

**替代方案**：把 `ApiClientError.message` 直接展示。否决——它是给调用方与日志的（如 `Request failed with status 500`），既不含恢复动作，也把两种故障混为一谈。

### D7：预算按实测修订，并记录归档顺序依赖

**选择**：实现完成后跑 `check:bundle` 取实测，按"向上取整到下一个 1,000"修订 `check-bundle.mjs` 与 `web-route-code-splitting`，`bundle-evidence.md` 记录前后值与构建身份。

**理由**：`web-route-code-splitting` 要求预算修订必须来自新鲜生产构建的实测、必须记录构建身份、且只能作为显式记录的动作发生。当前 eager 余量 75 字节，本变更的 eager 新增必然越界。

**归档顺序**：本变更与未归档的 `build-decision-first-research-workbench` 都修订同一组预算带。两者的 delta 都写在各自变更内，主 spec 尚未被前者的 delta 更新。**前者的 delta 必须先归档**，本变更的 spec diff 才对应到主 spec 的实际当前值；否则归档本变更会按主 spec 的旧值（40,000 / 269,151 一带）覆盖前者的修订。该依赖记录在 `bundle-evidence.md` 与 tasks 中。

## Risks / Trade-offs

- **焦点 + 滚动在同一个 effect 里改 DOM，可能与 `<h1>` 的渲染竞争**：D1 已把执行时机对齐到内容挂载之后，且只操作已存在的 `<h1>`（取不到则跳过滚动以外的焦点动作，不抛错）。
- **`tabindex="-1"` 加在标题上**：不进入 Tab 序列，因此不改变键盘遍历顺序；为避免"程序化聚焦却出现焦点框"的观感问题，为该 h1 显式关闭 outline。
- **页码进入 URL 后，`source` 筛选必须同时清除 `offset`**：既有 spec 已要求筛选变更重置到第一页，本变更把该要求落到 URL 层（删 `offset` 而不是仅改 state），并与既有"保留无关参数与 hash"的场景保持一致。
- **重试不清空已渲染内容**：错误态本身就没有可保留的内容，因此不需要"保留旧数据 + 重试"的中间态；重试期间回到 loading 呈现。
