## Context

`vela fetch-market-data` 在用户机器上持续报 `RemoteDisconnected`。诊断已锁定根因为两层 TLS 指纹拦截：

1. **本地 SpeedCat 代理**（`lsof` 确认 `SpeedCatC 44135 ... TCP localhost:7892 (LISTEN)`）检测 Python `requests` 的非浏览器 TLS ClientHello 立即 RST
2. **东财 push2his WAF** 即使绕过 SpeedCat 也对非浏览器 TLS 指纹直接 RST

**已确认**：Chrome 通过 SpeedCat 走 `push2his.eastmoney.com` 能拿到 `{"rc":0,"data":{...}}`（kline 数据本身健康），问题只出在客户端。

akshare 已提供 `stock_zh_a_hist_tx` 走 `proxy.finance.qq.com`，返回 `date/open/close/high/low/amount` 字段。Vela 业务逻辑（`backtest_runner` / `momentum_scoring` / `strategy_signal_generation` / `strategy_equity_curve`）完全不读 `volume` 字段，腾讯接口无 `volume` 字段无业务影响。

## Goals / Non-Goals

**Goals:**
- 恢复 `vela fetch-market-data` 在用户机器上能成功跑通
- 不破坏现有 `DailyPrice` / `MarketPrice` 数据契约
- AkShare provider 保留作为可注入的 fallback（不删代码）
- 不引入新依赖（akshare 已包含腾讯接口）
- 单元测试覆盖 Tencent provider 的 normalization / 错误传播路径

**Non-Goals:**
- 不实现 multi-source fallback / retry 链（保持简单）
- 不实现 real-time streaming 或 websocket
- 不改 `DailyPrice` 数据类的字段（保持向后兼容）
- 不优化拉取性能（按年循环由 akshare 内置）
- 不重写 akshare 内部实现

## Decisions

### D1. 数据源选择：腾讯 `stock_zh_a_hist_tx`

**选择**：akshare `stock_zh_a_hist_tx`（`https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get`）

**理由**：
- akshare 已包含，无需新依赖
- 走 `proxy.finance.qq.com` 子域名，腾讯 WAF 较松
- 返回字段是英文（`date/open/close/high/low/amount`），易映射
- 限流比东财宽容（akshare 大量用户使用）

**考虑过的替代**：
- **新浪 `fund_etf_hist_sina`**：需 `py_mini_racer`（额外依赖）+ JS 解密 + symbol 加 `sh`/`sz` 前缀 + 不支持服务端日期过滤（本地 filter）—— 工作量更大
- **维持东财 + `curl_cffi` 模拟 Chrome TLS**：加新依赖 + 仍可能被腾讯/新浪 WAF 拦 —— 不确定性高
- **维持东财 + SpeedCat 规则放行**：只过 SpeedCat 一关，东财 WAF 仍 ban —— 治标不治本

### D2. symbol 映射：硬编码 `sh`/`sz` 前缀

**选择**：根据 symbol 数值判断市场——`15` 开头 → `sz`，其他 → `sh`

**理由**：
- ETFConfig 只有 `symbol` 字段（6 位数字），没有 `exchange`
- 简单规则：`15*`（深市 159 段）vs `51*/56*/58*`（沪市）
- 与 akshare `stock_zh_a_hist_tx` 的 `param=sh510300`/`param=sz159915` 格式匹配

**Trade-off**：未来加债券 / 跨境 ETF 可能需要扩展规则——但 Phase 1 范围足够。

### D3. 字段映射：丢弃 `amount`、`volume` 传 None

**选择**：`amount` 不映射到 Vela 任何字段（Vela 无此字段），`volume` 显式传 `None`

**理由**：
- `DailyPrice.volume: int | None = None`（可选）
- `MarketPrice.volume: Mapped[int | None]`（nullable）
- 已确认 Vela 业务逻辑（grep 整个 `packages/core/src/vela_core/`）完全不使用 `.volume`
- `amount` 字段 Vela 无对应——直接丢弃

### D4. 默认 provider 切换：CLI + API 同步

**选择**：`fetch_full_market_data` / `fetch_incremental_market_data` 默认用 `TencentMarketDataProvider()`

**理由**：
- 一处失败影响所有入口——CLI 和 API 必须同步切换
- `AkShareMarketDataProvider` 仍可被注入（fallback），但不是默认

**Trade-off**：不提供"运行时切换 provider"的机制——保持简单，必要时再扩展。

### D5. AkShare 保留为 fallback 不删除

**选择**：`akshare_market_data_provider.py` 不删，仅从默认路径移除

**理由**：
- 未来腾讯出问题可临时回退
- spec 仍要求 AkShare 实现存在（fallback 语义）
- 测试代码（`test_akshare_market_data_provider.py`）继续保护 regression

### D6. 按年循环请求：交给 akshare

**选择**：不自己循环，直接调 `stock_zh_a_hist_tx(symbol, start_date, end_date)`

**理由**：
- akshare 内部已经按年循环（看 `stock_hist_tx.py:60-83`）
- 调一次接口拿 26 年数据 → akshare 内部拆 26 次 HTTP 请求
- vela 全量拉 26 年历史时性能由 akshare 负责
- vela 增量模式（只拉最新几天）→ akshare 循环 1-2 次

## Risks / Trade-offs

- **腾讯接口限流** → 腾讯 push 接口可能突然限流，但 akshare 大量用户使用、限流比东财宽松，风险中等
- **字段不完全对齐** → `volume` 字段缺失，Vela 业务无影响；`amount` 丢弃，Vela 无对应字段；可接受
- **按年循环慢** → 全量拉 26 年历史要 26 次请求，akshare 内部串行；vela 通常用 `--incremental` 只拉新数据，影响小
- **数据质量差异** → 腾讯 vs 东财的复权方式可能不同；Vela 不用复权（adjust=""），字段都是不复权价
- **Symbol 规则硬编码** → 未来加新市场 ETF 需要扩展 `to_tx_symbol`；Phase 1 范围可接受
- **回退路径不自动化** → 如果腾讯挂了，用户需手动改 CLI / API 代码切回 AkShare；不是 auto-fallback

## Migration Plan

**部署**：直接 `git commit` + 推到 main，本地 `uv sync` 即生效。无需 migration script，无需数据库 schema 变更。

**回滚**：`git revert` 即可。`AkShareMarketDataProvider` 代码保留，revert 后默认 provider 立即回到 AkShare。

**验证步骤**（在 `apply` 阶段）：
1. 跑 `pytest packages/core/tests/test_tencent_market_data_provider.py` 验证 normalization 正确
2. 跑 `pytest` 全套测试套件
3. 跑 `uv run vela fetch-market-data --incremental` 在用户机器上实际拉一次数据，确认不报 `RemoteDisconnected`
4. SQLite 查 `market_price` 表确认 rows 写入正确

## Open Questions

无——所有关键技术决策已锁定。实施时如遇 akshare 接口签名变化或腾讯 WAF 升级，再回到本 design 重新评估。
