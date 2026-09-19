# Proposal: consolidate-resource-loading

## Why

`apps/web` 的七个读路径各自手写同一套取数生命周期。实测（不是估计）：四个详情页的 effect **逐行同构**，各 27 行，只差 loader 调用、setter 名与请求标识——三个列表页是同形的第三到第七份，仅少一个 404 分支。

重复的不只是样板，而是**行为**：

- 「响应属于哪次请求」的陈旧响应守卫（`let isCurrent` / `requestKey`）。
- 404 → not-found 的映射。
- 「已存数据与当前请求不匹配就算加载中」的派生逻辑。
- 重试时先回到 loading 再重发。

这类逻辑的正确性我已经栽过一次：`improve-navigation-and-recovery-ux` 里路由切换 effect 的闩锁不幂等，StrictMode 双调用下首次加载就抢焦点，而 jsdom 用例因为没套 StrictMode 全部通过。**七份手写副本意味着同一类错误有七个藏身处**，而且只有一份会被修。

同时，`web-route-code-splitting` 的 lazy 带当前只剩 554 原始字节；一份共享实现只计一次，而七份实现计七次。

## What Changes

新增 `utils/useResource.ts`：一个持有请求标识与状态的取数 hook。

- **hook 同时持有状态与请求标识**，因此「这份数据属于这次请求吗」仍是结构性保证，而不是靠各页自觉比对。当前没有数据、或其标识与当前请求不符时，hook 对外报告 `loading`。
- **404 是否成为一个页面要渲染的 not-found 状态由调用方声明**：三个详情页声明是（它们各自渲染 not-found 文案），三个列表页声明否（列表端点的 404 按普通失败呈现）。
- **`reload()` 回到 loading 再重发**，即重试语义；调用方不再自己维护 reload token 与 `retry()`。

**七个读路径中有六个**迁移到该 hook（Signal / Backtest / Walk-forward 的详情、ETF 详情、Signal 列表、Backtest 列表），各自的 effect、状态类型、派生 helper 与 `retry()` 随之删除。

**两处不迁移**，因为它们的取数不是同一种东西：

- `WalkForwardListPage` 的列表读：它的成功回调还要**调和 run-trigger 状态机**（本地发起的 starting / refreshing 与服务端是否存在活动运行之间的优先级与回落）。这是页面特有的逻辑，不是重复逻辑；把它塞进 hook 需要一个只服务单点的 `onLoaded` 回调旋钮，而那类回调正是 React Query 从 API 里移除的东西。
- `BacktestDetailPage` 的 signals 分页读：它是**按 tab 懒加载**的（Overview 时不请求），并且带「同一 offset 不重复请求」的守卫。迁移它会把它变成页面加载即请求——行为倒退。

两处都保留原样；它们不是同一形状的副本，而是各自有不同用途的读。

## Impact

- **前端**：新增 `src/utils/useResource.ts` 与其单测；`SignalListPage` / `BacktestListPage` / `WalkForwardListPage` / `SignalDetailPage` / `BacktestDetailPage` / `WalkForwardDetailPage` / `EtfDetailPage` 迁移。
- **后端**：无。
- **契约**：无。这是纯重构，`.openspec.yaml` 标记 `skip_specs: true`——不新增也不修改任何 requirement，既有 spec 描述的行为必须逐条保持。
- **可观察的行为变化（唯一一处）**：Walk-forward 列表页在「已有运行在跑」的 409 路径上原本做静默重取，迁移后与重试共用 `reload()`，列表会短暂进入 loading。记录在 `design.md`。
- **明确不改**：API 请求形状、各页渲染、加载/失败/空态/not-found 的文案与结构、路由与 URL 契约。
