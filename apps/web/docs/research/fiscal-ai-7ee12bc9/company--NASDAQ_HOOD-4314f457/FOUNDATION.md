# Fiscal 基础实现与输入通道诊断（2026-10-09续开发）

## 本轮基础代码

按 clone-website Phase 2 的 foundation-first 要求，由主代理顺序实现基础，未派发交互组件。Phase 1 全状态仍未完成；本次是仅凭已归档证据可独立实现的基础准备，不把完整门槛降低为默认截图。

| 文件（`src/components/sites/fiscal-ai-7ee12bc9/shared/`） | 内容 / 证据 |
| --- | --- |
| `fonts.ts` | next/font/local：Plus Jakarta Sans 400/500/600、DM Mono 400/500、Space Grotesk 500；6个已验TTF，path相对调用文件；变量限定Fiscal，未挂到根layout |
| `foundation.module.css` | 本地scope类：默认背景、输入背景、选中导航、注册绿、文字、帮助文字及64px/80px壳尺寸；均来自默认计算样式，无全局选择器/主题/hover猜测 |
| `icons.tsx` | 9个真实SVG：关闭、Dashboard、Analysis、Charting、Screener、Query、Earnings、Fund Letters、Resources；路径/viewBox/默认尺寸来自shell-assets-and-css归档，使用currentColor；图标为装饰，标签由未来控件提供 |
| `types.ts` | 来源公司身份与导航文本/pathname类型；只表示来源，不替代产品instrumentId或能力资格 |

未新增依赖、来源路由、lab或产品导航，没有复制来源整个CSS/脚本。类型/样式/字体暂未被产品页面导入；生产build验证既有页面，不能声称已在产品中呈现或已通过字体渲染对照。下一批完整组件导入时需验证字体输出与来源截图。

实现前读取本项目安装的Next文档 `01-app/01-getting-started/13-fonts.md`、`11-css.md` 与font API，遵守本地相对路径、多权重、CSS隔离及命名导出。

## 输入阻塞复查

在同一浏览器新建来源标签后，页面标题/默认DOM可读取，但创建流程的状态取得超时。普通locator点击、force点击、CDP Runtime只读及CDP Input也发生超时；反复重试不足以证明交互成功。

临时显示浏览器后，DOM及矩形读取曾恢复（viewport618×683，burger expanded=false），但点击仍超时。重新定位当前任务也没有得到成功输入的验证。只证明读/输入通道行为不同，尚不能确认根因是原站控件、隐藏渲染或面板挂载；没有为绕过而注入脚本、修改页面DOM、禁用校验或改浏览器配置。

已向用户请求关闭再打开右侧浏览器面板。恢复后先检查原burger状态，再做一次点击→状态检查，成功才继续采样；不从迟到动作推断状态，不盲目累积更多标签。

菜单/搜索/hover/键盘/桌面内部滚动仍未补全，builder派发门槛保持。字体与默认tokens属于基础准备，不等于完整Phase2或门户重构完成。

## 验证与增量复核

85df17c：全仓lint、typecheck和生产build通过，构建路由保持原有集合；独立核验6个本地字体路径、9个SVG path/viewBox/默认宽高与原归档逐项一致。未导入页面，因此未宣称字体loader在产品页已渲染，也没有重复无变化后端或前轮36项行为套件。

沿用R1既有code-review流程，仅定向aac6dd9...85df17c新增差异，Standards0项、Spec0项，不重复整阶段旧代码。提交中文、未push或部署。浏览器恢复问题仍需关闭/重新打开面板后继续核验，不将输入尝试或显示面板当恢复成功。

## 再次续开发：来源阻塞对照与图标补齐

再次检查时，旧来源标签4已不在本会话，当前标签清单为空；没有假定用户已完成面板重开。新建来源标签5已出现正确标题/URL，但创建时状态获取超时、getTab状态获取超时，直接tabs.get句柄可得而DOM snapshot仍超时。

为定位范围，在同一浏览器建立临时localhost原生HTML（无外部依赖或脚本），details/summary默认关闭；snapshot 0.041秒、语义点击及更新snapshot 0.321秒，展开后显示“展开成功：原生点击通道可用”，截图0.042秒。随后同一标签6导航Fiscal再次超时，pageAssets.list也超时。由此确认基本读取/点击可用、阻塞在Fiscal页面上下文仍复现；不是全面输入通道失效，仍不能断言原站故障、反自动化或平台根因。未注入DOM或更改安全/浏览器配置。

本地诊断截图为`.test-output/browser-input-probe/open.png`，不是来源截图或产品验收。已请求用户手动检查Fiscal菜单是否正常响应；没有重试此前55个限流/拒绝资产，也没有将本地点击成功当成来源交互采全。

基础补齐6个实际来源glyph，shared/icons.tsx累计15个命名导出：

| 新增 | 原归档来源 | 保真边界 |
| --- | --- | --- |
| FiscalLogoIcon | ph-sidebar__dashboard-logo-link | 原path/viewBox，按h-full/w-full占满调用方；仅来源参考资产，不替换TradeAgent品牌 |
| SettingsIcon | Settings文字控件SVG0 | 22×22，原填充图形 |
| ChevronDownIcon | ph-sidebar__analysis-nav-link SVG1 | 原viewBox15×15与evenodd路径，默认16×16见desktop-chrome计算样式；无展开旋转假设 |
| UpdatesIcon | ph-sidebar__product-updates-card SVG0 | 20×20；调用方可按已采实值覆盖，不把桌面/手机不同尺寸合并为一条控件规格 |
| ChevronRightIcon | ph-sidebar__product-updates-card SVG1 | 16×16，原path |
| HelpIcon | shell-assets-and-css icons的header help control | 20×20，保留circle/path/line、无填充、2px描边和圆角端点 |

这仍是主代理顺序执行的Phase2基础准备。没有导入产品路由、猜造菜单状态、派发builder或宣称/app重构完成。新增图标已通过全仓lint/typecheck；页面装配后仍须进行字体及图标渲染视觉对照。

### Standards

沿用R1既有流程，定向a63c541...4b10733新增差异，0项可行动发现；未重复整阶段旧代码审查。

### Spec

同一新增差异0项可行动发现。路径/子图元/viewBox/尺寸/填充规则/描边均与来源归档一致；未将本地诊断赋予来源恢复或门户验收资格。

临时本地诊断标签已关闭，诊断服务已停止；源标签6已标记handoff并显示供用户检查，未设置新视口。显示后DOM读取仍超时，尚未确认Fiscal菜单点击成功；下一步依用户手动响应结果定位，不再机械重试同一输入。补充紧凑诊断截图：`.test-output/browser-input-probe/open-compact.png`。
