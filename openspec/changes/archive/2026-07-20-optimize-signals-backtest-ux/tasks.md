## 1. Backend - Signals SOURCE 过滤

- [x] 1.1 先扩展 `packages/core` 单测，覆盖 source 在分页前过滤、四个 `StrategySignal.SOURCES` 值和省略 source 的既有行为；再为 `list_strategy_signals()` 增加可选 `source: str | None` 并追加过滤条件。
- [x] 1.2 先扩展 `apps/api/tests/test_strategy_signal_history.py`，覆盖四个合法值、未知/空/字符串 `null` 的稳定 422 validation 响应和过滤后的分页顺序；再给 `list_strategy_signals_endpoint` 增加 `Literal["manual", "scheduled", "backtest", "legacy"] | None` 查询参数并透传给 core。
- [x] 1.3 保持既有响应字段、默认 limit/offset 和无 source 时的行为不变；不新增数据库索引或迁移。

## 2. Backend - Backtest 信号分页端点

- [x] 2.1 先在 `packages/core/tests/` 增加失败测试，覆盖作用域匹配、foreign strategy/config 返回 `None`、空集合、稳定 `(signal_date, id)` 排序、offset/limit、非法 `limit < 1` / `offset < 0` 和不过滤 status。
- [x] 2.2 在 `packages/core` 增加 `BacktestSignalSummaryEntry` 与 `list_backtest_signals(session, *, run_id, strategy_id, config_version, limit, offset=0)`：公共函数自身校验 limit/offset，用轻量查询验证 run 作用域，然后直接按 `StrategySignal.backtest_run_id` 查询四个摘要字段并在 SQL 中应用排序、offset 和 limit；禁止通过 `get_backtest_result()` 或 `run.signals` 全量加载后切片；同步从 `packages/core/src/vela_core/__init__.py` 导出新增类型和函数，保持 API 现有 package-root import 风格。
- [x] 2.3 先在 `apps/api/tests/test_backtest_run.py` 增加端点测试，覆盖响应 `{ signals: [...] }`、默认/自定义分页、稳定顺序、空集合、unknown 与 foreign strategy/config 的同形 404、非法 limit/offset 的稳定 422，以及逐页合并后无遗漏/重复且等于 detail `signal_count`。
- [x] 2.4 在 `apps/api/src/vela_api/main.py` 新增 `GET /api/backtests/{run_id}/signals`（limit 1–100 默认 20，offset >= 0）；加载当前配置后只调用 core 分页函数，将 `None` 映射为现有 Backtest not-found 错误形态，并用现有 response helper 风格序列化四个字段。
- [x] 2.5 更新显式枚举路由的 API health/database-session/contract 测试，使新增第 14 个端点被纳入覆盖；保持 `GET /api/backtests/{run_id}` 合同不变。

## 3. Frontend - client 层

- [x] 3.1 先扩展 `apps/web/src/api/client.test.ts`：验证 `listStrategySignals` 只在 source 存在时编码参数，并验证 `listBacktestSignals(runId, limit, offset)` 对 run id 和分页参数正确编码。
- [x] 3.2 扩展 `listStrategySignals(limit, offset, source?)`，新增 `BacktestSignalSummary` / `BacktestSignalsResponse` 和 `listBacktestSignals`；统一消费响应字段 `signals`，不引入 `signal_summaries` 别名。

## 4. Frontend - Signals SOURCE 筛选

- [x] 4.1 先新增 `SignalListPage.test.tsx` 组件测试，覆盖合法 URL 初始化、四个筛选切换、切换重置 offset、All 省略 source、非法/空/`null` URL 规范化、保留其他 query/hash、筛选空状态和快速切换时旧请求不覆盖新状态。
- [x] 4.2 在 `SignalListPage` 内增加 `StrategySignalSource` type guard 和 SOURCE 分段按钮组（All / Manual / Scheduled / Backtest / Legacy），使用 `role="group"`、可访问名称与 `aria-pressed`；不增加当前页文本搜索。
- [x] 4.3 用 `URL` / `URLSearchParams` 读取和更新 source：合法值恢复筛选，非法值规范化为 All，切换时 `history.replaceState` 只增删 source 并保留其他 query/hash；筛选变化把 offset 重置为 0，且请求状态同时按 source 与 offset 防止陈旧数据闪现。
- [x] 4.4 复用现有 panel/table/feedback primitives，只为分段控件增加最小的页面范围 token-based 样式；source 首页面为空时显示能区分“全部历史为空”和“当前来源为空”的 EmptyState。

## 5. Frontend - Pagination 与 Backtest 详情 Tab

- [x] 5.1 先新增 `Pagination.test.tsx`，覆盖未传总数时保持既有行为，以及传入 `totalCount` 后在部分末页和总数恰好为页大小整数倍时准确禁用 Next；再为 `Pagination` 增加可选 `totalCount` prop。
- [x] 5.2 先新增 `BacktestDetailPage.test.tsx`，覆盖默认 Overview、ARIA 关联、ArrowLeft/ArrowRight/Home/End 自动激活、正数计数首次激活才请求、零计数不请求、分页 offset 与精确末页、表格字段/链接、空/加载/错误状态、切回缓存页，以及 `backtestId` 变化重置和旧响应隔离。
- [x] 5.3 `BacktestDetailPage` 增加页面内两 Tab 状态与语义（`tablist` / `tab` / `tabpanel`、id/aria-controls/aria-labelledby、active tabIndex）；Overview 保留运行信息、指标、净值曲线和参数，并作为默认 Tab。
- [x] 5.4 Signals Tab 在 `signal_count > 0` 且首次激活时调用 `listBacktestSignals`，用 20 条页大小渲染 Signal # / Signal date / Result / 操作表，向 `Pagination` 传入 `signal_count`；实现 offset/run id 请求隔离，处理 loading/error/empty，且不显示 source 分类。
- [x] 5.5 `backtestId` 变化时重置为 Overview、offset 0 和未加载 Signals 状态；复用现有 panel/table/Pagination/DescriptionItem/EmptyState/FeedbackMessage，只为 Tab 增加最小页面范围 token-based 样式，不抽取新的通用 Tab 组件。

## 6. 校验与收尾

- [x] 6.1 运行新增测试和受影响测试，再运行完整质量门禁：后端 `pytest`、`ruff check .`、`mypy`；前端 `npm test`、`npm run lint`、`npm run lint:css`、`npm run typecheck`、`npm run build`。
- [x] 6.2 更新 `docs/ux-analysis-signals-backtest.md` 的最终决策：删除当前页搜索建议，说明分页摘要使用数据库级 limit/offset，并明确 detail 仍保留全量 `signal_ids` 的兼容性权衡；原型继续只作为非规范性示意，不要求同步其手写样式。
- [x] 6.3 运行 `openspec validate optimize-signals-backtest-ux --strict --no-interactive` 并确认通过；核对 git diff 仅包含本 Change 明确范围内的实现、测试和相关文档。
