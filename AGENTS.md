# Vela Agent 使用规则

## 仓库

- 仓库级命令从 Git 根目录执行；使用 `git rev-parse --show-toplevel` 确认根目录，执行 OpenSpec 工作前确认最近的 OpenSpec root。
- 以当前仓库、Git diff、OpenSpec CLI 输出、代码和测试为事实依据。
- 修改前检查 `git status`，保留所有无关或未跟踪工作，尤其是其他 OpenSpec Changes。

## 数据库安全

- 仓库根目录的 `vela.db` 是用户的持久化本地数据；未经明确授权，不得写入、迁移、重置、替换或删除。
- 这包括以默认数据库为目标的 `rm -f vela.db`、`alembic upgrade`、`vela init-db`、同步、抓取、信号、回测和 walk-forward 命令。
- 需要写入数据库的验证必须使用测试自有的 `tmp_path` 数据库，或 `/tmp` 下的明确副本，并通过 `--database-url` 指定。
- 不得为通过验证而削弱测试或修改现有持久化数据。

## 验证范围

- 开发过程中优先运行覆盖改动行为的最小测试和检查。
- Python 源码、测试、依赖、迁移或 Python 工具配置有改动时，完成前运行完整 Python gate。
- Web 源码、测试、依赖或前端构建/工具配置有改动时，完成前运行完整 Web gate。
- 仅跨前后端或共享 CI/质量配置改动需要同时运行两套 gate。
- 仅文档或 Agent 指令改动只需静态内容和 diff 检查，不运行测试套件。

## Python 验证

- 从仓库根目录使用 `uv` 运行 Python 命令；局部测试使用 `uv run pytest <test-paths>`。
- 完整 Python CI-equivalent gate：
  - `uv sync --group dev`
  - `uv run --no-sync ruff check .`
  - `uv run --no-sync ruff format --check .`
  - `uv run --no-sync mypy --config-file pyproject.toml`
  - `uv run --no-sync pytest`
- 除非任务授权修改源码，否则不得运行会重写文件的 format 或 auto-fix 命令。

## Web 验证

- 从仓库根目录通过 `npm --prefix apps/web` 运行 Web 命令，不得替换为 `pnpm`。
- 仅在 `node_modules` 缺失或不可信、`package.json`/`package-lock.json` 发生变化，或明确要求干净依赖复现时运行 `npm --prefix apps/web ci`。
- 完整 Web CI-equivalent gate：
  - `npm --prefix apps/web run lint`
  - `npm --prefix apps/web run lint:css`
  - `npm --prefix apps/web run typecheck`
  - `npm --prefix apps/web run test`
  - `npm --prefix apps/web run build`

## OpenSpec

- 使用 `openspec list --json` 发现 active Changes；不得根据任务勾选或 handoff 推断状态。
- 使用 `openspec validate <change-name> --strict` 验证指定 Change。
- 需要检查更广泛的规格健康状态时，使用 `openspec validate --all --strict` 和 `openspec doctor`。
- 当前 CLI 没有 `openspec verify` 命令；不得声称已运行。改用严格验证、需求追踪、测试和项目 gate。
- 只有在用户明确要求时才归档、提交或推送。

## Git 安全

- 不得 reset、clean、丢弃或覆盖用户的无关改动。
- 存在无关工作时，不得使用 `git add .`、`git add -A` 或宽泛目录暂存。
- 按明确文件 allowlist 暂存，提交前检查 `git diff --cached`。
- 不得 force-push 或重写历史。
- 获得授权并推送后，确认远端分支包含预期 commit。
