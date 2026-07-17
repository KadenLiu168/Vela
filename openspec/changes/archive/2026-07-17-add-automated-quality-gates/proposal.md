## Why

Vela 已有 Ruff、pytest 和 mypy 等本地工具，但缺少自动化执行与合并门禁，质量约束仍依赖开发者手工记忆，容易随项目扩展而退化。仓库同时包含 Python 后端与前端应用，已经到了需要用最小 CI 与本地预提交钩子把质量规则真正变成门禁的阶段。

## What Changes

- 新增仓库级自动化质量门禁，在 PR 和主分支 push 上自动运行核心验证。
- 使用现有 `uv` 工具链执行 Python 侧检查，避免引入额外的构建框架。
- 将前端现有 lint、typecheck、test 和 build 验证纳入同一门禁。
- 新增本地 pre-commit 钩子，为提交前提供快速反馈。
- 为 mypy 增加基础配置，使类型检查从“可选工具”变成稳定门禁。
- Ruff 保持现有基础规则，安全与复杂度规则分阶段收紧，不把首轮门禁变成大规模无关清理。

## Capabilities

### New Capabilities
- `automated-quality-gates`: 定义仓库级 CI、pre-commit、本地验证与渐进式静态检查门禁要求。

### Modified Capabilities
- `test-suite-validation`: 扩展现有验证契约，使 Python mypy 与 CI 可复用命令纳入质量门禁要求。

## Impact

- 新增 `.github/workflows/ci.yml`。
- 新增 `.pre-commit-config.yaml`。
- 更新 `pyproject.toml` 中的 mypy 和 Ruff 配置。
- 影响 GitHub 仓库分支保护/规则集的合并策略。
- 影响所有 Python 后端包、API、CLI、前端 app 与测试目录的提交和合并流程。
- 不改变业务运行时行为、API contract、数据库 schema 或策略逻辑。
