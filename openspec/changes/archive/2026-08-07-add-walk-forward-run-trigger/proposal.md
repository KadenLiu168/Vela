## Why

Walk-forward 是 Vela 验证策略参数稳定性的核心能力，但当前只能从 CLI 触发（`vela walk-forward --config <path>`，apps/cli/src/vela_cli/main.py:201）。API 层只有 `GET /api/walk-forwards` 和 `GET /api/walk-forwards/{id}`（apps/api/src/vela_api/walk_forward_router.py），前端 WF 列表/详情页只能浏览已持久化的运行（apps/web/src/pages/WalkForwardListPage.tsx）。这是后端核心研究能力在前端完全不可触发的最大缺口。研究者必须切到终端跑 CLI、记下 run id、再回前端查看，工作流割裂。

## What Changes

- **新增 `POST /api/walk-forwards/run` 端点**：无参（MVP 固定复用 `config/walk_forward_v1.yaml`，从 `AppConfig` 注入路径，不接收客户端文件路径以避免路径穿越与文件系统耦合），异步触发 `WalkForwardRunner.run()`，立即返回 `walk_forward_run_id` 供前端轮询。
- **重构 `WalkForwardRunner` 为两阶段持久化** **BREAKING**：当前 runner 是事务性一次写入（runner.py:73-107 在全跑完后才调 `persist_walk_forward_run`，`started_at`/`finished_at` 同时填且都 `nullable=False`），运行期间数据库无记录、无法轮询。改为：开始时插入 `status="running"` 记录拿到 id（`finished_at` 改 nullable），完成时 update 为 `status="success"` 并落 windows/evidence，失败时 update 为 `status="failed"` + `error_message` + `finished_at`。CLI 路径同步更新，对外行为不退化（CLI 仍打印 run id 与报告）。
- **`WalkForwardRun` 模型加 `status` 与 `error_message` 列** **BREAKING**：`status: Literal["running","success","failed"]`、`error_message: str | None`、`finished_at` 改 `nullable=True`。配套 alembic migration（编写但不强制应用到默认库，遵守 AGENTS.md 数据库安全）。
- **异步执行机制用 `asyncio.to_thread`**，**不**用 FastAPI BackgroundTasks。BackgroundTasks 在 starlette 实现里同步执行，单 worker 时整个 API 卡死，且进程崩溃会留 running 脏记录、无取消机制。`asyncio.to_thread` 不阻塞 event loop、可在 try/except/finally 兜底写 failed 状态、无新依赖（不引入 Redis/arq）。
- **前端 WF 列表页加 "Run walk-forward" 按钮**：触发后端 run 端点 → 按钮禁用并显示 running → 轮询 `GET /walk-forwards/{id}` 读 `status` → success 跳详情、failed 显示错误。Run 按钮放列表页而非 Dashboard，因为 WF 是低频研究工具，不属于日常调仓流程（与回测 Run 在 Dashboard 的定位差异在 design.md 说明）。
- **复用现有 `apps/api/src/vela_api/errors.py` 结构化错误分类**：参数非法/日历缺失/价格不足等返回 validation/operation_failed 分类，与现有端点一致。
- **命令面板（CommandPalette）可选追加 "Run walk-forward" 动作**，与现有 Run backtest / Generate signal 对齐。

## Capabilities

### New Capabilities
<!-- 无新 capability。异步执行是 http-api-service 的实现细节；状态流转是 walk-forward-evaluation-history 的扩展；Run 入口是 web-frontend-app 的扩展。 -->

### Modified Capabilities
- `http-api-service`: 打破现有 "Walk-forward API is read-only" requirement，新增 `POST /api/walk-forwards/run` 异步触发端点（立即返回 run_id，后台执行，可轮询状态）。**BREAKING**。
- `walk-forward-runner`: 打破现有 "Source writes use the caller transaction" requirement 的事务性一次写入约束，允许两阶段持久化（开始插 running 记录 → 完成更新 success/failed），CLI 与 API 共用同一 runner 且 CLI 对外行为不退化。**BREAKING**。
- `walk-forward-evaluation-history`: 打破现有 "Persist successful Walk-forward runs and ordered windows" requirement 的 immutability 与 "no HTTP mutation route" 约束，允许 `WalkForwardRun` 在 running→success/failed 状态间流转，并暴露 run 触发端点。**BREAKING**。
- `web-frontend-app`: 在 WF 列表页 requirement 基础上追加 Run 入口能力（按钮 + 运行中禁用 + 状态轮询 + 完成跳详情）。

## Impact

- **新增/修改后端代码**:
  - `packages/core/src/vela_core/walk_forward/runner.py`：重构 `WalkForwardRunner.run()` 为两阶段持久化，抽出 `_persist_running()` / `_persist_success()` / `_persist_failure()` 内部方法。
  - `packages/core/src/vela_core/walk_forward/persistence.py`：新增 update 状态的 helper（当前只有 `persist_walk_forward_run` 一次性写入）。
  - `packages/core/src/vela_core/models/walk_forward.py`：`WalkForwardRun` 加 `status`、`error_message` 列，`finished_at` 改 `nullable=True`。
  - `alembic/versions/`：新迁移加列 + 调整 nullable 约束（不强制应用到默认 `vela.db`）。
  - `apps/api/src/vela_api/walk_forward_router.py`：新增 `POST /api/walk-forwards/run` 端点（`async def` + `asyncio.to_thread`），list/detail response 增加 `status`/`error_message` 字段。
  - `apps/api/src/vela_api/schemas.py`：新增 `WalkForwardRunResponse`、`WalkForwardRunAcceptedResponse` schema；现有 list/detail response schema 加 status/error_message。
  - `apps/api/src/vela_api/dependencies.py` 或 `application-configuration`：`AppConfig` 增加 `walk_forward_config_path` 注入（MVP 固定 `config/walk_forward_v1.yaml`）。
- **修改 CLI**:
  - `apps/cli/src/vela_cli/main.py`：`run_walk_forward()` 复用重构后的 runner，对外行为不退化（仍同步阻塞、打印 run id 与报告）。
- **修改前端**:
  - `apps/web/src/api/client.ts`：新增 `runWalkForward(): Promise<WalkForwardRunAcceptedResponse>`，`WalkForwardPageResponse`/`WalkForwardDetailResponse` 增加 `status`/`error_message` 字段。
  - `apps/web/src/pages/WalkForwardListPage.tsx`：加 "Run walk-forward" 按钮 + 运行中禁用 + 轮询逻辑 + 成功跳详情/失败显示错误。
  - `apps/web/src/components/CommandPalette.tsx`（可选）：追加 "Run walk-forward" 动作。
- **测试**:
  - 后端契约测试：合法触发返回 run_id + accepted；非法（如 config 缺失/日历空）返回 4xx 结构化错误。
  - 后端端到端（测试库 tmp_path）：用极小参数空间（1 组合 × 1 窗口）跑 running→success；mock runner 跑 running→failed。
  - 前端测试：点击 Run 调 `runWalkForward`、运行中按钮 disabled、成功导航详情、失败显示错误。
- **依赖**: 无新增运行时依赖。`asyncio.to_thread` 是 Python 3.9+ 标准库。
- **数据库**: 新 alembic migration 改 `walk_forward_run` 表结构；默认库 `vela.db` 当前已滞后 6 个迁移，本 change 编写迁移但不强制应用（遵守 AGENTS.md），需用户授权 `alembic upgrade head` 才能默认库跑通。
- **BREAKING 影响**:
  - 现有 `http-api-service` spec 明文 "MUST NOT add an endpoint that starts... a Walk-forward execution" → 改为 SHALL provide。
  - 现有 `walk-forward-runner` / `walk-forward-evaluation-history` spec 要求事务性一次写入 + immutability → 改为允许两阶段 + 状态流转。
  - 历史已归档的 `WalkForwardRun` 记录无 `status` 列 → migration 需要 backfill 为 `status="success"`（这些记录都是成功跑完才落库的）。
  - list/detail API response 增加 `status`/`error_message` 字段，向前兼容（新增字段）。
