## Why

`vela fetch-market-data` 在用户机器上一直报 `('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))`——根因是两层 TLS 指纹拦截：(1) 本地 SpeedCat 代理检测到 Python `requests` 的非浏览器 TLS ClientHello 立即 RST；(2) 即使绕过 SpeedCat，东财 push2his 接口 WAF 也对非浏览器 TLS 指纹直接 RST。已经确认：**真实 Chrome 走代理能正常返回 200**（kline 接口数据本身是健康的），但 akshare 的 requests 走不到。所以必须**把数据源从 AkShare `fund_etf_hist_em` 切到腾讯 `stock_zh_a_hist_tx`**，绕过这两层指纹拦截，恢复数据获取。

## What Changes

- **新增 `TencentMarketDataProvider`**：实现 `MarketDataProvider` Protocol，调用 akshare `stock_zh_a_hist_tx`，按 Vela 的 `DailyPrice` 契约返回
- **修改 CLI 默认 provider**：`apps/cli/src/vela_cli/main.py` 的 `fetch_full_market_data` / `fetch_incremental_market_data` 默认使用 Tencent，AkShare 保留为可注入的 fallback
- **修改 API 默认 provider**：`apps/api/src/vela_api/main.py` 同上
- **修改 `market-data-provider` spec**：把 `AkShare ETF daily price provider` 相关 requirement 拆分为 `Tencent ETF daily price provider`（primary）+ `AkShare ETF daily price provider`（fallback）
- **新增单元测试**：`packages/core/tests/test_tencent_market_data_provider.py`，覆盖 normalization、date bounds、错误传播
- **更新 integration test fixture**：`tests/integration_data.py` 增加腾讯接口的 sample 数据

不破坏现有数据格式（Vela `DailyPrice` / `MarketPrice.volume` 字段兼容腾讯返回的字段集，business logic 不使用 `volume`）。

## Capabilities

### New Capabilities
无（不引入新 capability）

### Modified Capabilities
- `market-data-provider`: AkShare provider 不再是唯一实现，改为 "Tencent 是默认 provider，AkShare 作为可注入的 fallback"。Tencent provider 走 `stock_zh_a_hist_tx`，symbol 需加 `sh`/`sz` 市场前缀，按年循环请求；返回字段 `date/open/close/high/low/amount` 映射到 Vela 的 `DailyPrice` 字段（`amount` 丢弃，`volume` 传 `None`）

## Impact

**新增文件**：
- `packages/core/src/vela_core/tencent_market_data_provider.py`
- `packages/core/tests/test_tencent_market_data_provider.py`

**修改文件**：
- `apps/cli/src/vela_cli/main.py`（默认 provider 改 Tencent）
- `apps/api/src/vela_api/main.py`（默认 provider 改 Tencent）
- `tests/integration_data.py`（新增腾讯接口 sample）
- `openspec/specs/market-data-provider/spec.md`（spec delta）

**保留不动**：
- `packages/core/src/vela_core/akshare_market_data_provider.py`（作为 fallback 保留）
- `packages/core/src/vela_core/market_data_provider.py`（`DailyPrice` 契约不变）
- `packages/core/src/vela_core/market_data_fetcher.py`（fetch 流程不变）

**依赖**：akshare 已经包含 `stock_zh_a_hist_tx`，**不增加新依赖**。

**风险**：
- 腾讯接口按年循环请求，全量拉 26 年历史时需要 26 次请求（akshare 内置逻辑）
- 腾讯接口**没有 `volume` 字段**——已确认 Vela 业务逻辑（`backtest_runner` / `momentum_scoring` / `strategy_signal_generation` / `strategy_equity_curve`）完全不使用 `volume`，只用作 `MarketPrice.volume` 字段存储（nullable），无业务影响
