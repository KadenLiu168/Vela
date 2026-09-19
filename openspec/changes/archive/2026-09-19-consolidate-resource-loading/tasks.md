# Tasks: consolidate-resource-loading

## 1. hook 与其单测

- [x] 1.1 新增 `src/utils/useResource.ts`：持有 `{ status, key, data | error }`，`key` 与调用方当前 key 不符时对外报告 `loading`；`load` 经 ref 保存，effect 只依赖 key 与内部重试计数；`hasNotFoundState` 决定 404 是否产出 `not-found`；`reload()` 置 loading 并递增计数。→ verify: `useResource.test.tsx` 11 条通过（就绪读 data、换 key 立即回 loading 且不显示旧数据、陈旧响应不覆盖、404 开关两向、非 404 错误携带失败、reload 回 loading 后就绪、卸载后不写状态、最新 loader 不重取、返回值引用稳定、StrictMode 下状态正常、非 StrictMode 单次挂载只取一次）。
- [x] 1.2 幂等性核查：与路由切换那次不同，本 hook **没有跨挂载的闩锁**——它只在 key 或重试计数变化时重取，StrictMode 的第二次 effect 调用产生的是第二次请求（与迁移前各页行为一致，React 的既有开发期语义），其结果由 cleanup 的陈旧守卫丢弃，状态不会被写坏。因此这里不存在「双调用把首次加载读成导航」那一类失败模式；`StrictMode` 用例断言的是状态正确，而非请求次数。→ verify: 该用例通过；`fetches once for a single mount outside StrictMode` 证明非开发期只取一次。

## 2. 逐页迁移

- [x] 2.1 `SignalDetailPage`。→ verify: `App.test.tsx` 全绿。
- [x] 2.2 `BacktestDetailPage` 主读。→ verify: `BacktestDetailPage.test.tsx` 全绿。顺带删除 `backtestState.backtestId !== backtestId` 守卫——hook 已保证 ready 数据属于当前 id。
- [x] 2.3 `WalkForwardDetailPage` 主读。→ verify: `WalkForwardDetailPage.test.tsx` 全绿。
- [x] 2.4 `EtfDetailPage`（key 为 `id:range`）。→ verify: `App.test.tsx` 中 ETF 用例全绿。
- [x] 2.5 `SignalListPage`（key 为 `offset:source`）与 `BacktestListPage`（key 为 offset）。→ verify: 两个列表页测试文件全绿。
- [x] 2.6 **迁移中查出的 hook 缺陷（已修）**：hook 每次渲染返回新对象，而 `BacktestDetailPage` 的 signals effect 依赖了它——渲染即重跑 effect，失败时退化成自动重试循环，Retry 按钮永远不出现（被既有用例捕获）。修法是在 hook 内 `useMemo` 按 `(stored, key)` 记忆返回值，恢复 `useState` 对象原有的引用稳定性；并补一条「结果不变时返回值引用不变」的回归用例。同时给 hook 加 `hasNotFoundState` 重载，使列表页拿到不含 not-found 的三态，不必处理到不了的状态。
- [x] 2.7 **评估后不迁移**：`WalkForwardListPage` 的列表读（成功回调还要调和 run-trigger 状态机，需单点 `onLoaded` 旋钮）与 `BacktestDetailPage` 的 signals 分页读（按 tab 懒加载 + 同 offset 不重复请求）。理由见 `proposal.md`。

## 3. 门禁与预算

- [x] 3.1 完整前端门禁：`lint` / `lint:css` / `lint:css:root` / `typecheck` / `test` / `build`。→ verify: 全部通过；测试数 471 → 482（净增 11，全部来自 hook 单测）。
- [x] 3.2 `check:bundle` 实测并记录。→ verify: `violations: []`；lazy 69,446 → **68,322**（−1,124），total 353,035 → 351,957（−1,078），两条带都**不需要修订**（是下降）。eager +46 无法归因，已如实记录在 `bundle-notes.md` 而非编造原因。

## 4. 端到端验证

- [x] 4.1 真实浏览器复核。→ verify: headless Chrome 探针（API 指向 `cp` 出来的数据库副本，用户真实 `vela.db` 未被触碰，md5 前后一致）实测：
      - 六条迁移路径全部正常——`/signals` 20 行、`/signals/307` 2 条持仓、`/backtests` 1 行 + 分页、`/backtests/1` 全量证据区、`/walk-forwards/1` 显示 queued 与下一步说明、`/etfs/1` 图表读数。
      - 停掉 API 后 `/signals` 与 `/signals/999999` 均显示可读成因 + `Retry` 按钮。
      - 恢复 API 后四个详情页的 **not-found 路径**逐一验证：`Signal 999999 was not found.` / `Backtest run 999999 was not found.` / `ETF 999999 was not found.` / `Walk-forward run 999999 was not found.`——这是 404 → not-found 映射在收敛后仍然生效的直接证据。
- [x] 4.2 确认无行为回归：迁移只删除各自的 effect / 状态类型 / 派生 helper / `retry`，渲染函数与文案未改；482 测试全绿；浏览器 DOM 与迁移前一致。→ verify: diff 审阅 + 探针实测。
