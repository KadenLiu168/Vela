## Context

`backtest_run` 表当前字段（见 `backtest-run-model` spec）：`id, strategy_id, config_version, start_date, end_date, parameters_json, started_at, finished_at, status, error_message, total_return, annualized_return, max_drawdown, sharpe_ratio, volatility, created_at, updated_at` 及 `signals` 关系。它记录了**参数快照**（`parameters_json`）与指标，但**无任何输入数据版本信息**。`run_backtest` 在 `backtest_runner.py` 调用 `load_price_panel` 加载价格面板（依赖 `market-price-panel-loading`），随后 `strategy_equity_curve` 会另行读取持仓 ETF 在整个请求区间内的 `close_price` 与 `factor_hfq`。两次运行之间若数据漂移（增量同步、复权重算、缺口补录、HFQ 整条平移），run 表无法先排除数据差异。本变更在 run 上记录一份覆盖两类计算输入的数据指纹。

约束：
- 本地 SQLite（无原生 JSON 类型，SQLAlchemy `JSON` 用 TEXT 存）。
- 个人研究系统，先 checksum 不存全量（可重放后置为独立 change）。
- 用户将重置数据库，但 checksum 仍用于监控未来漂移。

## Goals / Non-Goals

**Goals:**
- `BacktestRun` 持久化 `data_snapshot_json`（`min_trade_date`, `max_trade_date`, `trading_day_count`, `active_etf_count`, `per_etf_row_counts`, `data_checksum`）。
- `run_backtest` 加载从 lookback buffer 至请求 `end_date` 的 active-ETF `price_panel` 后计算并通过 `BacktestResultRunInput` → `persist_backtest_result` 落库（同一 caller-managed 事务，不新增 commit）；历史信号继续逐调仓日截断面板，避免未来数据泄漏。
- `data_checksum` 对 `(etf_id, trade_date, close_price, factor_hfq)` 确定性哈希，检测漂移。

**Non-Goals:**
- 不存全量数据（不做可重放快照）——独立后续 change。
- 不改策略计算 / 指标语义。
- 不暴露 API / CLI / 前端（UI 展示为后续）。
- 不处理存量旧 run（用户重置库）。
- 快照不在 `BacktestRunResult` 返回值中暴露（保持返回类型不变）。
- 不记录代码/依赖版本，也不解决当前全局 latest-wins 信号读取；因此 checksum 相同只表示本 Change 定义的市场数据输入相同，不能单独证明结果可复现。

## Decisions

### D1: 单 JSON 摘要字段而非多列
用单个 `data_snapshot_json`（SQLAlchemy `JSON`）存摘要。理由：字段多为诊断性、可变结构（`per_etf_row_counts` 是 dict），单 JSON 列避免 schema 膨胀且 SQLite 友好。备选（拆成独立列）：更利于 SQL 查询，但 `per_etf_row_counts` 仍需 JSON 或单独表，且本期不查询只展示，单 JSON 更简单。

类型选型说明：仓库中已有 JSON 列 `parameters_json` 和 `positions_json` 使用 `Text` 类型 + 手动 `json.dumps`。`data_snapshot_json` 使用 `JSON` 类型以获取自动 dict↔str 序列化，简化读写。SQLite 上 `JSON` 底层仍存为 TEXT，兼容性不变。`per_etf_row_counts` 的 JSON object key 为十进制 ETF id 字符串（例如 `{"12": 252}`），避免 Python `int` key 经 JSON 往返后变为 `str` 的歧义。未来可统一迁移现有 `Text` JSON 列为 `JSON` 类型，但不属于本 Change 范围。

### D2: data_checksum 用确定性哈希（sha256 over 规范化行序）
对覆盖范围内所有价格行，按 `(etf_id, trade_date)` 排序；每行以 UTF-8 编码的紧凑 JSON 数组 `[etf_id, trade_date.isoformat(), str(close_price), str(factor_hfq)]` 加一个换行写入 hash 流，再算 sha256。结构化的逐行编码使字段边界无歧义，`Decimal` 用 `str(value)` 保持加载值的确定性表示。理由：确定性（同输入同输出）、敏感（任一行变即变）、廉价。备选（对 `factor_hfq` 列求聚合 sum/mean）：不同分布可得出相同聚合值，不敏感，排除。

注：字段名 `data_checksum` 而非 `factor_checksum`，因为哈希覆盖 `close_price` + `factor_hfq` 两列，不仅是 factor。

### D3: 计算时机在 `load_price_panel` 之后、指标计算之前
`run_backtest` 已有 price_panel 加载点。将其 `end_date` 从最后一个调仓日扩展为请求的 `end_date`，使同一个面板覆盖策略 lookback、每个调仓日信号计算，以及净值计算使用的区间末尾价格；净值计算复用该已加载面板，避免两次数据库读取之间的数据写入使摘要与实际输入错位。`generate_historical_strategy_signals` 已按 `price.trade_date <= rebalance_date` 截断每个信号可见数据，故不改变或引入前视。加载后立即从该面板计算摘要，暂存为字典，在 `persist_backtest_result` 调用时通过 `BacktestResultRunInput` 传入并落库到 `BacktestRun` 行。已有 caller-managed 事务，不新增 commit。

数据流：`load_price_panel(...)` → 计算 snapshot dict + 复用于净值计算 → 传入 `BacktestResultRunInput.data_snapshot_json` → `persist_backtest_result` 写入 `BacktestRun.data_snapshot_json`。

### D4: 迁移用 SQLite 兼容方式加 JSON 列
新增 Alembic 迁移添加 `data_snapshot_json`（nullable JSON）。upgrade 直接用 `op.add_column`；downgrade 用 `op.batch_alter_table` 包裹 `drop_column`（SQLite 不支持直接 DROP COLUMN）。沿用仓库现有 SQLite 迁移模式。

## Risks / Trade-offs

- [Risk] JSON 列在 SQLite 不强制结构。 → Mitigation：只由快照构造器生成固定字段；迁移测试验证 JSON 可写和 ORM 往返，迁移只加列。
- [Risk] `price_panel` 巨大时 checksum 计算开销。 → Mitigation：个人 ETF 量级（数百 ETF × 数千日）可忽略；未来扩量再优化。
- [Trade-off] 仅 checksum 不能还原旧数据重跑——已决定后置为独立 change。
- [Trade-off] `data_snapshot_json` 使用 SQLAlchemy `JSON` 类型而非仓库已有的 `Text` 惯例（`parameters_json` / `positions_json` 均用 `Text` + 手动 `json.dumps`）。`JSON` 提供自动序列化，底层仍为 TEXT，功能等价。未来可统一迁移但非本 Change 范围。
- [Edge case] partial 状态 run（部分 signal 失败）仍写入快照——快照在 signal 生成前计算，反映加载的数据，不依赖 signal 结果。
- [Edge case] 面板为空（请求区间的市场日期来自非 active ETF，或 active ETF 在范围内无行）——仍持久化摘要：`min_trade_date`/`max_trade_date` 为 `null`，两个计数为 `0`，`per_etf_row_counts` 为 `{}`，`data_checksum` 为空字节流的 sha256；该 run 的 `partial` 语义仍由既有信号生成决定。
- [Trade-off] 此摘要覆盖启动时选定 active ETF 的原始 `close_price`/`factor_hfq` 行，而非保存全量数据；它足以定位这些输入的漂移，却不能重放数据，也不能代表代码版本或信号隔离状态。
- [Risk] 迁移失败中途。 → Mitigation：沿用现有 migration 测试模式（upgrade/downgrade 往返）。

## Migration Plan

1. 新增 Alembic 迁移：`ADD COLUMN data_snapshot_json` (nullable JSON)。upgrade 用 `op.add_column`，downgrade 用 `op.batch_alter_table` 包裹 `drop_column`（SQLite DROP COLUMN 兼容）。
2. 更新 `BacktestRun` 模型字段 + `BacktestResultRunInput` 字段。
3. 更新 `persist_backtest_result` 传入 `data_snapshot_json` 到 `BacktestRun(...)` 构造。
4. 更新 `run_backtest` 将 `load_price_panel` 覆盖至请求 `end_date`，在其后计算 snapshot dict，通过 `BacktestResultRunInput` 传入；保持每个历史信号只接收不晚于其调仓日的价格。
5. 更新现有模型测试 `test_backtest_run_optional_completion_fields_are_nullable` 包含 `data_snapshot_json`。
6. 迁移测试（upgrade 后列存在、JSON 可写、downgrade 移除）。
7. 回滚：Alembic downgrade 移除列；代码与 schema 同步回滚。

## Open Questions

None blocking.
