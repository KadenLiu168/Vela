## Context

动机见 proposal.md。当前 React/Vite 前端使用原生 CSS、单一 tokens.css、本地 Geist 字体、Ladle 和 Vitest。styles.css 含共享规则及 1024/900/720px 覆盖；桌面卡片 y padding 为 20px，部分窄屏规则却扩大到 32px。全局 section-gap 为 96px，列表标题到内容为 48px。此次需要改变这些空间契约，而不是重复已完成的配色迁移。

现行 research-workbench-ui 和 backtest-results-ui 已规定研究顺序与折叠默认值；本次保留。detail-page-typography-consistency 的标题场景仍引用已移除的 text-heading-sm，本次在修改同一标题行为时同步更正。

当前归档验收目录只有 README 与 review-results.json，没有 runner、fixtures 或 lockfile。旧结果不证明当前版本通过，也不能提供可执行复现。

## Goals / Non-Goals

**Goals:** 将既有 Celestial Research 深化为一致的研究界面：空间分组清楚、关键文本可读、窄屏证据完整、状态反馈统一，并有与实际构建关联的浏览器验收。

**Non-Goals:** 不新增主题、侧栏、导航入口、字段或计算；不替换字体二进制；不改变图表数据/坐标计算、金融格式化、后台请求与操作锁；不做全站 CSS 文件拆分或大型 React 抽象；不修改旧归档证据。

## Decisions

### 1. 沿用现有视觉身份，按角色深化

选择 Taste 的克制研究工作台方向（variance 3 / motion 2 / density 7）。相比高密度终端，保留更好的长文本阅读；相比全新明亮主题，避免重新迁移所有颜色与图表。配色和 Geist 文件完全复用，新增生产依赖为零。

普通 research panel 使用 surface-panel，突出指标和 Command Palette 使用 surface-raised。card-bg 保留 raised，新增 panel-bg 指向 panel。普通面板不加阴影，card-shadow 变为 none；浮层沿用 shadow-xl。边框与半径不变。通过显式表面角色覆盖而非全局替换 raised 实现，保证 palette 契约不变。

### 2. Token 增量清单和消费者

所有新 token 均在唯一 :root 声明；响应式规则选择 token，不在 media query 重新声明变量。尺寸值用 rem 表达（以下 px 为默认根字号 16px 下等价值），从而随用户根字体设置缩放；断点继续使用现有 CSS px。

| Token | 动作 / 默认值 | 消费者 |
| --- | --- | --- |
| --section-gap | 96px 改为 var(--space-xl)，48px | 顶级研究章节 |
| --section-gap-compact | 新增 var(--space-lg)，32px | <=720px 顶级章节 |
| --group-gap | 新增 var(--space-md)，24px | 相关指标/筛选内容组 |
| --heading-content-gap | 新增 var(--space-md)，24px | 所有页标题到首内容 |
| --page-gutter-wide | 新增 var(--space-lg)，32px | >1024px shell 水平边距 |
| --page-gutter-medium | 新增 var(--space-md)，24px | 721..1024px shell 水平边距 |
| --page-gutter-compact | 新增 var(--space-sm)，16px | <=720px shell 水平边距 |
| --card-padding-y | 20px 改为 var(--space-md)，24px | 标准面板 y padding |
| --card-padding-x | 保留等值24px，使用 var(--space-md) | 标准面板 x padding |
| --card-padding-compact | 新增 var(--space-sm)，16px | 紧凑面板和手机面板两轴 |
| --panel-bg | 新增 var(--surface-panel) | 普通研究面板 |
| --card-shadow | 改为 none | 普通/指标卡片，浮层不消费此别名 |
| --control-min-height | 新增 2.25rem，36px | 按钮、输入、选择器 |
| --control-touch-size | 新增 2.75rem，44px | <=720px 或 pointer:coarse 控件高度和最小宽度 |
| --text-page-title-compact | 新增 1.75rem，28px | <=720px 所有页标题 |
| --leading-page-title-compact | 新增 2.25rem，36px | <=720px 所有页标题行高 |

将本次消费的既有 text/leading 尺寸 token 从 px 转为等值 rem，不改变默认计算大小；包括 card 行高例外。space/spacing ladder 同样转等值 rem 以支持用户字体设置。保留 page-max-width 1200px 和其他既有 Token；不做未使用 Token 清理。内部行距继续使用已有 8/12/16px primitives，无额外别名。

标题默认 36/40、章节 22/28、卡片 16/22、正文 15/22、数据 13/20、指标 24/30 和 32/36，均不改变默认尺寸。手机仅页标题改 28/36。重要日期值和证据计数至少 label 12/16，状态/风险/不可用原因至少 dense 13/20；compact-list 标签仍 11/20，数值仍 13/20，保持共享基线。语义 class 标记特定内容，不通过字符串是否像数字推断字体。

### 3. 页面与组件按现有所有权迁移

Dashboard 保留 current state → latest signal → strategy performance → OOS robustness → deep evidence → reference/operations；回测详情保留现有六段顺序和 Signals tab。先在这两页验证同组/跨组间距，然后推广到 Signal、Walk-forward、ETF 和列表页面。

AppShell 继续顶部导航和原品牌，API 地址保持可访问、使用次级文字并允许长地址换行，不增加隐藏信息开关。统一页首标题/说明/操作布局：900px 以下自然堆叠。详情主要章节使用 section-gap，面板内部及指标组使用 group-gap；避免 margin 与 gap 同时累加。既有章节标题后16px、run-trigger 后16px等非冲突局部契约保留。

标准研究区域 24px padding，紧凑指标/事实区域显式使用 compact 16px；720px 以下所有面板16px。表格保留列与语义，数值右对齐、普通文字左对齐，表头使用 label role；数据行采用最小40px高度、可随多行文字增长，含触摸控件时由44px目标决定。局部滚动区域有 accessible name、tabIndex 和可见焦点。

按钮继续三类，不添加第四类或新的主操作；输入帮助/错误通过 aria-describedby 关联，错误附 aria-invalid；复用已有 loading/error 状态，不新建操作状态机。为按钮/输入/面板/混排表格增加必要的 Ladle stories，覆盖适用状态。

仅在结构和行为均重复时提取组件；否则复用现有组件和共享选择器。修复与新样式直接冲突的 ancestry 覆盖，并用计算样式断言防止再次覆盖；不以文件行数为理由重写页面。

### 4. 响应式与 Motion

保留1024/900/720边界：宽屏相关指标并排，<=900px指标最多两列，<=720px主要内容单列。宽表独立滚动而不是删列；长名称换行，JSON等预格式化内容有局部滚动或安全折行。图表只调整展示尺寸、刻度显示数量和图例布局，不更改数值/坐标算法。策略/两个基准按稳定 key 使用实线/虚线/点线，图例同步，保留现有系列色和文本/表格替代。

shell 使用 min-height:100dvh 和合理回退；palette 使用动态视口可用高度及内部滚动，保持纯 CSS 实现（不引入 VisualViewport 订阅）。

hover 120ms、可选浮层200ms、折叠可立即变化或<=200ms；不新增动画库。减少动效时所有使用动效的组件及伪元素过渡/动画关闭，Skeleton为静态占位并保留文本状态。保持路由自身的焦点/滚动语义。

### 5. 可重放验收与证据矩阵

在 apps/web/e2e/ 建立独立于后端的 fixtures 与 Playwright 用例，配置位于 apps/web/playwright.config.ts，npm --prefix apps/web run test:e2e 运行生产构建的静态服务器（由 runner 管理启动/关闭）。新增 @playwright/test、@axe-core/playwright 仅为 devDependencies；按安装时可用版本锁定 package-lock，不新增 Python 工具。

验收构建显式使用相对 `/api` base URL，并由 runner 启动无 API proxy 的生产静态预览；不使用当前 `vite.config.ts` 中将 `/api` 转发至 `127.0.0.1:8000` 的开发服务器。所有 API 方法/path/query 显式匹配 fixtures，未匹配请求记录并 abort，最终断言无未匹配请求。浏览器只允许 runner 启动的静态服务器 origin 提供页面及资产；该 origin 的 `/api` 请求也必须先由 fixtures 拦截，任何其他 origin（包括本机其他端口）一律阻断并令验收失败。阻止 service worker 绕过拦截。GET和被测POST均在内存中模拟；不启动 FastAPI，不设置默认 vela.db 写入口。以故意未匹配的 API 请求及本机其他端口请求验证 fail-closed。本次操作回归测试可点击按钮，但网络写入只落在拦截模拟器。

| 范围 | 状态 | 视口 / 验证 |
| --- | --- | --- |
| 全8个业务路由及404 | populated；404自身状态 | 1440x1000、390x844：层级、文本、控件、overflow、axe |
| Dashboard + Backtest Detail | populated（详情含展开的Deep Analysis） | 320x844、768x1000、1024x1000；1025/1024/1023、901/900/899、721/720/719：断点与计算样式 |
| Dashboard + 三个列表 | loading/empty/error | 1440x1000、390x844：状态组件与重试 |
| Backtest + Walk-forward Detail | legacy/insufficient/failed；Walk-forward queued/running | 390x844：证据完整、不可用原因、操作可达 |
| Signal Detail + ETF Detail | 长中英名称、负数、长标识 | 320x844：字体、完整性及图表/表格 |
| Palette | populated/filter-empty/source-error | 1440x1000、390x844、390x400：焦点、激活项、滚动、关闭恢复（短视口不模拟软件键盘） |
| 共享控件/表格/图表 | 各适用状态 | reduced-motion、pointer:coarse、文本放大、对比度和非颜色线型 |

200%文字放大通过根字号放大检查相对字体；320px重排与全部代表内容纳入自动化验收。移动端人工验收（真实设备软件键盘与读屏人工步骤）已按用户决定移出范围；键盘可达性、对比度与窄视口完整性由自动化断言覆盖。

报告记录 git HEAD、tracked diff+untracked前端源码 fingerprint、build manifest hash、fixtures/harness hash、浏览器版本、route/state/viewport、断言结果及截图hash。排除 node_modules、dist、报告本身等生成物避免自引用。缺证据、未知请求、控制台未处理异常、失败断言均阻止验收。输出写入专用报告目录；评审最终报告和截图作为本 Change evidence 一并保留或关联不可变可访问工件，旧归档不改。

### 6. 规格和验证边界

四个 delta 能力之外的研究计算/数据要求保持不变。design-system 已有 spacing ladder、radius、颜色值约束继续保留；更新 type scale、heading、card padding、surface 和 rhythm 冲突条款。card-type-scale 只增重要内容的角色例外，不改变四级阶梯本身。

完整 Web gate：lint、lint:css、typecheck、test、build。运行 `test` 和验收构建时清除外部 `VITE_API_BASE_URL`，避免现有条件式 API 集成测试访问真实本机服务，并固定验收构建的相对 `/api` 地址。额外运行 lint:css:root、build:tokens-doc（再运行确认生成物稳定）、ladle:build、test:e2e。本次只涉及前端和规划文件，正常不需要 Python gate；若实施意外修改 Python 相关文件，须重新审视范围并执行完整 Python gate。

## Risks / Trade-offs

- [全局 CSS 层叠使尺寸回退] → 比较真实计算样式与代表页面，再推广；不只搜索变量名称。
- [更紧凑导致重要证据难读] → 固定最小文字角色，长文本和负值fixture，保持原有精度与来源。
- [普通面板背景变化降低边界识别] → 对比度按实际文字/状态组合检查；必要控件边界独立满足3:1，不要求装饰边框承担交互识别。
- [自动化验收覆盖范围有限] → 对比度、键盘流程、焦点与文本放大均以自动化断言覆盖；不在自动化覆盖内的移动端人工验收已按用户决定移出范围，不在报告中宣称未经验证的结论。
- [浏览器工具增加维护成本] → 单一web锁文件、固定fixtures、小型覆盖矩阵；不引入泛用证据平台。

## Migration Plan

1. Apply前读取本Change并严格验证；建立浏览器入口，在样式变更前采集当前基线，不把旧报告当基线。
2. 迁移Tokens及对应集中测试，完成Dashboard和回测详情样板；以新契约比较前后截图/计算样式，失败就修正消费规则，不任意改验收值。
3. 推广共享组件和其余路由，完成响应式、motion和a11y。
4. 更新生成文档，完成全部gate和证据；保留代表页面前后对照。只有用户明确要求才归档/提交/推送。
5. 如需回退，只回退本Change对应前端和验证文件；无数据库迁移、数据清理或历史重写。
