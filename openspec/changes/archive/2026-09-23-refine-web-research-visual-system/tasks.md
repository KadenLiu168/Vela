## 1. 基线与隔离验证入口

- [x] 1.1 核对当前源码、active Change及四份delta，记录改动前路由/组件/Token消费者清单；验证Dashboard五层和回测详情六段顺序与现有规格一致，保留所有无关工作。
- [x] 1.2 建立apps/web/e2e、Playwright配置及test:e2e脚本，加入仅测试使用的依赖与lockfile；依赖变化后运行npm --prefix apps/web ci，验证 runner 使用相对`/api`构建并启动/关闭无API proxy的生产静态服务器，不启动后端。
- [x] 1.3 建立完整method/path/query匹配的内存API fixtures、只放行runner静态服务器origin的网络阻断和service-worker隔离；该origin的`/api`必须先被拦截，本机其他端口也阻断。用故意未匹配API及本机其他端口请求验证阻断并令验证失败，确认任何POST不抵达真实API。
- [x] 1.4 在视觉修改前采集Dashboard/Backtest Detail的1440与390基线及现有状态，输出源码/build/fixture/harness身份和截图hash；验证报告引用的工件实际存在。

## 2. Token、Typography与空间

- [x] 2.1 实施design.md第2节Token清单及消费尺寸等值rem迁移，保留颜色/字体资产/半径/1200px宽度；以集中测试和浏览器计算样式验证默认尺寸、唯一root和放大行为。
- [x] 2.2 统一全站页标题36/40及<=720px的28/36角色，落实重要日期/计数/状态文字角色；验证同视口跨页字体一致、Sans/Mono内容语义和compact-list的11/20与13/20基线不回退。
- [x] 2.3 统一章节48/32、同组24、页标题后24、章节标题后16px节奏及24/16px面板padding，清除直接冲突覆盖；在Dashboard与Backtest Detail比较前后截图，验证无重复margin/gap及风险信息丢失。

## 3. 组件与页面推广

- [x] 3.1 为标准面板应用panel表面、强调指标保留raised并去除卡片阴影，保留palette浮层层级；验证普通/强调/浮层三种角色和实际文本对比度。
- [x] 3.2 统一按钮、输入、选择器适用状态与36px/44px目标、pending宽度和错误关联；通过组件交互测试验证三类按钮、原操作锁、aria-pressed、aria-invalid及错误关联。
- [x] 3.3 在Ladle补充按钮、输入、面板和混排表格的状态示例，复用既有反馈组件；验证所有适用状态可见且生产构建不包含catalog。
- [x] 3.4 将共享页首、空间和组件规范推广到Signal/Backtest/Walk-forward列表和详情、ETF及404；验证路由/字段/默认折叠/研究顺序和既有格式化结果不变，API元信息保持可访问。
- [x] 3.5 统一表格数值右对齐、名称换行及可访问局部滚动，图表系列补充稳定线型及同步图例；用长名称、负值、空值和三系列fixtures验证数据精度、语义和文本替代不丢失。

## 4. Responsive、Motion与Accessibility

- [x] 4.1 落实1024/900/720断点、32/24/16页边距、指标列数及手机单列布局；按design.md矩阵验证页面无横向溢出、表格区域可键盘滚动和操作可达。
- [x] 4.2 调整shell/palette动态视口与内部滚动；验证390x400短视口下输入/激活结果可达。
- [x] 4.3 统一120ms交互反馈及可选200ms浮层，关闭数字/图表等待和装饰性入场；通过reduced-motion浏览器计算样式验证组件及伪元素无非必要动效且加载提示仍存在。
- [x] 4.4 验证并修复本次涉及的焦点可见性、遮挡、skip link、路由焦点、弹层进入/限制/恢复和异步播报；键盘完整流程、axe及实际前景/背景对比度检查均通过。

## 5. 综合验收与文档

- [x] 5.1 完成design.md全部route/state/viewport矩阵及断点前后1px验证，记录每项spec对应断言或人工步骤；结果包含截图、计算样式、失败项和版本身份，验证报告不会将旧构建结果当作当前通过。
- [x] 5.2 使用200%文字设置及320px重排检查全部代表内容；验证名称、状态、单位、操作无截断/覆盖，宽表只在自身区域滚动。
- [x] 5.3 已按用户决定移出范围：不再要求真实移动设备软件键盘与 VoiceOver 人工验收；窄视口与键盘可达性由自动化验收覆盖（见 4.2/4.4）。
- [x] 5.4 生成docs/tokens.md并验证再次生成无差异，补充可从干净checkout运行的浏览器验证说明和代表页面前后对照；保证依赖、fixtures和runner均纳入交付清单，截图和报告可访问。
- [x] 5.5 清除外部`VITE_API_BASE_URL`后运行完整Web gate：npm --prefix apps/web run lint、lint:css、typecheck、test、build；额外执行lint:css:root、ladle:build和test:e2e，确认全部通过并记录实际结果。
- [x] 5.6 运行openspec validate refine-web-research-visual-system --strict及diff检查，核对需求→实现→证据；确认未修改持久化数据库及无关文件，未完成证据不得勾选完成。归档/提交/推送留待用户明确授权。
