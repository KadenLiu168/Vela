## Context

Vela 目前有三个 `MarketDataProvider` 实现，均继承自 `BaseMarketDataProvider`：

- `TencentMarketDataProvider`（默认）→ `akshare.stock_zh_a_hist_tx`
- `AkShareMarketDataProvider`（名义 fallback）→ `akshare.fund_etf_hist_em`
- `JoinQuantMarketDataProvider`（独立备份）→ `jqdatasdk`

代码核实的现状：

1. **Tencent 与 AkShare 不是独立数据源**——两者共用 `akshare` 库、共用 `requests`/TLS 栈，仅调用 akshare 封装的不同上游接口。2026-07-04 的故障根因是本地代理 + 东财 WAF 的双层 TLS 指纹拦截；AkShare 走的正是被拦截的东财 `push2his` 接口，对该故障零帮助。
2. **AkShare 无生产调用**——`apps/api/main.py:60` 与 `apps/cli/main.py:364,371` 默认均构造 `TencentMarketDataProvider()`；全仓 `AkShareMarketDataProvider` 的实例化仅出现在 `test_akshare_market_data_provider.py` 与 `test_market_price_mapping.py`。系统没有任何自动 failover 逻辑，Tencent 失败不会切 AkShare。
3. **AkShare 的差异化数据 volume 无人消费**——grep 确认 `backtest_runner` / `momentum_scoring` / `strategy_signal_generation` / `strategy_equity_curve` 均不读取 `volume`，仅作为 nullable 字段存入 `MarketPrice`。
4. **7-08 去重已把公共契约上提到基类**——ordering、error-type-location、factor-field、validation、retry 等 provider-agnostic requirement 已独立于 AkShare 存在。

结论：AkShare 是纯维护负担。真正独立的备份是 JoinQuant（独立依赖 + 独立 TLS 栈 + 独立凭据）。

## Goals / Non-Goals

**Goals:**
- 移除 `AkShareMarketDataProvider` 实现及其公开导出，数据源收敛为 Tencent(default) + JoinQuant(独立备份)。
- 清理 AkShare 相关测试，并把仅依赖 AkShare 构造的测试迁移到保留的 provider。
- 从 `market-data-provider` spec 中移除全部 AkShare requirement，并把可注入 fallback 的示例改为 JoinQuant。
- 保持所有保留行为不变：Tencent 默认、JoinQuant 可注入、ordering/factor/retry/validation 契约不变。
- 清理残留在配置、测试 fixture、前端 mock 中的 AkShare 数据源标签，使其与默认数据源 Tencent 一致。

**Non-Goals:**
- 移除 `akshare` 运行时依赖（Tencent 仍需）。
- 引入自动 failover 编排（Tencent→JoinQuant 自动切换）——这是独立的后续变更，本次不做。
- 改动 `BaseMarketDataProvider`、`_derive_factor_frame`、`DailyPrice` 契约或 `MarketDataProviderError`。
- 改动 volume 字段本身（`MarketPrice.volume` 保持 nullable，JoinQuant 仍可写入）。

## Decisions

### Decision 1: 硬删除 AkShare provider，而非弃用标记

直接删除 `akshare_market_data_provider.py` 及其从 `vela_core.__init__` 的导出，而不是保留并打 `DeprecationWarning`。

**Rationale**: 这是个人项目，无外部消费者需要迁移窗口；保留弃用桩只会延续维护负担。破坏面已核实仅限该类的直接引用（生产代码零处）。

**Alternative considered**: 保留类但标记 deprecated。拒绝——违背"简洁优先"，且 AkShare 连当前的 fallback 角色都不成立。

### Decision 2: 保留 akshare 依赖

`pyproject.toml` 的 `akshare` 依赖不动。

**Rationale**: akshare 库有两处生产依赖，均与 AkShare provider 无关：(1) Tencent provider 通过 `akshare.stock_zh_a_hist_tx` 工作；(2) 交易日历同步 `trading_calendar_sync.py` 直接调用 `akshare.tool_trade_date_hist_sina`（见 `trading-calendar` spec）。删 AkShare provider 与删 akshare 依赖是两件事，后者会同时破坏默认数据源与交易日历同步。

### Decision 3: 删除测试 #3，而非迁移

`test_market_price_mapping.py` 的三个测试中，只有 `test_akshare_daily_rows_normalize_then_map_to_market_price`（#3）用 `AkShareMarketDataProvider`；#1/#2 直接构造 `DailyPrice`，与 provider 无关，不受影响。#3 的唯一独有覆盖是"带 volume 的 source 行 → normalize → factor 派生 → 映射到 `MarketPrice.volume`"这条端到端链。**直接删除 #3**，不做迁移。

**Rationale**: #3 的覆盖已被拆分覆盖——"带 volume 的 source 行 normalize" 由 `test_joinquant_market_data_provider.py`（volume=[900,1000]）覆盖；"`DailyPrice(volume=1000)` → `MarketPrice.volume`" 由本文件 #1 覆盖。#3 仅把两段串联，增量价值极低。删除符合"简洁优先"，覆盖无实质损失。

**Alternatives considered**:
- 用 `JoinQuantMarketDataProvider` fake source 重写 #3（Tencent 无 volume 列，无法保留 volume 断言；JoinQuant 才有）。拒绝——需处理 JoinQuant 的 auth-once 路径与 factor 列，为一条冗余的串联测试增加复杂度，不值当。
- 改用 Tencent fake source 并把断言改成 `volume is None`。拒绝——会静默削弱 volume 覆盖，语义走样。
- 保留 AkShare 仅为这一个测试。拒绝——本末倒置。

### Decision 4: spec delta 用 REMOVED + MODIFIED，并清理保留 requirement 的悬挂引用

5 个 AkShare 专属 requirement 用 `## REMOVED Requirements`（附 Reason + Migration）。`## MODIFIED Requirements` 包含三条整块重写：
1. `Default market data provider is Tencent`：`AkShare provider remains injectable` 场景 → `JoinQuant provider remains injectable`。
2. `Provider error type location`：场景 `Concrete providers do not own the error type` 的 `(AkShare or Tencent)` → `(Tencent or JoinQuant)`。
3. `JoinQuant ETF daily price provider`：requirement 描述 `the akshare package used by the AkShare and Tencent providers` → `used by the Tencent provider`。

**Rationale**: 后两条是保留 requirement 内的 AkShare 悬挂引用——删除 AkShare provider 后这些文本会变成事实错误（引用一个不存在的 provider），而 `openspec validate` 只校验 delta 格式、抓不到跨引用陈旧，必须显式 MODIFY。

**刻意不动**: `Provider implementation independence` 的 `Contract does not expose AkShare types` 场景保留原样——这里 "AkShare" 指 akshare **库**（仍是依赖，Tencent + 交易日历都用），requirement 依然成立；改词属无谓 churn，遵循"精准修改"。

### Decision 5: 清理残留的 AkShare 数据源标签

将所有把 `akshare` 当作市场数据 provider 标签的字符串改为 `tencent`，分两类：

**A. 读取真实 `etf_pool.yaml` 的断言**（改 yaml 后必断，必须同步）：
- `config/etf_pool.yaml` 的 `provider` 从 `akshare` 改为 `tencent`；
- `apps/api/tests/test_api_config.py` 与 `packages/core/tests/test_config.py`（两处）的 `provider` 断言同步改为 `tencent`。

**B. 内联 fixture / fake provider 的标签**（不读真实配置、不会断，但与 cleanup 意图一致）：
- `tests/integration_data.py` 与 `packages/core/tests/test_dashboard_aggregation.py` 的 `DataFetchLog(source="akshare", ...)` 改为 `source="tencent"`；
- `packages/core/tests/test_etf_pool_sync.py` 的内联 `ETFPoolConfig(provider="akshare")` 与 `packages/core/tests/test_strategy_config.py` 的内联 yaml fixture `provider: "akshare"` 改为 `tencent`；
- `packages/core/tests/test_market_data_fetcher.py` 的 fake provider `ExhaustedRetryMarketDataProvider`：`name = "akshare"` → `"tencent"`，错误文案 `f"akshare market data provider error..."` → `f"tencent market data provider error..."`，并同步更新引用该文案的两条断言（line 159、161，错误串前缀 `SPY: akshare` → `SPY: tencent`）。

**C. UI mock**：`apps/web/src/App.test.tsx` 的 mock 错误文案 "AkShare provider timed out while fetching 510300" 改为 "Tencent provider timed out while fetching 510300"。

**Rationale**: 默认数据源已切换为 Tencent，继续使用 `akshare` 作为 provider/日志源/UI 文案会误导用户认为 AkShare 仍是生产数据源。A 类是硬依赖（改 yaml 必断）；B 类虽不触发 `AkShareMarketDataProvider` 代码路径、不会断，但与 cleanup 意图一致，一并清理避免同模式区别对待。校验中发现 `packages/core/tests/test_config.py` 原本被遗漏——它与 `apps/api/tests/test_api_config.py` 同样读取真实 `etf_pool.yaml` 并断言 `provider == "akshare"`，不补会导致 pytest 变红。Review（Loop 1 F1）进一步发现 `test_config.py` 的 5 处内联 yaml fixture `provider: akshare`（line 37/65/91/197/287）同样属于 B 类却未被列出，与 `test_strategy_config.py` 同模式区别对待，已补充清理（task 4.10）。

**刻意不动**: `apps/cli/src/vela_cli/main.py` 中 `sync-trading-calendar` 的 help 文案 "from akshare" 保持不变，因为交易日历同步确实直接调用 `akshare.tool_trade_date_hist_sina`；`data_quality.py` 中 "akshare/tencent" 注释也保持不变，因为该注释指的是 `akshare` 库；`packages/core/tests/test_market_data_provider.py:83` 的 `assert "akshare" not in source` 契约独立性断言保留——它断言 provider 契约模块不引用 akshare，移除 AkShare provider 后该断言依然成立；各测试中 `TradingCalendar(source="akshare")` 保留——交易日历确实来自 akshare 库。

## Risks / Trade-offs

- **失去 volume 数据源** → 缓解：业务逻辑零消费（已 grep 确认）；JoinQuant 的 `_column_map` 含 volume，未来若需要 volume，JoinQuant 已可提供。
- **失去"东财接口"这一路数据** → 缓解：该路正是 7-04 被 WAF 拦截的路径，价值本就存疑；Tencent + JoinQuant 覆盖两个独立栈。
- **外部代码直接引用 `vela_core.AkShareMarketDataProvider`** → 缓解：破坏在 proposal 中显式标注 BREAKING；已确认仓内生产代码零引用。
- **测试迁移引入回归** → 缓解：迁移后运行完整 pytest；`test_market_price_mapping` 的断言语义保持不变（只换 provider 构造方式或直接构造 DailyPrice）。

## Migration Plan

1. 删除 `akshare_market_data_provider.py` 与 `test_akshare_market_data_provider.py`。
2. 从 `vela_core/__init__.py` 移除 `AkShareMarketDataProvider` 的 import 与 `__all__` 条目。
3. 迁移 `test_market_price_mapping.py`（按 Decision 3）。
4. 运行 `ruff` + `mypy` + `pytest` 全绿。
5. 清理 AkShare 数据源标签（按 Decision 5 A/B/C 三类）：A 类改 `etf_pool.yaml` 并同步 `test_api_config.py`、`test_config.py` 断言；B 类改 `integration_data.py`、`test_dashboard_aggregation.py`、`test_etf_pool_sync.py`、`test_strategy_config.py`、`test_market_data_fetcher.py`（含耦合断言）的内联 fixture 标签；C 类改 `App.test.tsx` mock 文案。
6. 归档 spec delta（AkShare requirement 从 `openspec/specs/market-data-provider/spec.md` 移除，fallback 场景更新为 JoinQuant）。

**Rollback**: `git revert` 本变更即可恢复 AkShare provider（akshare 依赖始终在位，无需额外恢复依赖）。

## Open Questions

- 无（`test_market_price_mapping.py` 的处理已在 Decision 3 定为删除 #3）。

## Out of Scope（范围外观察）

- `packages/core/tests/test_market_data_provider.py:83` 的 `assert "akshare" not in source` 契约独立性断言保留不动——它断言 provider 契约模块不引用 akshare，移除 AkShare provider 后依然成立。
- 各测试中 `TradingCalendar(source="akshare")` 与 `trading_calendar_sync.py` 的 `source="akshare"` 保留不动——交易日历确实来自 akshare 库，与市场数据 provider 无关。
- `apps/cli` `sync-trading-calendar` help 文案 "from akshare" 与 `data_quality.py` 注释保留不动——指 akshare 库。
