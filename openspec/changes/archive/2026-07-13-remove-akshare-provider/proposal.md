## Why

`AkShareMarketDataProvider` 是一个名义上的 fallback，实际零价值：它与默认的 `TencentMarketDataProvider` 共用同一个 `akshare` 库和同一套 `requests`/TLS 栈（Tencent 调 `stock_zh_a_hist_tx`，AkShare 调 `fund_etf_hist_em`），因此对触发 2026-07-04 切换的那类本地代理/TLS 指纹拦截**无法提供任何独立冗余**。真正独立的备份是 `JoinQuantMarketDataProvider`（独立的 `jqdatasdk` 依赖、独立 TLS 栈、独立凭据）。此外 AkShare 在生产代码中**没有任何实例化调用**（仅出现在自身测试中），也没有自动 failover 逻辑；它唯一的差异化数据 `volume` 已确认被全部业务逻辑（backtest / momentum / signal / equity curve）忽略。保留它只是维护负担。

## What Changes

- **BREAKING**: 移除 `AkShareMarketDataProvider` 实现（`packages/core/src/vela_core/akshare_market_data_provider.py`）及其从 `vela_core` 的公开导出。
- 数据源收敛为两个真正独立的栈：`TencentMarketDataProvider`（默认，akshare 栈）+ `JoinQuantMarketDataProvider`（独立备份，jqdatasdk 栈）。
- 删除 AkShare 的单元测试模块（`test_akshare_market_data_provider.py`），并将仅依赖 AkShare 构造的测试（`test_market_price_mapping.py`）改用 Tencent 或 JoinQuant provider。
- 更新 `market-data-provider` spec：移除全部 AkShare 相关 requirement（provider、normalization、error propagation、validation、retry、fallback 可注入性），并将保留的 provider-agnostic 行为（ordering、error type location、factor field、retry）措辞与 Tencent/JoinQuant 对齐，不再引用 AkShare。
- **保留** `akshare` 作为运行时依赖——Tencent provider 仍通过它调用 `stock_zh_a_hist_tx`。本变更**不移除 akshare 依赖**。
- **保留** `BaseMarketDataProvider` 共享基类与 `_derive_factor_frame` 等公共逻辑不动。
- 清理残留的 AkShare 数据源标签：将 `config/etf_pool.yaml` 的 `provider` 改为 `tencent`，同步更新所有读取该配置的断言（`apps/api/tests/test_api_config.py`、`packages/core/tests/test_config.py`）；将所有 `DataFetchLog`/`ETFPoolConfig` 内联 fixture 与 fake provider 的 `akshare` 标签改为 `tencent`（`tests/integration_data.py`、`packages/core/tests/test_dashboard_aggregation.py`、`packages/core/tests/test_etf_pool_sync.py`、`packages/core/tests/test_strategy_config.py`、`packages/core/tests/test_market_data_fetcher.py`，后者含引用 fake provider 文案的耦合断言）；将 `apps/web/src/App.test.tsx` 的 mock 错误文案改为 Tencent 相关。

## Capabilities

### New Capabilities

_(无——本变更为移除，不引入新 capability。)_

### Modified Capabilities

- `market-data-provider`: 移除所有 AkShare 专属 requirement（`AkShare ETF daily price provider`、`AkShare daily price normalization`、`AkShare provider error propagation`、`AkShare fetched daily price validation`、`AkShare transient source retry`）；修改 `Default market data provider is Tencent` 中的 `AkShare provider remains injectable` 场景，将"可注入 fallback"的示例从 AkShare 改为 JoinQuant；确认 provider-agnostic 的 ordering / error-type-location / factor-field requirement 不再以 AkShare 为例证。

## Impact

**删除文件**：
- `packages/core/src/vela_core/akshare_market_data_provider.py`
- `packages/core/tests/test_akshare_market_data_provider.py`

**修改文件**：
- `packages/core/src/vela_core/__init__.py`（移除 `AkShareMarketDataProvider` 导入与 `__all__` 条目）
- `packages/core/tests/test_market_price_mapping.py`（改用 Tencent/JoinQuant 构造 provider）
- `openspec/specs/market-data-provider/spec.md`（删除 AkShare requirement，调整 fallback 场景）
- `config/etf_pool.yaml`（`provider` 从 `akshare` 改为 `tencent`，反映默认数据源）
- `apps/api/tests/test_api_config.py`（同步 `provider` 断言）
- `packages/core/tests/test_config.py`（同步读取真实 `etf_pool.yaml` 的 `provider` 断言两处，并清理 5 处内联 yaml fixture 的 `provider` 标签为 `tencent`，与 `test_strategy_config.py` 一致--Review F1 发现的同类遗漏）
- `tests/integration_data.py`（`DataFetchLog.source` fixture 从 `akshare` 改为 `tencent`）
- `packages/core/tests/test_dashboard_aggregation.py`（`DataFetchLog.source` 内联 fixture 从 `akshare` 改为 `tencent`）
- `packages/core/tests/test_etf_pool_sync.py`（内联 `ETFPoolConfig.provider` 从 `akshare` 改为 `tencent`）
- `packages/core/tests/test_strategy_config.py`（内联 yaml fixture `provider` 从 `akshare` 改为 `tencent`）
- `packages/core/tests/test_market_data_fetcher.py`（fake provider `name` 与错误文案 `akshare` → `tencent`，同步更新引用该文案的两条断言）
- `apps/web/src/App.test.tsx`（mock 错误文案 AkShare → Tencent）

**保留不动**：
- `packages/core/src/vela_core/tencent_market_data_provider.py`（默认 provider，继续依赖 akshare）
- `packages/core/src/vela_core/joinquant_market_data_provider.py`（独立备份）
- `packages/core/src/vela_core/base_market_data_provider.py`（共享基类）
- `packages/core/src/vela_core/market_data_provider.py`（`DailyPrice` 契约、`MarketDataProviderError`）
- `pyproject.toml` 中的 `akshare` 依赖（Tencent 仍需）

**依赖**：不新增、不移除任何依赖。`akshare` 因 Tencent 保留；`jqdatasdk` 作为可选 extra 保持不变。

**公开 API 破坏**：`vela_core.AkShareMarketDataProvider` 不再导出。已确认无生产调用点（`apps/api`、`apps/cli` 默认均构造 Tencent），破坏面仅限直接引用该类的外部代码/测试。

**风险**：低。业务逻辑不消费 volume；无自动 failover 依赖 AkShare；spec 中 provider-agnostic requirement 已独立于 AkShare 存在（7-08 去重时已上提到基类契约）。新增的语义标签清理可减少默认数据源为 Tencent 后仍出现 "akshare" 字符串造成的混淆。
