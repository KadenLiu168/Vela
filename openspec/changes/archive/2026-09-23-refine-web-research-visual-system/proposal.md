## Why

上一轮 Celestial Research 已统一颜色语义和字体，但空间密度、面板层级、窄屏文字与组件状态仍缺少统一的产品契约。此次深化现有研究工作台，提高长页阅读和数据比较效率，并补齐当前 checkout 缺少的可重放浏览器验收入口。

## What Changes

- 保留深色配色、Geist 字体资源、三类按钮、当前路由和 Dashboard 五层研究顺序，统一页面、章节、同组内容的空间节奏。
- 明确标准/紧凑面板、控件尺寸、手机标题和重要辅助信息的字体角色，保持数字精度与数据语义。
- 统一导航、表单、表格、图表、状态反馈和 Command Palette 的视觉状态、响应式与 reduced-motion 行为。
- 建立长期维护的浏览器 fixtures、断言、截图和版本关联证据；覆盖代表页面、关键状态、断点、键盘及无障碍检查。
- 所有工作限于前端表现及其验证；不改后端、持久化数据、业务计算、操作触发语义或主题数量。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `design-system`: 空间/控件 Token、面板层级、共享标题响应式、组件状态和动效契约。
- `card-type-scale`: 重要辅助信息使用可读角色的明确例外，保留四级数据阶梯与跨页基线。
- `detail-page-typography-consistency`: 同视口跨页一致的标题角色，替换过时的标题 Token 引用。
- `web-frontend-app`: 全站研究层级、窄屏完整性、可访问交互及可重放验收要求；品牌适配手机标题。

## Impact

预计涉及 `apps/web/src/styles/tokens.css`、`styles.css`、现有 components/pages、对应 tests/stories、`docs/tokens.md` 与前端浏览器验证配置。复用 React/Vite、CSS 和 Ladle；仅允许新增测试用途的 Playwright 与 axe-core 集成依赖，不引入运行时 UI/动效框架。

归档 `2026-09-22-redesign-web-visual-system/evidence/browser/` 当前仅存在 README 和结果 JSON，不能作为可执行 harness。新入口位于 `apps/web/e2e/`，历史记录保持原样。数据库验证完全通过浏览器拦截的固定 API 数据隔离；不得启动默认数据库写操作。
