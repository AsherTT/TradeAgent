# 搜索采样恢复与首个组件实现

2026-10-10维护入口修订：本档案随60e6316源码迁入`D:/桌面/Trade/TradeAgent/apps/web`。后续采样、spec、builder和提交均在新入口进行；下文旧目录和旧提交号为来源历史，不是后续写入目标。当前未完成事项与来源门槛保持。

## 迁入后平板补采

### 后续增量：无结果组件与HOOD键盘状态

主仓74466b4归档SearchEmptyMessage完整spec及三尺寸段落全部CSS/指针状态，ff07646通过隔离builder实现。合并后lint/typecheck/build通过，原10个page路由保留；R1原流程一次定向双轴复核74466b4...ff07646均0项。两个静态组件SearchEmptyMessage/SearchGuidance已通过独立实际SSR+CSS+本地字体的三尺寸渲染对照，但验证页手动映射CSS类与@font-face，不作为Next字体loader、产品父布局或/app接入验收。见[组件增量验收](STATIC_COMPONENT_VALIDATION_20261010.md)。未接任何正式路由。

新档案全部位于本目录，截图在既有同page-key命名空间：

- `v602-{desktop,mobile}-hood-result-cards-deep-20261010.json.gz`保存公司/ETF/投资者代表卡片的所有后代样式，桌面26/20/13节点、手机25/20/13节点。部分卡片超出当前滚动区，不能以DOM存在代替可见/hover/导航验收；未收齐30条HOOD结果的全部CSS。
- `v602-desktop-hood-result-company-hover-20261010.json.gz`确认真实CDP鼠标移动后公司卡片:hover=true、背景rgb(64,64,79)。baseline档已经相同背景且悬停，故**没有取得该卡片真正的非hover→hover样式差值**；ETF/投资者hover仍待。
- ArrowDown从首条HOOD移到第二条ASML，ArrowUp恢复HOOD；输入焦点保持。两份`v602-desktop-hood-arrow*20261010.json`保留完整href/data-active/背景列表。鼠标仍在HOOD上，HOOD悬停背景与ASML键盘选中背景分开记录，不能合并成统一active色。此证据只覆盖本轮桌面All/HOOD序列。
- Tab将输入由`HOOD`改为`HOOD pages`，input保持active；显示47条内部页面结果和Clear Search。`v602-desktop-hood-tab-20261010.txt`是完整DOM快照；`v602-desktop-hood-pages-card-and-clear-20261010.json.gz`保留全部链接文案/href、首条Income Statement卡片19节点和Clear Search三节点的全部CSS；同名Tab来源JPEG已查看。其他46条页面结果的完整CSS、移动/平板和返回键行为尚缺。
- Clear Search点击后query为空、恢复30条默认结果、按钮消失且输入仍active，见`v602-desktop-hood-pages-clear-20261010.json`。
- 重新输入HOOD确认首条data-active=true后按Enter，搜索输入消失、可见dialog为空，URL仍为`/company/NASDAQ_HOOD/`且Robinhood标题存在；before/after两档保存。该同pathname选择验证不授予其他结果跨pathname或分类导航验收。

四个较大的深层档案以gzip无损保存，解压字节逐一核验与原JSON一致。资产403/429保持，不新增下载。来源临时视口最终reset、搜索已由Enter关闭；当前标签只用于后续采样，不复用旧tab8编号。

下一步继续补卡片非hover/hover/focus、各分类与三尺寸键盘/关闭/动画、直接页面结果及导航/公司/图表状态，再按完整spec逐个builder。不能由本轮小组件和桌面键盘状态推断完整搜索spec已可派发。

主仓已与GitHub同步后重新打开原URL，来源仍v6.0.2。768×1000的搜索默认框架、输入/按钮样式及30条链接保存于`v602-tablet-search-shell-resumed.json`；它仅保存外层，不冒充630节点完整默认态。平板搜索采用铺满视口的弹窗，自动聚焦`main-search-bar-modal`。同名入口有抽屉离屏与页头两份，明确定位`#ph-app-header`内可见输入，避免strict mode歧义。

无结果查询`zzzznonexistentcompany987654`的全部51个节点、父索引、属性、矩形、计算样式和SVG保存于`v602-tablet-search-no-results-resumed.json`；来源截图为同命名空间`source-tablet-search-no-results-resumed.jpg`，已查看。Escape关闭后搜索输入不存在、可见dialog为空、公司标题保留，保存`v602-tablet-search-escape-closed-resumed.json`。恢复临时视口后继续后续状态采样。此批没有产品代码变更，不重复构建或阶段审查。

旧60e6316以后来源文件在主仓提交；下文“未push”和旧工作区只指当时历史。卡片深层、hover、Tab/Enter、关闭按钮/点击外部、动画与导航等缺项保持，完整规格就绪后再派发builder。

## 已取得的增量

来源当前为 v6.0.2。桌面 1440×1000 点击页头搜索成功打开独立搜索弹窗，自动聚焦 `main-search-bar-modal`；默认 All 分类有30个结果。不是下拉框，也不是网站不可访问。

- 默认弹窗完整630个节点，分为 `v602-desktop-search-empty-part-{000,100,200,300,400,500,600}.json.gz`；每组最多100节点。已验证连续index、合法parent、相同视口和空query，无缺口。节点保留源文本、CSS、矩形、SVG及相关属性。
- 框架另存 `v602-desktop-search-empty-shell.json.gz`，便于小组件检查，不替代结果列表。
- HOOD查询真实匹配Robinhood及相关公司/ETF/投资者；完整文案/链接在`v602-desktop-search-hood-content.json.gz`，前100节点和框架另存。**HOOD全部节点CSS尚未归档，不能当完整搜索规格。**
- 无匹配查询`zzzznonexistentcompany987654`显示`No results found...`，48个节点完整保存；桌面和手机来源JPEG均已查看。
- 手机清空输入恢复30条默认结果，`v602-mobile-search-cleared.json.gz`。
- 手机Companies、ETFs & Funds、Investors各10条；三个档案包含全部结果文案、href、外层样式及每个分类的选中/非选中tab样式。卡片深层样式仍待补。
- 投资者分类ArrowDown把`data-active=true`及背景`rgb(28,28,33)`移到第二条；ArrowUp恢复第一条。原HOOD ArrowDown前100节点未见实质变化，单独保留，不泛化为所有分类已验收。
- Escape关闭搜索，`main-search-bar-modal`消失。`v602-mobile-search-escape-closed.json.gz`中的`dialog=true`是另一个保留在DOM、display:none/零矩形的公司弹窗，不代表搜索仍打开。最终`v602-search-final-closed-restored.json.gz`直接确认搜索输入不存在、可见dialog为空、公司标题仍在、菜单关闭。
- 临时viewport override已reset，最终默认视口807×822；来源tab8留作后续工作，未改账户设置或发起交易。

## 首个规格与实现

`components/SearchGuidance.spec.md`完整限定弹窗底部静态提示及分隔线，独立于弹窗输入、类别、结果和开关状态。全文、全部计算CSS、无媒体资产、指针前后和1440/768/390三宽度已采。

- 桌面/平板单行，手机自然三行；无组件断点或固定宽高。
- 指针点击静态span后，五个元素的全部CSS和矩形完全一致；没有导航、按钮或可聚焦控件。
- 前端89db998先提交来源及规格。按cloner skill在隔离worktree `D:/桌面/Trade/.scratch/fiscal-search-guidance`派发builder，f5f7121实现SearchGuidance.tsx及同名CSS Module，已快进合并。
- Builder类型检查通过；合并后`npm run check`（lint、typecheck、production build）全部通过，OUTPUT_PLAN原10个page路由保留。
- 原R1 code-review两轴只定向复核89db998...f5f7121新增组件：Standards0、Spec0；没有重复整阶段审查。
- 组件尚未导入路由；构建证明类型/现有路由安全，**不证明该未接入组件或字体loader已经完成运行渲染、整页视觉QA或门户接入**。

## 超时边界与有效操作方式

1. 单次源页面读取/locator动作常耗约21秒，两次顺序操作约42秒。按45秒工具预算安排，控制每次最多两个这样的动作；截图单独调用，不与读取混装。
2. 搜索DOM输出超过约20万字符时会被截断。先小范围采样，结果按100节点分组；每组JSON解析成功后保存，合并时核验index/parent/总数。不能保存截断字符串再声明完整。
3. 本轮把读取与慢截图放一起曾再次触发超时；读取文件已经保存，截图未完成时改为独立`screenshot`成功。分片循环一次跑完也超过整次工具预算，改为每次独立调用。
4. 重置后恢复同一个IAB浏览器2和来源tab8；可通过已公开的Browser.tabs.get绑定，避免不必要的整页原生AX读取。不重复导航现有URL。
5. 使用官方CUA/Playwright只读DOM与公开locator操作；未注入事件/改DOM、抓应用内部状态、绕过验证或使用shell浏览器控制。
6. 原来的403/429资产失败仍单列，未机械重刷；公司logo等缺失仍未解决。

## 继续开发顺序及缺项

搜索剩余：各分类深层卡片、输入hover/focus/clear控件、结果hover、Tab/Enter选择/导航、点击外部关闭、桌面及平板完整弹窗布局/动画；公共状态和受限状态分别记录。导航剩余：hover、键盘、响应式子菜单、帮助、Updates。公司页签、内部scroll sweep及图表多状态仍待。

仅SearchGuidance通过小组件派发条件。搜索框架/导航不能借该组件跳过skill的 **“For stateful components: every state's content and styles are captured”** 门槛（`.agents/skills/clone-website/SKILL.md`）。继续逐个采样→完整spec→隔离builder→合并构建；全部组件就绪后来源pathname装配及三尺寸全状态对照，再映射自有门户/证券/研究契约并接/app。当前仍P10/R1，R2未启动。

所有提交信息中文；未push、部署或改后端/真实.env/模型与worker开关。截图是来源证据，不是产品完成截图。原有dirty文档及.test-output保留。
