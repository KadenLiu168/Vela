## Why

Walk-forward currently produces persisted OOS backtests but its configuration, window-to-run mapping, parameter-selection evidence and aggregate report exist only in one CLI process. Users cannot later audit which OOS runs belonged together, compare completed evaluations, or review the evidence through the API and Web application.

## What Changes

- 新增完整成功的 Walk-forward evaluation 持久化模型：顶层运行记录及有序窗口子记录，关联每个 selected OOS `BacktestRun`。
- 保存完整 WF 配置快照、解析后的基础策略配置、`wf_provenance_v1` canonical checksum、执行前 compact input manifest/checksum、证据契约版本、开始/完成时间和结构化聚合 evidence；路径保留用于展示但不参与有效配置 checksum。
- 输入 manifest 保存有界 ETF 本地 id/身份/上市日期、完整官方 session 序列、基准月末判定使用的 following-session sentinel、实际加载价格行计数与 checksum；checksum 覆盖当前执行可能使用的 ETF id 映射及策略可见的 `close_price`/`factor_hfq`，但不重复保存全部原始价格行。
- 每个窗口保存边界、选中参数、生成的 OOS version、candidate/eligible/skipped 数量、固定类别的跳过原因计数、train Sharpe 和唯一 OOS run 关联；指标值继续由关联的持久化 OOS run/benchmark 记录拥有。
- 仅在所有窗口、双基准和证据聚合成功后，于现有 caller-owned transaction 中写入 WF 父子记录；任一失败仍整体回滚，不持久化失败 WF 审计记录。
- 重复执行始终创建新的 WF run，但相同有效配置和输入数据产生可比较的 checksum；不自动复用旧结果。
- 新增限定当前策略、只读且分页边界固定的 Walk-forward 列表与详情 API，不通过 HTTP 启动参数搜索；响应使用完整、明确的 Pydantic 契约。
- 将现有 Backtest、Backtest Signals 与 Signal 的 by-id 读取边界改为当前 `strategy_id` 内跨 `config_version` 可读，使 `wf-*` OOS 证据链可以完整访问，同时继续隐藏其他策略记录。
- 新增 Walk-forward History 与独立 Detail 页面，展示元数据、证据充分性、完整 OOS/双基准与 active/downside risk metrics、IS/OOS gap 和参数稳定性，并链接到已有 OOS Backtest Detail 及其 Signal 证据链。
- CLI 完成后打印持久化 WF run id；保留现有即时文本/`--output` 报告。
- 明确不回填历史 OOS runs、不持久化失败运行、不扩展 Dashboard、不生成自动评分/pass-fail，也不连续拼接 OOS 净值曲线。

## Capabilities

### New Capabilities

- `walk-forward-evaluation-history`: 定义成功 WF 运行及窗口的持久化、配置/数据 provenance、查询、重复执行和历史兼容契约。

### Modified Capabilities

- `walk-forward-runner`: 在现有原子事务末尾持久化完整成功的结构化 evaluation 并返回稳定 run id，不保存失败运行。
- `cli-database-initialization`: `vela walk-forward` 输出持久化 evaluation id，同时保留即时报告行为。
- `http-api-service`: 增加只读、分页的 Walk-forward history/detail，并将现有 Backtest/Signal by-id 读取调整为同策略跨配置版本可读。
- `web-frontend-app`: 增加 Walk-forward 列表、详情、导航和可用的 OOS Backtest/Signal 深链接，不改变 Dashboard。

## Impact

- 影响 `packages/core` 的 Walk-forward runner/report、SQLAlchemy 模型、查询 helper 和 Alembic migration。
- 增加 FastAPI Walk-forward router/schema/client 契约及 React history/detail 页面和路由；调整现有 Backtest/Signal by-id 查询的配置版本过滤。
- 此 Change 应在前两个 Change 稳定后实施，以持久化并展示其最终 evidence shape 和 expanded metrics。
- migration 与验证只使用测试自有文件型 SQLite；不回填或写入默认 `vela.db`，不新增第三方依赖。
