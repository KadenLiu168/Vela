## Why

研究工作流里两个 Signals / Backtest 界面痛点长期影响复盘效率：

1. **Signals 列表有 SOURCE 展示、无筛选**。`strategy_signal.source` 字段（manual / scheduled / backtest / legacy）已在列表以彩色徽章呈现，但全链路（core 查询函数、API、前端 client）都没有 source 维度，用户只能逐页肉眼扫徽章来找某类信号。
2. **Backtest 详情的 Signals 把其余信息挤到最下方**。API 一次性返回完整 `signal_ids` 且无摘要分页接口；详情页按“运行信息 -> 指标 -> Signals（整行链接列表）-> 净值曲线 -> 参数”顺序铺开。回测跨数百交易日时，净值曲线和参数被长列表推到页面下方，且每行只有一个 id 链接，信息密度低。

两者都是现有数据缺少合适查询或组织入口的问题，可以在保持既有接口兼容的前提下，以有限改动改善研究复盘体验。

## What Changes

- **Signals 列表增加 SOURCE 服务端筛选**
  - API `GET /api/strategy-signals` 新增可选 `source` 查询参数（`Literal` 校验 4 值枚举，非法值 422；省略参数表示全部）。
  - core `list_strategy_signals()` 增加 `source` 过滤。不新增索引：当前本地 MVP 先复用 `(strategy_id, config_version)` 主作用域索引，并以测试和后续实际数据量验证是否需要复合索引。
  - 前端 client `listStrategySignals(limit, offset, source?)` 仅在筛选激活时传 `source`。
  - `SignalListPage` 增加分段筛选条（全部 / Manual / Scheduled / Backtest / Legacy）；筛选状态同步到 URL `?source=`，切换时回到第一页。
- **Backtest 详情改为 Tab 化 + 信号紧凑分页表**
  - 详情页拆为「概览 Overview」（运行信息 + 指标 + 净值曲线 + 参数，默认可见）与「信号 Signals (N)」两个 Tab，使用户无需先越过完整 Signals 列表即可查看概览内容。
  - Signals Tab 用紧凑分页表（列：Signal # · Signal date · Result · 操作）。
  - 新增 `GET /api/backtests/{run_id}/signals?limit&offset`，返回 `{ signals: [...] }`，每项包含 `signal_id`、`signal_date`、`result`、`backtest_run_id`。core 使用按 `backtest_run_id` 的直接 SQL 查询和数据库级 `LIMIT/OFFSET`，不通过 `get_backtest_result()` 全量加载关系后再切片。
  - `GET /api/backtests/{run_id}` 继续返回既有 `signal_ids` 与 `signal_count`，用于兼容现有调用方和 Tab 计数；因此本 Change 限制摘要页请求和页面渲染规模，但不宣称消除 detail 响应中 `signal_ids` 的全量传输。
  - Signals Tab 不做来源分类：数据库约束保证关联到 backtest run 的信号 source 恒为 `backtest`。
  - `Pagination` 增加向后兼容的可选总数能力，Backtest Signals 使用 `signal_count` 准确判断下一页，避免总数恰好为页大小整数倍时出现空白下一页。

## Capabilities

### New Capabilities

_（无新增顶层能力；改动落在现有 API 与前端能力上。）_

### Modified Capabilities

- `http-api-service`：
  - `GET /api/strategy-signals` 增加可选 `source` 查询参数。
  - 新增 `GET /api/backtests/{run_id}/signals`，按 limit/offset 返回该回测的信号摘要。
- `web-frontend-app`：
  - Signals 列表页增加 SOURCE 分段筛选条并同步 URL。
  - Backtest 详情页改为 Tab 布局，Signals Tab 消费分页信号接口并渲染紧凑表。

## Impact

**后端（apps/api + packages/core）**

- `apps/api/src/vela_api/main.py`：`list_strategy_signals_endpoint` 增加 `source` 参数；新增 `backtest_signals_endpoint`，调用 core 并把不存在或不属于当前 strategy/config 的 run 统一映射为 404。
- `packages/core/src/vela_core/strategy_signal_report.py`：`list_strategy_signals()` 增加 source 过滤；新增分页摘要类型与 `list_backtest_signals(session, *, run_id, strategy_id, config_version, limit, offset=0)`，先验证 run 作用域，再按现有 `backtest_run_id` 索引直接分页查询信号。
- 不新增数据库迁移或索引。

**前端（apps/web）**

- `apps/web/src/api/client.ts`：`listStrategySignals` 增加 `source` 参数；新增 `listBacktestSignals` 及响应类型。
- `apps/web/src/pages/SignalListPage.tsx`：分段筛选条、URL 初始化/规范化/同步和筛选状态。
- `apps/web/src/pages/BacktestDetailPage.tsx`：Tab 容器、概览面板、懒加载的 Signals 分页表。
- `apps/web/src/components/Pagination.tsx`：增加可选 `totalCount`，保持现有调用方行为不变。

**测试**

- 后端：core 与 API 测试覆盖 source 过滤、非法 source、分页顺序/边界、空集合、作用域 404、参数 422，以及分页集合与 detail `signal_count` 一致。
- 前端：client、`Pagination`、Signals 列表和 Backtest 详情测试覆盖 URL、筛选、Tab 键盘语义、懒加载、分页边界、空/加载/错误状态和 run id 切换。

**界面风格（必须遵守）**

新增 UI MUST 复用当前页面已有的 `.dashboard-panel`、`.holdings-table`、`Pagination`、`DescriptionItem`、`EmptyState`、`FeedbackMessage` 与 `tokens.css` 变量。仓库当前没有通用 Tab 或 segmented-control primitive，因此允许为这两个控件增加最小、页面范围明确、基于 token 的样式；不得把页面内控件过早抽象成新的通用组件，也不得复制已有 panel/table/feedback 样式。`docs/prototype/signals-backtest-redesign.html` 仅为沟通示意稿，不是样式基准。

**兼容性**

`source` 是可选参数，新信号端点是增量接口，`Pagination.totalCount` 是可选 prop；`GET /api/backtests/{run_id}` 的既有字段保持不变。现有调用方无需修改。
