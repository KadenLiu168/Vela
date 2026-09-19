# Design: consolidate-resource-loading

## Context

七个读路径的手写生命周期已经过两轮变更打磨，行为是被测试与 spec 固定住的既有契约；本次要在不改变这些行为的前提下把七份收敛成一份。已归档的 `improve-navigation-and-recovery-ux` 与 `build-decision-first-research-workbench` 的 bundle-evidence 记录了 lazy 带余量仅 554 原始字节。

## Goals / Non-Goals

**Goals**

- 各页的加载 / 就绪 / 未找到 / 失败 / 重试行为逐条不变（唯一例外见 D5）。
- 「陈旧响应不得覆盖当前请求的结果」与「数据与其请求标识绑定」这两个不变量从一个共享实现获得，而不是七个副本各自维持。
- 保留 lazy 余量。

**Non-Goals**

- 不改任何页面渲染、文案、类型形状（页面自己的渲染函数签名不变）。
- 不引入取数库或缓存层。
- 不改 API 客户端。

## Decisions

### D1：hook 同时持有状态与请求标识

**选择**：hook 内部状态是 `{ status, key, data | error }`；当 `key` 与调用方当前传入的 key 不符时，对外报告 `loading`。

**理由**：当前各页把 `offset` / `signalId` 与 `data` 存在同一个对象里，正是为了让「这份数据属于这次请求吗」成为类型与结构上的保证，而不是一次容易漏掉的比对。如果 hook 只返回状态、让页面另行持有 offset，这个不变量就退化成两个必须手工同步的状态源——那是**倒退**，不是收敛。因此 hook 必须把 key 与 data 绑定在同一处。

**代价**：hook 的状态类型带一个类型参数 `K`；调用方读 `state.data` 前仍要按 `status` 收窄（与今天相同）。

### D2：`load` 经 ref 保存，effect 只依赖 key 与内部重试计数

**选择**：`load` 是每次渲染新建的闭包；hook 用 ref 持有最新的一份，effect 只在 key 或重试计数变化时执行。

**理由**：若把 `load` 放进依赖数组，每次渲染都会重新取数。这是 `useLatest` 的标准写法，也是唯一能在保持「调用点写法自然」的同时让 effect 依赖最小的方法。

**替代方案**：要求调用方把 loader 包进 `useCallback`。否决——那只是把正确性的负担从 hook 挪回七个调用点，与本次目的相反。

### D3：404 是否可渲染由调用方声明

**选择**：`hasNotFoundState`（详情页 `true`，列表页 `false`）。

**理由**：三个详情页各自渲染「Signal 42 was not found.」这类文案；列表端点没有 not-found 呈现，404 今天按普通失败处理。让 hook 无条件产出 `not-found` 会迫使列表页处理一个它们不该展示的状态，或把 404 错误对象丢掉改成别的文案——两者都是行为变更。

**代价**：一个布尔选项。它的名字表达的是「这个页面会渲染 not-found」，是调用方的事实，不是实现旋钮。

### D4：请求标识用字符串

**选择**：详情页传自己的 id；ETF 详情传 `id:range`；列表页传由 offset 与筛选拼出的标识。

**理由**：hook 只需要「这次请求是不是同一个」的等价判断，字符串让这个判断显式且可读，也避免了元组在依赖数组里的身份问题。

### D5：`reload()` 先回到 loading 再重发

**选择**：`reload()` 把状态置为 loading 并递增内部计数。

**理由**：这正是 `web-read-failure-recovery` 要求的重试行为（「the page's loading state is shown while that request is in flight」），今天各页在 `retry()` 里手写同样的两行。

**唯一的行为变化**：`WalkForwardListPage` 在 409（已有运行在跑）路径上原本递增 `refreshToken` 做**静默**重取，迁移后与重试共用 `reload()`，列表会短暂进入 loading。这是可接受的：该分支刚告诉用户「已有运行在进行」，紧接着刷新列表把它显示出来，出现加载态是诚实的。该变化记录于此，并由既有 409 用例覆盖。

## Risks / Trade-offs

- **一次改七个页面**：迁移按页逐个进行，每页迁移后立即跑该页的测试文件，再跑全量；任何一页出问题只回退这一页。
- **hook 自身是微妙代码**：`useLatest` + 重试计数 + key 比对，约 60 行。它必须有自己的单测，覆盖 key 变化、陈旧响应、404 分支开关、重试回到 loading、卸载后不写状态。
- **StrictMode**：hook 的 effect 必须幂等——`improve-navigation-and-recovery-ux` 已经在这一类上栽过一次。hook 的单测在 `StrictMode` 下挂载。
- **字节期望**：预期 lazy 带下降，但共享 hook 本身计入 lazy，因此净收益需实测；若实测为负，本变更失去预算理由，只保留质量理由（仍成立）。
