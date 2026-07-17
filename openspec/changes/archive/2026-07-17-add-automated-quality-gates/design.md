## Context

Vela 当前已经具备本地质量工具基础：`pyproject.toml` 配置了 pytest testpaths 和 Ruff 基础规则集，dev dependency group 里也已经声明了 `mypy`、`pytest`、`pytest-cov` 和 `ruff`。前端同样已有 lint、lint:css、typecheck、test、build 命令。缺口不是“有没有工具”，而是这些检查仍然依赖开发者手动执行，没有进入提交与合并路径。

## Goals / Non-Goals

**Goals:**

- 建立最小但真实的 CI 门禁，在 PR 和主分支 push 上自动运行 Python 与前端验证。
- 复用仓库现有工具链，让本地命令与 CI 命令一致。
- 为 mypy 建立可执行的基础配置，而不是只安装依赖。
- 引入 pre-commit 作为轻量本地反馈层。
- 保持 Ruff 基础规则稳定，安全和复杂度规则分阶段引入。
- 明确 branch protection 是真实门禁的一部分。

**Non-Goals:**

- 不引入 tox 作为跨环境矩阵工具。
- 不新增 Makefile 作为必要入口。
- 不在首轮强制全仓 `mypy --strict`。
- 不改变业务逻辑、数据库 schema、API contract 或前端 UI。
- 不把完整 pytest 或前端 build 放进 pre-commit。

## Decisions

### Decision 1: CI 是核心门禁，pre-commit 是辅助层

CI 才能稳定阻止回归进入主分支；pre-commit 只能提供本地反馈。因此先落地 GitHub Actions，再补本地 hook。

Alternatives considered:

- **只加 pre-commit**：反馈快，但可绕过，不能约束合并。
- **只依赖手工命令**：无法形成真正门禁。

### Decision 2: Python CI 直接使用 `uv`

Python job 通过 `uv sync --group dev` 安装依赖，并用 `uv run` 执行 Ruff、mypy、pytest。这样本地和 CI 的路径一致，不额外引入 tox 或 Makefile。

Alternatives considered:

- **tox**：适合多版本矩阵，但会增加重复配置。
- **Makefile**：可作入口，但不是门禁本体。

### Decision 3: mypy 先建立基线，再渐进收紧

首轮 mypy 只覆盖 `apps/api/src`、`apps/cli/src` 和 `packages/core/src`，并使用 Python 3.11 语义、显式的 warning 选项和针对第三方库的定向处理。先让门禁可执行，再逐步扩大严格度。

Alternatives considered:

- **立即 `strict = true`**：容易一次性暴露大量历史问题。
- **只安装 mypy 不配置**：无法形成稳定约束。

### Decision 4: Ruff 安全/复杂度规则分阶段启用

先保留现有 `E`、`F`、`I`、`UP`、`B` 基础规则和 format check。`S`、`C90` 等扩展规则后续单独推进，并通过 `per-file-ignores` 处理测试误报。

Alternatives considered:

- **一次性启用更多规则集**：覆盖更广，但会把门禁建设变成大规模 lint 清理。
- **永远保持基础规则**：短期简单，长期会漏掉退化。

### Decision 5: 前端验证纳入同一个门禁，但拆分 job

Python 与前端各自独立成 job，失败时更容易定位，也更适合各自缓存依赖。

Alternatives considered:

- **只跑 Python**：无法覆盖 monorepo 里的前端质量要求。
- **一个 job 串行跑所有检查**：实现简单，但缓存和定位都差。

### Decision 6: branch protection 需要单独配置

`.github/workflows/ci.yml` 只能提供检查结果，真正禁止失败 PR 合并还需要 GitHub branch protection 或 ruleset。这个步骤应在任务和文档中明确。

Alternatives considered:

- **只提交 workflow**：检查会跑，但仍可绕过。
- **把分支保护伪装成代码改动**：不符合 GitHub 的实际管理方式。

## Risks / Trade-offs

- [Risk] 首次 CI 暴露既有失败 → Mitigation: 先以现有基础规则建立门禁，历史问题单独拆分修复。
- [Risk] pre-commit 过重影响提交体验 → Mitigation: 只放 Ruff check/format 和轻量文件检查。
- [Risk] mypy 对第三方库支持不足产生噪声 → Mitigation: 用定向配置或 stub 处理，不做全局粗暴忽略。
- [Risk] 前端和 Python job 缓存复杂化 → Mitigation: 保持两个独立 job。
- [Risk] 没有 branch protection 时门禁可被绕过 → Mitigation: 在任务和文档中明确要求启用保护规则。
