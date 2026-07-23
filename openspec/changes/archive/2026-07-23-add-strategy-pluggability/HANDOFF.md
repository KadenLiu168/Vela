# Handoff: add-strategy-pluggability

## 当前真实状态校正（2026-07-23，Final Verify 完成）

本节以当前工作树为准，并覆盖下方所有历史记录中的旧进度、旧失败和旧文件清单。

- Git：`main`，`3d7f036ad0fd3a1d3ba4ceeb4107667733475acd`；本 Change 尚未提交。保留开始前已有的无关中文 `.txt`，仅为确认范围读取，未修改。
- Tasks：`tasks.md` 当前为 **43/43**；1.1–8.7 均已勾选。
- 实施：API 已输出 common 字段加 `type`、嵌套 `parameters`；Web 使用 `type` discriminated union，Dashboard 仅在 dual-momentum 读取专属参数，并有 equal-weight 无缺失字段渲染回归。`App.test.tsx` 修复了 ETF 日期补入 fixture 后的非唯一文本定位。
- 本阶段验证：Change 相关 Python 核心/API 集为 **168 passed**；`npm --prefix apps/web run test` 为 **165 passed, 7 skipped**；web lint、CSS lint、root CSS、typecheck、build 与 bundle check 均通过；Ruff、format、mypy、Python build、pre-commit 和 `git diff --check` 均通过。
- Handoff 差异：旧章节中的“25/43”“6.x 未开始”“API/Web fixture 未迁移”“Web 163 passed, 1 failed”均已过时，不得作为状态或风险依据。
- 验证：修复后全量 Python 为 **602 passed, 1 skipped**（可选 JoinQuant SDK 未安装）；Ruff、format、mypy（56 source files）、Python sdist/wheel build 与 pre-commit 通过；Web lint、CSS lint、root CSS、typecheck、test（**165 passed, 7 skipped**）、build、bundle check 通过；`openspec validate add-strategy-pluggability --strict` 与 `openspec doctor --json` 通过。本机 OpenSpec CLI 没有独立 `verify` 子命令（`unknown command 'verify'`），故以上 strict/doctor/项目门禁构成 Verify 证据。
- 结构与 schema：三处共享编排模块没有 concrete-strategy import 或 strategy-type conditional；仅 backtest audit `parameters_json` 写入 `type`。没有 Alembic migration 或持久化 schema 修改。已知的同 identity 并发 backtest read-isolation 风险仍为明确 out of scope。
- Review：本轮完整独立审查修复三项真实问题：(1) historical shared wrapper 曾向任意策略暴露未来价格（High），现由共享边界逐日期截断并有 RED→GREEN 协议探针测试；(2) unknown registry lookup 曾抛内建异常而非 project-owned error（Medium），现使用 `StrategyRegistryError`；(3) Web client contract test 仍使用旧扁平 shape 且 `trend_filter` 类型过宽（Medium），现使用受 `DashboardResponse` 约束的真实 nested fixture 与严格字段类型。修复后复审未发现未解决 Blocker/High/必要 Medium。
- 当前风险：同 identity 并发 backtest read-isolation 为设计明确 out of scope；JoinQuant integration 因可选 SDK 未安装而跳过。无未处理的本 Change 高优先级问题。

**Final Verify：READY。**

## 1. Change 信息

- **Change 名称：** `add-strategy-pluggability`
- **Change 目录：** `openspec/changes/add-strategy-pluggability`
- **当前分支：** `main`
- **当前提交 SHA：** `3d7f036ad0fd3a1d3ba4ceeb4107667733475acd`
- **Handoff 生成时间：** 2026-07-23（Asia/Shanghai）
- **当前执行阶段：** Apply（正在迁移既有测试与调用方；尚未进入完整 Validate/Review/Fix 闭环）
- **OpenSpec 状态：** `spec-driven`，`25/43` tasks 勾选完成；planning artifacts 均完整。

## 2. Change 目标与范围

目标是把当前硬编码的 dual-momentum 信号/回测路径改为由已验证配置选择的、参数绑定的 `Strategy` 协议和闭合注册表，并以 `equal_weight` 作为第二个策略实现。配置变为以 `type` 判别的顶层 Pydantic union，策略参数置于 `parameters`，API/Web 采用相同的 type-aware 形状。共享生成、持久化、持仓、权益曲线、指标和报告路径必须不感知具体策略；dual momentum 的计算、无未来数据截断、预期失败结果、回调与事务语义必须保持。

非目标：动态插件发现、动态 import、第三方插件、多策略单次回测、`strategy_type` 数据库字段/迁移、组合优化、实盘执行，以及修复既有同 identity 并发回测读隔离问题。

验收重点：两个配置变体严格校验；registry 只支持已注册类型；`StrategyGenerationError` 转为既有 failed result 而非吞掉程序错误；equal weight 以 ETF id 稳定排序并给出精确 `Decimal("1") / Decimal(N)`；回测使用 strategy 声明的非负 lookback；API/Web 支持两种形状；身份 `(strategy_id, version)` 跨类型隔离；无 schema migration；所有 Python/Web 门禁及 OpenSpec 严格校验通过，并至少完成一轮独立 Review/Fix/Validate。

## 3. OpenSpec Tasks 状态

`tasks.md` 已勾选 1.1–1.7。以下状态以实际工作树与本轮验证为准；`[~]` 不是完成，不能据此勾选 task。

### 1. Configuration union and migration contract

- [x] 1.1–1.7：补齐 missing/unknown type 断言，移除 local shim，把所有 in-repo direct validation callers 与配置 fixtures 迁移为 nested shape；`rg` 未发现 `StrategyConfig.model_validate` 或公开 `defense_lookup=` caller。目标 Python 集合 `115 passed`；mypy `56 source files` 通过。

### 2. Protocol, position type, registry, and error boundary

- [x] 2.1–2.6：新增 `test_strategy_registry.py` 覆盖两个 factory、参数绑定、unknown registry、预期/意外错误与 callback；现有 generation regressions 覆盖 empty-active、empty-result、historical order/no-future-data/callback。registry 改为 module-constant closed plain dict，移除无必要 `MappingProxyType`/ignore。

### 3. Dual-momentum migration with behavioral parity

- [x] 3.1–3.5：现有 golden regression 覆盖 trend、history、ranking/tie、Top-N、多防御资产、missing-defense、empty/no-future-data/result/callback；`DualMomentumStrategy` 仅绑定 `DualMomentumParams` 并以 active ETFs 解析防御资产。全量 Python suite `592 passed, 1 skipped`。

### 4. Strategy-agnostic live and backtest orchestration

- [ ] 4.1 仍缺明确 service registry-dispatch/no-defense-lookup spy test。
- [x] 4.2 service 仅把 config、active ETFs、price panel 交给 generic wrapper；既有 source/commit regression 通过。
- [ ] 4.3 已新增 negative-lookback-before-persistence regression，但仍缺 resolved/zero lookback 与无 type-branch 的明确断言。
- [x] 4.4 runner 使用 bound strategy lookback、保留 `lookback * 2 + 10`，并调用 generic historical generation。
- [x] 4.5 audit `parameters_json` 含 type，signal linkage/holdings/equity/metrics regressions 均通过，无 schema 修改。
- [x] 4.6 已移除 test double 及仓库 caller 的 `defense_lookup=`；搜索为零结果。

### 5. Equal-weight validation strategy

- [x] 5.1–5.2：registry tests 覆盖按 ETF id 排序、一 ETF 一 position、精确 Decimal 均分、null rank/score、空 price panel 与 0 lookback。
- [ ] 5.3 generic live/historical wrapper integration 已有，但仍缺 service-level live integration 断言。

### 6. Persisted identity isolation and config-only switching

- [ ] 6.1 未开始。
- [ ] 6.2 未开始。
- [ ] 6.3 未开始。
- [ ] 6.4 未开始（identity rule 仅存在 Approved Change 文档，未在 config 旁新增说明）。

### 7. API serialization and in-repo web consumer

- [ ] 7.1 未添加 API tests。
- [~] 7.2 `_serialize_config` 已输出 common + `type` + `parameters`；现有 API contract test 仍断言旧扁平形状。
- [~] 7.3 `DashboardStrategySummary` 已改为 discriminated union；typecheck 通过。
- [~] 7.4 Dashboard 已只在 dual-momentum 分支读取 momentum fields；equal-weight render test 未添加。
- [~] 7.5 CommandPalette 两个 fixture 已迁移；`App.test.tsx` 的 dashboard fixture 未迁移，Vitest 失败。

### 8. Verification and quality gates

- [~] 8.1 最新目标 Python 集合（含 registry）为 `119 passed`；Ruff、format、mypy通过。Web typecheck/test/lint/CSS/build 已通过（`164 passed, 7 skipped`）。
- [x] 8.2 当前实现后全量 Python pytest：`592 passed, 1 skipped`。
- [~] 8.3 上轮 Ruff、format、mypy 已通过；本轮新增测试后最终仍需重跑。
- [~] 8.4 Web 门禁已通过；最终仍需在收尾时重跑。
- [ ] 8.5 未完成明确搜索审查。
- [ ] 8.6 未完成 migration/schema 差异审查与风险记录。
- [~] 8.7 `openspec validate add-strategy-pluggability --strict` 当前通过。

## 4. 已完成实现

- `strategy_config.py`：实现顶层 discriminated union、typed `parameters`、non-empty version、strict extra forbid、TypeAdapter helper、legacy flat loader message、dual-only defensive asset validation。对应 1.2–1.4；仅 config test 部分覆盖。
- `config/strategy_v1.yaml`：已改为 `type: dual_momentum` 与嵌套 `parameters`。对应 1.5；loader/config tests 通过。
- `strategies/types.py`：定义统一 position DTO、protocol、domain error。对应 2.2–2.3；无独立测试。
- `strategies/dual_momentum.py`：封装旧纯计算，按 active ETF 构造 defensive lookup。对应 3.2–3.4；未通过 golden tests。
- `strategies/equal_weight.py`：实现零 lookback、按 ETF id 排序、均分 Decimal 权重。对应 5.2；未测试。
- `strategies/registry.py`：注册 dual/equal factories 与 resolver。对应 2.4；未测试。
- `strategy_signal_generation.py`：shared wrapper dispatch、预期 `StrategyGenerationError` 转 failed result、空 active 失败、空 position success。对应 2.5–2.6；未完成回归。
- `strategy_signal_service.py` 与 `backtest_runner.py`：去除共享 defense lookup；runner 用 bound strategy lookback，拒绝负值，audit JSON 增加 type。对应 4.2、4.4–4.5；未通过回归。
- API/Web：序列化与 Dashboard type/render 已开始迁移。对应 7.2–7.5；web typecheck/lint 通过但 test 未全绿。

## 5. 当前进行中的修改

当前应视为 **task 1.6 / 1.7 的测试夹具与 direct validation caller 迁移**，随后才能可靠验证 2–5 节实现。

- 已写入但未验证：`strategy_config.py` 的 adapter annotation、registry 的 immutable representation、dual/equal strategies、generic wrappers、runner/service/API/Web 改动。
- 不完整：测试仍大量 flat config；test-generation 仍传删除的 `defense_lookup`；API 与 web dashboard fixture 仍旧 shape；无 equal weight/registry/identity tests。
- 继续入口：先读 `packages/core/tests/test_strategy_signal_generation.py`、`test_strategy_signal_service.py`、`test_backtest_runner.py`、`test_momentum_scoring.py`、`test_trend_filter.py` 的 config factories，逐个改为 nested literal 并改为 `validate_strategy_config(...)`；不要恢复 flat-config runtime compatibility。
- 不要重复实现：不要重新创建 union、strategy protocol、two strategy modules、generic dispatch、API serialization 或 Dashboard union；先审查和修正现有实现。

## 6. 修改文件清单

`git diff --stat`（生成 Handoff 前）为 13 tracked files，`306 insertions(+), 353 deletions(-)`；另有 untracked Change 目录、strategies 目录和无关 `.txt`。

- Modified: `apps/api/src/vela_api/config.py` — 新 API strategy shape。
- Modified: `apps/web/src/api/client.ts` — discriminated dashboard type。
- Modified: `apps/web/src/components/CommandPalette.stories.tsx`、`CommandPalette.test.tsx` — equal-weight fixture。
- Modified: `apps/web/src/pages/DashboardPage.tsx` — variant-safe rendering。
- Modified: `config/strategy_v1.yaml` — nested dual config。
- Modified: `packages/core/src/vela_core/{strategy_config.py,momentum_scoring.py,trend_filter.py,strategy_signal_generation.py,strategy_signal_service.py,backtest_runner.py}` — core migration。
- Modified: `packages/core/tests/test_strategy_config.py` — partial config coverage；其中 local compatibility shim 是待修复问题。
- Added/untracked: `packages/core/src/vela_core/strategies/{__init__.py,types.py,dual_momentum.py,equal_weight.py,registry.py}` — 新 strategy layer。
- Added/untracked: `openspec/changes/add-strategy-pluggability/` — 用户开始前已有的 Approved Change artifacts；本文件也位于其中。
- Added/untracked, **无关且不得触碰**：名称为 `现在我的策略只有一种，如果我改策略的话，需要改代码吗?.txt` 的中文文件。
- Deleted: 无。

## 7. Git 工作区状态

核查时输出的 `git status --short`：

```text
 M apps/api/src/vela_api/config.py
 M apps/web/src/api/client.ts
 M apps/web/src/components/CommandPalette.stories.tsx
 M apps/web/src/components/CommandPalette.test.tsx
 M apps/web/src/pages/DashboardPage.tsx
 M config/strategy_v1.yaml
 M packages/core/src/vela_core/backtest_runner.py
 M packages/core/src/vela_core/momentum_scoring.py
 M packages/core/src/vela_core/strategy_config.py
 M packages/core/src/vela_core/strategy_signal_generation.py
 M packages/core/src/vela_core/strategy_signal_service.py
 M packages/core/src/vela_core/trend_filter.py
 M packages/core/tests/test_strategy_config.py
?? openspec/changes/add-strategy-pluggability/
?? packages/core/src/vela_core/strategies/
?? 现在我的策略只有一种，如果我改策略的话，需要改代码吗?.txt
```

当前分支 `main`，没有为本次 Change 创建提交。开始前已有的未跟踪内容是 Change 目录与中文 `.txt`；不得 stash、reset、clean、checkout 覆盖，尤其不得覆盖该中文文件或删除/重建 `vela.db`。最近提交：`3d7f036a feat: fix factor HFQ strategy price — migrate from backward-adjusted to forward-adjusted pricing`。

## 8. 测试和验证结果

以下均为实际运行记录；未执行的命令不标为通过。

- PASS: `openspec validate add-strategy-pluggability --strict` — 当前严格校验通过；最终仍须在所有 task 完成后重跑。
- PASS（早期基线）：`uv run pytest packages/core/tests/test_strategy_config.py packages/core/tests/test_strategy_signal_generation.py packages/core/tests/test_strategy_signal_service.py packages/core/tests/test_backtest_runner.py apps/api/tests/test_api_config.py apps/api/tests/test_dashboard.py` — 变更前 `76 passed`；已过时，不能证明当前实现。
- PASS: `uv run pytest packages/core/tests/test_strategy_config.py -q` — 当前 `46 passed`；该文件含待移除 shim，不能单独作为 task 1 完成证据。
- FAIL: `uv run pytest packages/core/tests/test_strategy_config.py packages/core/tests/test_strategy_signal_generation.py packages/core/tests/test_strategy_signal_service.py packages/core/tests/test_backtest_runner.py packages/core/tests/test_momentum_scoring.py packages/core/tests/test_trend_filter.py apps/api/tests/test_api_config.py apps/api/tests/test_dashboard.py -q` — `52 passed, 60 failed`。主要失败为 union alias 没有 `.model_validate`（旧 fixtures/callers）；旧 `defense_lookup` 调用未迁移；`test_api_config.py` 仍断言 old serialized shape。需修复后重跑。
- PASS: `uv run ruff check . && uv run ruff format --check .` — 当前全部通过；修复后仍需重跑。
- FAIL: `uv run mypy --config-file pyproject.toml` — `packages/core/src/vela_core/strategy_config.py:158`：`STRATEGY_CONFIG_ADAPTER` 缺少类型注解；未修复。
- PASS: `npm --prefix apps/web run typecheck` — 当前通过。
- PASS: `npm --prefix apps/web run lint`、`npm --prefix apps/web run lint:css` — 当前通过。
- FAIL: `npm --prefix apps/web run test` — `App.test.tsx > loads dashboard aggregate data through the shared client` 仍给 dashboard strategy fixture 用旧 flat fields，Dashboard 因缺 `type` 未显示 `63 / 126 days`；`163 passed, 1 failed, 7 skipped`。未修复。
- NOT RUN: `npm --prefix apps/web run build` — 包含于 `lint && lint:css && typecheck && test && build` 的串行命令，但 test 失败所以 build 未执行；修复后必须单独/完整重跑。
- NOT RUN（当前实现后）: `uv run pytest` 全量 Python suite、API integration、web `check:bundle`；不得假定通过。

## 9. Review 结果

尚未进行独立 reviewer code review；此前只有实现者的局部检查，不能视为 task 要求的 Review。

已发现但未修复的高优先级问题：

1. **P1 — 旧 direct validation callers 未迁移。** `StrategyConfig` 是 `Annotated` union，`.model_validate` 不存在；多个 tests 立即失败。应改用导出的 helper/adapter，并把 raw dict 改为 nested shape。
2. **P1 — 测试中存在规避迁移的 local shim。** `packages/core/tests/test_strategy_config.py` 定义 local `class StrategyConfig`，只为保留 `.model_validate` 调用；这违反 task 1.7 和“不得通过特殊逻辑规避质量”。应删除 shim，显式调用 helper。
3. **P1 — 已删除的 `defense_lookup` 参数仍在 generation/backtest tests。** 必须迁移这些 tests，并确认 dual strategy 从 active ETFs 建 lookup。
4. **P1 — API/Web contract tests 未迁移。** API 断言 old top-level dual fields；`App.test.tsx` fixture 缺 `type`/`parameters`。
5. **P1 — mypy error。** Adapter 注解缺失。
6. **P1 — 无 registry/equal-weight/negative-lookback/identity-isolation tests。** specs 核心验收未被证明。

未完成的 review 检查：spec 覆盖、expected/unexpected error boundary、callback count、future-data truncation、transaction behavior、no concrete strategy imports/type branches、schema diff、无关修改。现有实现也尚未证明不破坏 dual momentum 行为。

## 10. 已知问题、风险和阻塞

- **P1 / 阻塞继续验证：** Python 旧配置 fixtures/direct callers。影响 core generation/service/backtest/momentum/trend tests；建议先以 nested literals + `validate_strategy_config` 迁移，不修改 OpenSpec。
- **P1 / 阻塞最终验证：** `defense_lookup` 旧测试 API。影响 generic wrapper regressions；建议删除参数并让 test active ETF set 决定 missing-defense 情形，不修改 OpenSpec。
- **P1 / 阻塞最终验证：** API/Web fixtures 未跟随 breaking shape。建议更新 API expectation 与 App dashboard fixture，补 equal-weight rendering test，不修改 OpenSpec。
- **P1 / 阻塞类型门禁：** adapter mypy annotation。建议用适合 mypy 的 `TypeAdapter[StrategyConfig]` 注解或等价显式类型；不修改 OpenSpec。
- **P1 / 阻塞 specs 覆盖：** registry/equal-weight/identity tests 缺失。按 tasks 2、5、6 实施；不修改 OpenSpec。
- **P2 / review 风险：** registry 用 `MappingProxyType` 而 spec/design 写“immutable plain-dict”。继续前阅读任务/测试期望并决定改为 module-constant plain dict，或用清晰的 immutable mapping type；若需改变设计文本才修改 OpenSpec，目前不应猜测。
- **P2 / review 风险：** `DualMomentumStrategyConfig` 增加 legacy-shaped convenience properties（`momentum` 等）；这可能弱化“parameters only”的迁移边界，应在 tests 迁移后评估并尽量删除，除非存在真实 public compatibility requirement。
- **非阻塞、已确认 out of scope：** same-identity concurrent-backtest read-isolation 风险保持 out of scope；无 DB migration。

当前没有外部环境阻塞，但上述 P1 项使 Final Verify 阻塞。

## 11. 关键设计决策

- 顶层 union 由 sibling `type` 判别，参数嵌套在 `parameters`；依据 design D6 与 strategy-configuration spec。明确不采用在 `parameters` 内部判别或继续接受 flat YAML。
- strategy 为参数绑定的 structural protocol，只有 `lookback_days()` 和单日期 `generate_signal(...)`；依据 design D1。明确不传 Session、不做 SQL、不做动态 discovery。
- shared wrapper 所有权包括 result/persist/error conversion；strategy 只返回统一 positions 或抛 `StrategyGenerationError`；依据 D2/D4。明确不让 concrete strategy 持久化/吞异常。
- dual momentum defense lookup 从 injected `active_etfs` 派生；依据 D2/D8。明确不再给 shared generic API 传 `defense_lookup`。
- lookback 表示 signal date 之前的 sessions；runner 继续 `lookback * 2 + 10` 日历缓冲；依据 D5/backtest spec。
- equal weight 不读 price panel、0 lookback、ETF id 稳定排序、`Decimal("1") / Decimal(N)`；依据 D8/strategy-pluggability spec。
- persisted identity 不含 type，故 type/参数改变必须使用不同 `(strategy_id, version)`；依据 D9。明确不增加 schema column/migration。
- API shape 固定为 common + `type` + `parameters`，Dashboard 以 discriminated union 渲染；依据 D10。明确不保留 dual-only unconditional top-level API fields。

## 12. 下一步执行顺序

1. 阅读本 Handoff、proposal、design、四个 delta specs、tasks；运行第 13 节只读检查，确认 status 与本文件一致。
2. 先完成 1.6/1.7：删除 `test_strategy_config.py` local shim；把全部 `StrategyConfig.model_validate(...)` callers 改为 `validate_strategy_config(...)`；把 raw dual fixtures 改为 `type: dual_momentum` 和 nested `parameters`。每个迁移点先写/调整断言并运行对应 test file。
3. 更新 generation/service/backtest tests，删除 `defense_lookup` argument；将 dual calculations direct helper calls 传 `config.parameters`。运行 core target suite，直到旧 dual regression 恢复。
4. 修复 `STRATEGY_CONFIG_ADAPTER` mypy annotation，运行 mypy；不要通过 ignore/弱化配置跳过。
5. 为 tasks 2.1、3.1、4.1、4.3、5.1、5.3 写 RED tests，再依次验证 registry/error boundary/lookback/equal weight。
6. 迁移 API contract 与 `apps/web/src/App.test.tsx` dashboard fixture；新增 equal-weight API/dashboard render tests。运行 API tests、web typecheck/test/build。
7. 实现 tasks 6.1–6.4 的 distinct identity fixtures、switching/isolation integration coverage与 config-adjacent identity documentation。
8. 每完成一个真正完成的 task 才勾选 `tasks.md`；不要一次性批量勾选。
9. 运行全量 Python pytest、Ruff、format、mypy、全部 web scripts、OpenSpec strict validate；再进行独立代码 Review，修复 P1/P2 真实问题并重跑全部门禁。
10. 更新本 Handoff 或完成报告。只有所有 43 tasks、质量门禁和 Review 均满足时才写 Final Verify PASS。

## 13. 推荐恢复命令

先运行（只读）：

```bash
git branch --show-current
git rev-parse HEAD
git status --short
git diff --stat
git diff --check
openspec status --change add-strategy-pluggability --json
openspec instructions apply --change add-strategy-pluggability --json
rg -n 'StrategyConfig\.model_validate|defense_lookup' packages apps tests --glob '*.{py,ts,tsx}'
```

局部恢复验证：

```bash
uv run pytest packages/core/tests/test_strategy_config.py -q
uv run pytest packages/core/tests/test_strategy_signal_generation.py packages/core/tests/test_strategy_signal_service.py packages/core/tests/test_backtest_runner.py packages/core/tests/test_momentum_scoring.py packages/core/tests/test_trend_filter.py apps/api/tests/test_api_config.py apps/api/tests/test_dashboard.py -q
uv run ruff check .
uv run ruff format --check .
uv run mypy --config-file pyproject.toml
npm --prefix apps/web run lint
npm --prefix apps/web run lint:css
npm --prefix apps/web run typecheck
npm --prefix apps/web run test
npm --prefix apps/web run build
openspec validate add-strategy-pluggability --strict
```

最终全量 Python 门禁（仅在局部绿后）：

```bash
uv run pytest
```

禁止使用 `git reset --hard`、`git clean -fd`、未经确认的 checkout/stash 操作，且不要删除/重建 `vela.db`。

## 14. 最终 Verify 状态

- 所有 tasks 已完成：**否**（0/43 checkboxes）
- OpenSpec Validate 通过：**是**（当前严格校验）
- 所有相关测试通过：**否**（目标 Python 60 failures；web 1 failure）
- lint 通过：**是**（Ruff、web eslint、stylelint）
- formatter check 通过：**是**（Ruff format）
- 类型检查通过：**否**（mypy 1 error；web typecheck 通过）
- 构建或质量门禁通过：**否**（web build 未运行；全量 Python 未运行）
- 已完成至少一次实现后 Review：**否**
- 无未处理高优先级 Review 问题：**否**（多个 P1）
- 实现与 specs 一致：**未证明**（部分实现已写，但关键 specs/tests 未完成）
- 无明显无关修改：**未证明**（工作区保留一个开始前已有的无关 `.txt`；本 Change 改动尚待 review）

## Final Verify: NOT READY

剩余条件：完成并勾选全部 tasks；迁移/修复 Python、API 与 Web tests；修复 mypy；运行 build 与全量 pytest；完成 registry/equal-weight/identity coverage；执行独立 Review 并修复所有 P1；重跑所有门禁。
