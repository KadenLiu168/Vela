## 1. 移除实现与导出

- [x] 1.1 删除 `packages/core/src/vela_core/akshare_market_data_provider.py`
- [x] 1.2 在 `packages/core/src/vela_core/__init__.py` 中移除 `from vela_core.akshare_market_data_provider import AkShareMarketDataProvider` 及 `__all__` 中的 `"AkShareMarketDataProvider"` 条目
- [x] 1.3 全仓 grep `AkShareMarketDataProvider` 确认除待迁移测试外无其他引用（尤其 `apps/api`、`apps/cli` 生产代码）

## 2. 清理测试

- [x] 2.1 删除 `packages/core/tests/test_akshare_market_data_provider.py`
- [x] 2.2 删除 `packages/core/tests/test_market_price_mapping.py` 中的 `test_akshare_daily_rows_normalize_then_map_to_market_price`（#3）及其 `FakeAkShareModule` 辅助类；保留 #1/#2（直接构造 `DailyPrice`，与 provider 无关）
- [x] 2.3 移除 `test_market_price_mapping.py` 顶部对 `AkShareMarketDataProvider` 与 `pandas` 的 import（删除 #3 后不再需要）

## 3. 更新 spec

- [x] 3.1 从 `openspec/specs/market-data-provider/spec.md` 移除 5 个 AkShare requirement（`AkShare ETF daily price provider`、`AkShare daily price normalization`、`AkShare provider error propagation`、`AkShare fetched daily price validation`、`AkShare transient source retry`）
- [x] 3.2 修改 `Default market data provider is Tencent` requirement：将 `AkShare provider remains injectable` 场景替换为 `JoinQuant provider remains injectable`
- [x] 3.3 清理保留 requirement 内的 AkShare 悬挂引用：`Provider error type location` 场景 `(AkShare or Tencent)` -> `(Tencent or JoinQuant)`；`JoinQuant ETF daily price provider` 描述 `the akshare package used by the AkShare and Tencent providers` -> `used by the Tencent provider`
- [x] 3.4 确认 `Provider implementation independence` 的 `Contract does not expose AkShare types` 场景**保留不动**（此处 AkShare 指 akshare 库，仍是依赖）；通读 ordering / factor field 等 provider-agnostic requirement 无遗留错误引用

## 4. 清理 AkShare 数据源标签

**A. 读取真实 `etf_pool.yaml` 的断言（改 yaml 后必断，必须同步）**

- [x] 4.1 将 `config/etf_pool.yaml` 的 `provider` 从 `akshare` 改为 `tencent`
- [x] 4.2 同步更新 `apps/api/tests/test_api_config.py` 中 `body["etf_pool"]["provider"]` 断言为 `"tencent"`
- [x] 4.3 同步更新 `packages/core/tests/test_config.py` 两处断言：`config.provider == "akshare"`（line 23）与 `config.etf_pool.provider == "akshare"`（line 147）改为 `"tencent"`

**B. 内联 fixture / fake provider 标签（不读真实配置，但与 cleanup 一致）**

- [x] 4.4 将 `tests/integration_data.py` 的 `data_fetch_log` fixture 中 `source="akshare"` 改为 `source="tencent"`
- [x] 4.5 将 `packages/core/tests/test_dashboard_aggregation.py` 的 `DataFetchLog` 内联 fixture 中 `source="akshare"` 改为 `source="tencent"`
- [x] 4.6 将 `packages/core/tests/test_etf_pool_sync.py` 的内联 `ETFPoolConfig(provider="akshare")` 改为 `provider="tencent"`
- [x] 4.7 将 `packages/core/tests/test_strategy_config.py` 的内联 yaml fixture `"provider": "akshare"` 改为 `"tencent"`
- [x] 4.8 将 `packages/core/tests/test_market_data_fetcher.py` 的 fake provider `ExhaustedRetryMarketDataProvider`：`name = "akshare"` -> `"tencent"`，错误文案 `f"akshare market data provider error..."` -> `f"tencent market data provider error..."`，并同步更新引用该文案的两条断言（line 159、161：`"SPY: akshare market data provider error symbol=SPY"` -> `"SPY: tencent market data provider error symbol=SPY"`）。注意保留 line 580 的 `TradingCalendar(source="akshare")` 不动
- [x] 4.10 将 `packages/core/tests/test_config.py` 的 5 处内联 yaml fixture `provider: akshare`（line 37/65/91/197/287）改为 `tencent`，与 4.7 的 `test_strategy_config.py` 内联 fixture 清理保持一致（Review F1 发现的同类遗漏，避免同模式区别对待）

**C. UI mock**

- [x] 4.9 将 `apps/web/src/App.test.tsx` 中 mock 错误文案 "AkShare provider timed out while fetching 510300" 改为 "Tencent provider timed out while fetching 510300"

## 5. 验证

- [x] 5.1 运行 `ruff check` + `ruff format --check`（`ruff check` 全绿；`ruff format --check` 存在 14 个**预先存在**的格式问题，经 `git stash` 比对确认全部与本次 change 无关，本次未引入新格式问题——按"修改范围限于当前 change"原则不修复无关文件）
- [x] 5.2 运行 `mypy`（本次修改/删除的文件**无 mypy 报错**；仓库预先存在 52 个 mypy 错误于 6 个无关文件，与本次 change 无关）
- [x] 5.3 运行完整 `pytest`（491 passed；1 个**预先存在**失败 `tests/test_joinquant_integration.py::test_joinquant_fetches_real_etf_daily_prices`，因 JoinQuant 账号权限限制数据范围至 2026-04-11，与本次 change 无关且不在修改范围）
- [x] 5.4 运行 `openspec validate remove-akshare-provider --strict` 通过（`openspec validate --all --strict`：38 passed, 0 failed）
