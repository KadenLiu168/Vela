## Context

当前研究前端有两块体验短板：

- **Signals 列表**：`strategy_signal.source`（manual / scheduled / backtest / legacy）已由 `SourceBadge` 展示，但 `list_strategy_signals()`、`GET /api/strategy-signals` 和前端 client 都不接受 source，用户只能逐页查看。
- **Backtest 详情**：`getBacktestDetail` 返回完整 `signal_ids`；页面在净值曲线和参数之前渲染所有 signal id 链接，导致长回测详情被低信息量列表拉长。

架构约束是业务查询放在 `packages/core`、HTTP 参数与错误映射放在 `apps/api`、前端使用 React 19 + Vite，并保持现有 API 合同向后兼容。项目是本地个人研究 MVP，应优先采用小而可测试的改动，避免为单页控件建立不必要抽象。

## Goals / Non-Goals

**Goals:**

- Signals 列表提供真正跨页生效的服务端 SOURCE 筛选，并允许用 URL 分享该筛选。
- Backtest 详情默认展示概览；Signals 独立为懒加载、数据库级分页的紧凑表。
- 新增行为具备明确的错误、空数据、分页边界和无障碍验收标准。

**Non-Goals:**

- 不改变信号来源枚举、信号生成流程或数据库 schema。
- 不增加 Signals 文本搜索、批量操作、实时刷新或多来源组合筛选。
- 不删除或改变 `GET /api/backtests/{run_id}` 既有的 `signal_ids` / `signal_count` 字段。
- 不建立通用 Tab/segmented-control 组件库；只有出现第二个真实复用点时再抽象。
- 不承诺本 Change 消除 backtest detail 中全量 `signal_ids` 的传输；这是兼容性保留项。

## Decisions

**D1 - SOURCE 筛选走服务端。**

前端只拥有当前页数据，客户端 source 过滤会误导用户。`GET /api/strategy-signals` 增加可选 `source`，core 在既有 strategy/config/status 作用域上追加 source 条件。只有参数省略时表示全部；字符串 `null`、空字符串和未知值都不是合法来源，由 FastAPI 返回稳定的 422 validation 错误。

不增加文本搜索。当前列表已经固定在当前 `config_version`，搜索 config version 没有区分度；只搜索当前页的 signal id 又会遗漏后续页。若未来有跨历史搜索需求，应单独定义服务端查询合同。

**D2 - URL 只持久化合法 SOURCE。**

`SignalListPage` 初始化时读取 `window.location.search`：四个合法值恢复对应筛选；缺失参数表示 All；非法或空值规范化为 All 并从 URL 移除。切换筛选用 `URL` / `URLSearchParams` 和 `history.replaceState` 更新，只增删 `source`，保留其他 query 参数与 hash，并把 offset 重置为 0。App 的路由只消费 pathname，因此不修改 `App.tsx` 路由核心。

**D3 - Backtest 信号分页必须在数据库执行。**

不能复用 `get_backtest_result()` 后对 `run.signals` 做 Python 切片：该函数通过 `selectinload` 全量加载 equity curve 与 signals，且若 API 先用它校验归属、core 再调用一次，还会产生重复查询。这违背服务端分页的边界。

新增 `list_backtest_signals(session, *, run_id, strategy_id, config_version, limit, offset=0)`：

1. 用轻量查询确认 run 同时匹配 `run_id`、`strategy_id`、`config_version`；不存在或不匹配返回 `None`。
2. 直接查询 `StrategySignal` 所需四列，按 `signal_date ASC, id ASC` 排序并应用 SQL `OFFSET/LIMIT`。
3. run 存在但无信号时返回空 list。

该查询复用现有 `ix_strategy_signal_backtest_run_id`。API 只负责加载当前配置、调用 core，并把 `None` 映射为稳定 404，不直接重复业务查询。

**D4 - 新端点统一返回 `signals`。**

`GET /api/backtests/{run_id}/signals` 返回 `{ "signals": [...] }`，每项为 `{ signal_id, signal_date, result, backtest_run_id }`。返回该 run 的全部关联信号，不按 status 过滤，口径与 detail 的 `signal_count = len(run.signals)` 一致。结果按 `(signal_date, id)` 升序，`limit` 为 1–100（默认 20），`offset >= 0`。

Backtest 结果在当前同步事务完成后才对 API 可见，已完成 run 的信号关联视为不可变。若未来支持运行中增量可见或删除信号，offset 分页与 detail 计数的一致性需要另行设计快照/游标语义。

**D5 - detail 合同保持兼容，性能收益如实限定。**

现有 `GET /api/backtests/{run_id}` 继续返回完整 `signal_ids` 和 `signal_count`。新端点使 Signals Tab 的摘要数据和 DOM 渲染按页受限，并避免为摘要读取完整 signal 对象；但 detail 仍会传输 id 数组。彻底移除这部分全量传输需要版本化或兼容迁移，不在本 Change 内。

**D6 - Backtest 详情用两个 Tab。**

Overview 默认显示运行信息、指标、净值曲线和参数；Signals (N) 独立显示信号表。这里的可验收目标是“查看概览内容不再需要先滚过完整信号列表”，而不是依赖具体 viewport 的“所有内容都 above the fold”。

Signals 数据仅在首次激活该 Tab 且 `signal_count > 0` 时请求；计数为 0 时直接显示空状态。分页变化请求对应 offset。切换回 Overview 可保留已加载页；`backtestId` 变化时必须重置活动 Tab、offset 和 Signals 请求状态，且旧请求不得覆盖新 run。

**D7 - Pagination 使用已知总数消除空白下一页。**

现有 `Pagination` 只用 `itemCount >= pageSize` 推断下一页，在总数刚好为页大小整数倍时会允许进入空白页。给组件增加可选 `totalCount`：提供时用 `offset + itemCount < totalCount` 判断 Next；未提供时保持既有推断，避免影响 Signals/Backtests 列表现有合同。Backtest Signals 传入 detail 的 `signal_count`。

**D8 - 无障碍 Tab 采用简单的自动激活模式。**

Tab 使用 `role="tablist"`、`role="tab"`、`role="tabpanel"`、`aria-selected`、`aria-controls` 和关联 id。ArrowLeft/ArrowRight（以及 Home/End）移动焦点并激活目标 Tab；只有活动 Tab `tabIndex=0`。无信号时 Signals Tab 仍可进入并显示明确空状态。

**D9 - 复用已有展示原语，缺失控件只加最小样式。**

面板、表格、分页、描述项、空/加载/错误态复用现有组件和 class。Tab 和 SOURCE segmented filter 在仓库中没有现成 primitive，直接在各自页面内用语义化 button/section 实现，并增加最小的 token-based 样式；不新增通用组件，不复制已有 primitive CSS。独立 HTML 原型不作为实现基准。

## Risks / Trade-offs

- **[Trade-off] detail 仍包含全量 `signal_ids`。** 保持兼容的代价是初始响应大小仍随信号数增长；本 Change 只界定摘要查询和渲染规模。后续若真实数据证明这是瓶颈，再提出版本化合同变更。
- **[Trade-off] source 暂不新增复合索引。** 现有 strategy/config 索引先缩小本地单策略数据集；四值 source 选择性低。若真实查询计划或数据量显示退化，再基于测量增加匹配过滤与排序的复合索引，而不是预先迁移。
- **[Risk] 前端详情计数与分页请求分两次完成。** 当前已完成 run 的 signal 关联不可变，因此可接受；未来若引入运行中可见性需重新评估。
- **[Risk] `Literal` 与模型枚举可能漂移。** API 测试应断言四个 `StrategySignal.SOURCES` 值均被接受，并断言未知值返回稳定 422；变更枚举时两处必须同步。
- **[Trade-off] 页面内实现 Tab/segmented filter。** 当前只有一个使用点，避免过早抽象；第二个使用点出现时再提取 primitive。

## Migration Plan

- **后端**：扩展 source 查询；新增 core 分页查询和 API 子资源端点。无 schema 变更、无数据迁移。回滚为删除新增参数透传与端点。
- **前端**：扩展 client；增加 SOURCE 筛选和 Backtest tabs；为 `Pagination` 增加可选总数。所有改动向后兼容，可随同 Change 回滚。
- **验证**：先以单元/组件测试覆盖新增合同和边界，再运行仓库现有完整质量门禁与 `openspec validate --strict`。

## Resolved Questions

- Backtest 信号页大小复用 `PAGE_SIZE = 20`。
- Signals Tab 显示 `signal_date` 与 `result`，避免逐条详情请求。
- SOURCE 列表首版不增加文本搜索；服务端 source 筛选已直接解决已定义问题。
