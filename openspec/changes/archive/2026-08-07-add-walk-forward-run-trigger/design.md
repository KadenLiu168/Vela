## Context

Walk-forward（WF）是 Vela 验证策略参数稳定性的核心能力。当前架构：

- **CLI 唯一入口**：`vela walk-forward --config <path> --database-url <url> --output <path>`（apps/cli/src/vela_cli/main.py:201），同步阻塞执行，打印报告。
- **API 只读**：`GET /api/walk-forwards`（列表）+ `GET /api/walk-forwards/{id}`（详情），无运行端点。`http-api-service` spec 明文 `MUST NOT add an endpoint that starts... a Walk-forward execution`。
- **前端只读**：`WalkForwardListPage.tsx` / `WalkForwardDetailPage.tsx` 仅浏览已持久化运行，无 Run 入口。回测的 Run 入口在 `DashboardPage.tsx`，不在列表页。
- **Runner 事务性一次写入**：`WalkForwardRunner.run()`（packages/core/src/vela_core/walk_forward/runner.py:54-109）在全跑完后才调 `persist_walk_forward_run`，`started_at`/`finished_at` 同时填且都 `nullable=False`。运行期间数据库**无记录**。
- **WF 耗时数量级**：参数空间 5×5×3×3=225 组合 × 3-4 窗口（2019-2024 / anchored_rolling / train=3 / test=1 / step=1）≈ 675-900 次回测，单次回测 1-2 秒，总耗时约 11-30 分钟。WF 强制 SQLite 源库（runner.py:55），训练回测在内存库跑（`_memory_snapshot` backup 整库到 `:memory:` engine），源库只承受 3-4 次 OOS 回测写 + 一次 persist。
- **现有异步基础设施**：apps/api 全局 grep 无 BackgroundTasks / asyncio / ThreadPoolExecutor / Celery / arq。现有 `POST /api/backtests/run` 和 `POST /api/strategy-signals/generate` 都是纯同步 `def`，HTTP 请求线程内跑完才返回。

约束：
- 项目是本地单机研究工具，单用户，不需要高并发。
- 极简栈：纯 FastAPI + SQLite，无 Redis / 外部任务队列。
- AGENTS.md 数据库安全：默认 `vela.db` 未经授权不得迁移；当前已滞后 6 个迁移。
- WF 强制 SQLite 源库 + 内存库 backup，同进程多 session 有潜在锁竞争。

## Goals / Non-Goals

**Goals:**
- 提供 `POST /api/walk-forwards/run` 端点，前端可一键发起 WF，与回测/信号的 UI 触发体验对齐（一键发起 + 可观察结果）。
- 异步执行不阻塞 event loop，单 worker 下其他 API 请求仍可响应。
- 运行状态可轮询：前端能区分 running / success / failed。
- 进程内失败可兜底：runner 抛异常时记录 failed 状态，不留 running 脏记录。
- CLI 路径对外行为不退化（仍同步阻塞、打印 run id 与报告）。
- 复用已验证的 `WalkForwardRunner` + `format_report()`，不重写 WF 核心逻辑。

**Non-Goals:**
- 多 config 支持（MVP 固定 `config/walk_forward_v1.yaml`）。
- 取消运行机制（用户误点只能等完成或重启进程）。
- 进度百分比查询（只有 running/success/failed 三态，不报"跑了几个窗口"）。
- 并发限流（同时多个 POST /run 会同时起多个 runner，消耗资源；MVP 不限流，文档警示）。
- 任务持久化到外部进程队列（不引入 Redis/arq；进程崩溃任务丢失，接受）。
- 回测/信号端点也异步化（本 change 只动 WF）。
- 历史已归档 WF 记录的 status 回填策略由 migration 处理，不在前端展示 running 态。

## Decisions

### Decision 1: 异步机制用 `asyncio.to_thread`，不用 BackgroundTasks / subprocess / 外部队列

**选择**：`async def run_walk_forward_endpoint(...): run_id = await asyncio.to_thread(_run_wf_blocking, ...)`。

**理由**：
- **不阻塞 event loop**：`to_thread` 把同步 runner 调用丢到默认线程池，event loop 继续响应其他请求。BackgroundTasks 在 starlette 实现里是同步执行，单 worker 时整个 API 卡死。
- **失败可兜底**：`try/except/finally` 包住 `to_thread` 调用，异常时 update `status="failed"` + `error_message`，不留 running 脏记录。BackgroundTasks 无此能力。
- **无新依赖**：`asyncio.to_thread` 是 Python 3.9+ 标准库。arq/Celery 要引入 Redis，与项目极简栈不符。
- **与现有同步 router 风格接近**：现有 `POST /api/backtests/run` 是同步 `def`，本端点只是包了一层 `async def` + `to_thread`，改动最小。

**Alternatives considered**：
- **FastAPI BackgroundTasks**：拒绝。starlette 实现里同步执行，单 worker 卡死整个 API；in-process 进程崩留 running 脏记录；无取消机制。是数十分钟 CPU 密集任务的反模式。
- **subprocess 调 CLI**（`vela walk-forward --config ...`）：备选。进程隔离更彻底、复用已验证 CLI、避免 SQLite 锁竞争，但要自己写 PID 跟踪 / 超时 kill / 退出码映射 / stdout 捕获，复杂度高。**留作 Open Question**：如果实测发现 `to_thread` 下 SQLite 锁竞争或单进程内存压力过大，再切 subprocess。MVP 不上。
- **arq/Celery + Redis**：拒绝。项目无 Redis，引入外部依赖不划算；本地单机工具不需要分布式任务队列的可靠性。

### Decision 2: 重构 `WalkForwardRunner` 为两阶段持久化

**选择**：runner 从"事务性一次写入"改为"两阶段持久化"：
1. **开始**：插入 `WalkForwardRun` 记录，`status="running"`、`started_at=now`、`finished_at=NULL`、`evidence_json={}`、`window_count=0`、其他字段先填占位（config/manifest/checksum 等可在 preflight 后填，或先填 config 后更新）。立即 commit 拿到 `run_id`。
2. **完成**：update 该记录，`status="success"`、`finished_at=now`、`window_count=len(results)`、`evidence_json=evidence`、落 `WalkForwardRunWindow` 子记录。
3. **失败**：在 runner 最外层 `try/except` 捕获任何异常，update 该记录 `status="failed"`、`error_message=str(exc)`、`finished_at=now`，然后 re-raise（让 API 层映射为结构化错误）。

**理由**：
- 现有事务性一次写入导致运行期间数据库无记录，"立即返回 run_id + 前端轮询"根本走不通。这是本 change 的真正核心，不是"补个 status 字段"。
- 两阶段持久化让前端能轮询 running 态，且失败时有明确 failed 记录可查。

**Alternatives considered**：
- **新增独立的 `walk_forward_run_status` 表**：拒绝。状态与 run 一一对应，没必要拆表；直接在 `WalkForwardRun` 加列更简单。
- **运行期间不落库，用进程内内存 dict 跟踪 status**：拒绝。进程崩就丢全部状态，且 detail 端点要查 status 必须读库。

**对 CLI 的影响**：CLI 路径复用重构后的 runner。CLI 同步阻塞调用 `runner.run()`，开始时插 running 记录、完成时更新 success、失败时更新 failed。对外行为不变（仍打印 run id 与报告）。CLI 不需要轮询，因为它是同步的。

**对现有 spec 的破坏**：
- `walk-forward-runner` spec "Source writes use the caller transaction" 要求 `SHALL neither commit nor roll back the caller-provided source session` + 事务性一次提交。两阶段持久化打破这条（开始时要 commit 一次拿到 id）。需 MODIFIED。
- `walk-forward-evaluation-history` spec "Persist successful Walk-forward runs and ordered windows" 要求 `persist one logically immutable WalkForwardRun only after every configured window... succeeds` + `no update/delete helper or HTTP mutation route`。两阶段 + status 流转打破这条。需 MODIFIED。

### Decision 3: `WalkForwardRun` 加 `status` + `error_message` 列，`finished_at` 改 nullable

**选择**：
- `status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")`，CHECK 约束 `status IN ('running','success','failed')`。
- `error_message: Mapped[str | None] = mapped_column(Text, nullable=True)`。
- `finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`（从 `nullable=False` 改）。
- 现有 `started_at` 保持 `nullable=False`（开始时必有）。
- 现有 `evidence_json` 保持 `nullable=False`，但开始时先填占位 `{}`，完成时更新为真实 evidence。
- 现有 `window_count` 保持 `nullable=False`，开始时填 0，完成时更新。

**历史记录 backfill**：migration 给历史已归档的 `WalkForwardRun` 记录 `status="success"`、`error_message=NULL`（这些记录都是成功跑完才落库的，finished_at 已有值）。

**Alternatives considered**：
- **复用 `BacktestRun.status` 的枚举值**（如 `success`/`failed`/...）：`BacktestRun` 有 status 字段但 WF 的状态语义不同（WF 没有 "running" 之外的中间态如 "pending"）。新增 WF 专属 `Literal["running","success","failed"]` 更清晰。
- **用 `finished_at IS NULL` 推断 running 态**：拒绝。显式 status 字段更可读、可查询、可加 CHECK 约束；NULL 语义推断易出错（如进程崩留下的 running 记录 finished_at 也是 NULL，但实际是 failed）。

### Decision 4: Run 按钮放 WalkForwardListPage，不放 Dashboard

**选择**：在 `WalkForwardListPage.tsx` 顶部加 "Run walk-forward" 按钮。

**理由**：
- **定位差异**：回测是日常操作（调仓信号生成流程的一部分），Run 在 Dashboard 与日常工作流对齐；WF 是低频研究工具（参数寻优、过拟合检验），不属于日常调仓流程。
- **列表页是研究入口**：研究员打开 WF 列表页 = "看历史 → 想跑新的 → 看新的"，Run 按钮放在这里符合研究工作流。
- **与回测不一致是合理的**：两个工具定位不同，UI 位置不同说得通。design.md 显式记录此差异。

**Alternatives considered**：
- **放 Dashboard 与回测对齐**：拒绝。Dashboard 是日常操作面板，WF 数十分钟长任务不属于日常面板；放 Dashboard 会让日常面板混入研究工具。
- **新建 WalkForwardDashboard 页**：拒绝。YAGNI，列表页已足够承载 Run 入口。

### Decision 5: 端点无参，config 路径从 `AppConfig` 注入

**选择**：`POST /api/walk-forwards/run` 无 query/body 参数。后端从 `AppConfig` 读取 `walk_forward_config_path`（新增配置项，MVP 默认 `config/walk_forward_v1.yaml`），传给 `WalkForwardRunner`。

**理由**：
- **避免路径穿越**：API 不接收客户端文件路径，杜绝读服务器任意 YAML 的安全风险。
- **避免文件系统耦合**：API 只交换数据，不交换路径。容器化部署时路径可能不存在。
- **与现有风格一致**：`backtest_router` 用 `app_config.strategy`（依赖注入），不接收路径。
- **当前只有一个 config**：多 config 支持是 YAGNI。

**Alternatives considered**：
- **接收 config 名字**（如 `?configName=walk_forward_v1`）：备选。未来要多 config 时再加，后端从白名单映射到路径。MVP 不上。
- **接收 config 路径**：拒绝。安全 + 耦合问题。
- **接收 config 内容**（POST body 传 YAML）：拒绝。WF config 较复杂，且与"配置文件驱动"的现有设计不符。

### Decision 6: 错误分类复用现有 `apps/api/src/vela_api/errors.py`

**选择**：runner 抛出的预期错误（config 缺失/无效、日历空、价格不足、无 scorable 组合等）映射为 `validation` 或 `operation_failed` 分类，与现有 `POST /api/strategy-signals/generate` 的错误处理一致。非预期异常走 `unexpected-error` 合约。

**理由**：现有 `errors.py` 已有结构化分类基础设施，复用避免另起炉灶。

### Decision 7: 前端轮询策略

**选择**：
- 点击 Run → 调 `runWalkForward()` → 拿到 `run_id` → 按钮禁用 + 显示 "Running..." → 每 5 秒轮询 `GET /walk-forwards/{run_id}` 读 `status`。
- `status==="success"` → 停止轮询 + 导航到 `/walk-forwards/{run_id}` 详情页。
- `status==="failed"` → 停止轮询 + 显示 `error_message` + 按钮恢复可点。
- `status==="running"` → 继续轮询。
- 轮询上限 60 次（5 分钟）后停止 + 提示"运行时间过长，请稍后刷新列表查看"。**注**：WF 可能跑 30 分钟，5 分钟上限会误报。改为：轮询无上限，但页面可见时才轮询（`document.visibilitychange` 监听），切到后台停止轮询。

**理由**：WF 长耗时，固定上限会误报；可见性监听避免后台空轮询。

## Risks / Trade-offs

- **[Risk] 进程崩溃留 running 脏记录** → `to_thread` 包 try/except/finally 兜底写 failed；但进程被 SIGKILL/断电时仍会留 running 记录。**Mitigation**：list/detail 接口对 `status="running"` 且 `started_at` 超过 1 小时的记录标记为 `stale`（前端显示"可能已中断"）。MVP 可只在前端显示 running 态时不假定一定完成。
- **[Risk] SQLite 锁竞争** → WF 训练在内存库跑，源库只承受 OOS 回测写 + persist。同进程并发读 list 应该 OK。但 `_memory_snapshot` 的 backup 操作持有源连接读锁，可能与同时进行的 OOS 写冲突。**Mitigation**：MVP 接受单用户单任务假设（文档警示同时多个 POST /run 可能锁竞争）；若实测冲突，切 subprocess（Decision 1 Open Question）。
- **[Risk] 同时多个 POST /run 资源耗尽** → 每个 runner 占一个线程 + 一份内存库 backup（整库 size）。**Mitigation**：MVP 不限流，文档警示；后续可加进程内信号量限流到 1。
- **[Risk] BREAKING 现有 spec** → 3 个 spec 的 requirement 要 MODIFIED（http-api-service read-only、walk-forward-runner 事务性、walk-forward-evaluation-history immutability）。**Mitigation**：proposal 明确标记 BREAKING；migration backfill 历史记录为 success；list/detail response 新增字段向前兼容。
- **[Trade-off] 无进度百分比** → 只有 running/success/failed 三态。研究员不知道"跑了几个窗口"。**Mitigation**：可接受，WF 是研究工具不是交互式操作；未来可加 `progress` 字段（window_ordinal / total_windows）但不在 MVP。
- **[Trade-off] 无取消机制** → 误点 Run 只能等完成或重启进程。**Mitigation**：按钮 disabled + 明确提示"运行中，预计 11-30 分钟"；未来可加 cancel 端点（kill 线程或 subprocess）。
- **[Risk] CLI 行为退化** → 重构 runner 为两阶段持久化，CLI 路径也受影响。**Mitigation**：CLI 仍同步阻塞调用 `runner.run()`，对外行为不变（打印 run id 与报告）；增加 CLI 测试覆盖确保不退化。

## Migration Plan

1. **编写 alembic migration**（不强制应用到默认 `vela.db`）：
   - `walk_forward_run` 加 `status` 列（`String(16), nullable=False, default="success"`）+ CHECK 约束。
   - 加 `error_message` 列（`Text, nullable=True`）。
   - `finished_at` 改 `nullable=True`。
   - backfill 历史记录 `status="success"`（所有已存在记录 finished_at 非空，视为成功）。
2. **重构 `WalkForwardRunner`**：抽出 `_persist_running()` / `_persist_success()` / `_persist_failure()`，CLI 与 API 共用。
3. **更新 `walk_forward` persistence helper**：新增 update 函数。
4. **加 API 端点**：`POST /api/walk-forwards/run`（async + to_thread）+ list/detail response 加 status/error_message。
5. **加前端 Run 按钮 + 轮询**。
6. **测试**：极小参数空间端到端 + mock runner 失败路径 + 前端组件测试。
7. **用户授权后** `alembic upgrade head` 应用到默认库（遵守 AGENTS.md）。

**回滚**：本 change 未应用到默认库前，回滚只需删除 change 目录 + revert 代码。应用后回滚需写 downgrade migration（drop 新列、恢复 finished_at nullable=False），但历史 backfill 的 `status="success"` 不可逆（无原始状态信息，但这些记录本来就是成功的，回滚后无 status 列也无影响）。

## Open Questions

1. **subprocess 退路**：若 `to_thread` 实测发现 SQLite 锁竞争或内存压力，是否切 subprocess 调 CLI？需在实施阶段做一次小规模实测（跑一个窗口的 WF，同时并发 list 请求，观察是否锁冲突）。
2. **并发限流**：MVP 不限流，但若用户误触多次 Run 怎么办？可在端点层加"已有 running 记录时拒绝新请求"的简单防护，但这会阻止多策略并行研究。倾向不加，文档警示。
3. **stale running 检测**：list/detail 是否对超时 running 记录标记 stale？MVP 可只在前端显示"运行中（已超 X 分钟）"提示，后端不主动判断。
4. **`AppConfig` 注入 `walk_forward_config_path`**：是加到 `AppConfig` 顶层字段，还是复用 `application-configuration` capability 的现有机制？需看 `AppConfig` 现有结构决定。
