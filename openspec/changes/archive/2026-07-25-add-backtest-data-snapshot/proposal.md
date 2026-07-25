## Why

回测不可审计的一个根因：`backtest_run` 表不记录任何**数据版本信息**，两次运行之间若数据漂移（增量同步、复权重算、缺口补录、HFQ 整条平移）无法被证明。这导致"Run1 vs Run2 差 7pt"无法先排除数据差异。需在每次回测时记录其市场数据输入的**指纹**，使数据漂移可被可靠识别。

## What Changes

- `BacktestRun` 模型新增 `data_snapshot_json` 字段（JSON），持久化本次回测市场数据输入的摘要：`min_trade_date`、`max_trade_date`、`trading_day_count`、`active_etf_count`、`per_etf_row_counts`、`data_checksum`。
- `run_backtest` 加载覆盖 lookback buffer 至请求 `end_date` 的 active-ETF 价格面板；它仍按每个调仓日截断该面板生成信号，并在加载后计算摘要，通过 `BacktestResultRunInput` → `persist_backtest_result` 路径落库到 `BacktestRun` 行（同一 caller-managed 事务，不新增 commit）。
- `data_checksum`：对覆盖范围内所有 `(etf_id, trade_date, close_price, factor_hfq)` 行，按确定性、无歧义的编码计算 **sha256 哈希**，用于检测数据漂移（仅检测，不存全量数据）。
- 新增 Alembic 迁移添加 `data_snapshot_json` 列（SQLite 兼容）。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `backtest-run-model`: `BacktestRun` 须在创建时持久化其市场数据输入的快照摘要（含 `data_checksum`），以支持数据漂移检测与回测可审计。

## Impact

- Affected code:
  - `packages/core/src/vela_core/models/backtest.py`（新增 `data_snapshot_json` 字段）。
  - `packages/core/src/vela_core/backtest_result_persistence.py`（`BacktestResultRunInput` 新增 `data_snapshot_json`，`persist_backtest_result` 写入该字段）。
  - `packages/core/src/vela_core/backtest_runner.py`（加载覆盖完整回测区间的 price_panel 后计算摘要，并通过 `BacktestResultRunInput` 传入；历史信号仍只见各自调仓日及之前的数据）。
  - 新增 Alembic 迁移（添加 `data_snapshot_json` 列）。
- Affected tests:
  - 迁移测试（列存在、JSON 可写、空值允许、downgrade 移除）。
  - checksum 确定性测试（同数据同 hash；任意一行 `close_price`/`factor_hfq` 改动后 hash 必变；行序无关；字段边界无碰撞）。
  - `run_backtest` 落库测试（摘要字段被正确写入且可解析，覆盖到 `end_date`；partial 状态 run 也写入快照）。
  - 模型测试：`test_backtest_run_optional_completion_fields_are_nullable` 新增 `data_snapshot_json`。
- 无 API / CLI / 前端变更：快照为内部可审计字段，本期不暴露 UI（可在后续变更于回测详情页展示）。
- 依赖 `market-price-panel-loading`（复用 `load_price_panel` 输出）。
- 此 Change 仅把数据差异变为可观测证据；它不记录代码版本，也不替代 `scope-backtest-signals-by-run` 对本次 run 信号隔离的修复，因而不单独承诺“相同 checksum 必得相同结果”。
