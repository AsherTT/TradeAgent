# 公司双语与分析说明增量验证

2026-10-09，Asia/Shanghai。前端b66fc9a、d9147e1、61ecf49；沿用cloner项目。当前P10/R1/FE-03分块实现与QA-01，完整公司页未完成。

## 范围与来源

CompanyAnalysisModel.spec.md先于实现，三个宽度定向样式来自有效overview分块基准，每份9节点；CompanyAnalysisModel.source-fresh.json补充桌面实时outerHTML。analysis-model-source-desktop.jpg为799×276区域，已读图。新静态组件展示Analysis Model and Snowflake及Industry and Sector Metrics，四条原生公开链接保留target=_blank和noopener noreferrer nofollow；不联网、不接账户或金融数据。

英文来源的团队说明缺词及三空格、前三条不同链接标签指向同一support分类URL、industry段落section用词均保留。中文提供语义适配，团队说明仅写模型设计与构建，没有杜撰团队或链接。来源Data Sources既有链接契约维持原规格，不因新模型链接不同而扩大改动。

Analyst Sources默认三行可读；Show 85 more analysts触发注册提示，三行及按钮不变。正文提示88位分析师、40位提交估计；未采到其余85行，不建立虚假完整列表。证据analyst-expand-signup-gate.dom.txt。无CAPTCHA、第三方登录/注册/条款操作。

## 统一中英切换

按照BilingualCompanyPreview.spec.md复用既有LanguageProvider/LanguageSwitcher。首页、来源参考页、账户、门户、公司、研究与报告已有统一入口；补公司验证页缺失入口，翻译其静态样本、声明、模型和行业说明，补功能联调页提示及两实验页标题。当前及后续页面继续共用该语言机制，不新增互相独立的语言状态。

日期、UTC口径、来源href、provider品牌及SEC正式名称不因翻译变化。英文是来源对照基准，中文是用户授权的产品适配。验证页仍声明静态样本，不接自有/app真实对象。

真实浏览器验证英文刷新保留、跨页到门户及功能联调页、中文切换后返回公司验证页并刷新保留。已有登录状态令/register跳转/app；只检查语言入口，不创建账户或退出已有会话。无会话注册页由HTTP SSR测试覆盖，注册输入保留由真实AuthForm/LanguageProvider的DOM测试覆盖。

## 三尺寸与交互

六张company-bilingual-{zh,en}-{desktop,tablet,mobile}.jpg均已读图，完整页面包含标题/按钮、两个表格及模型/行业说明。CompanyBilingual.local-validation.json保存1440/768/390布局、文本和样式，interaction-validation.json保存刷新/跨页/键盘测量。

| 宽度 | document.scrollWidth | 表容器宽 | 中文表宽 | 英文表宽 |
| --- | --- | --- | --- | --- |
| 1440 | 1440 | 800 | 800 | 800 |
| 768 | 768 | 704 | 704 | 704 |
| 390 | 390 | 358.4 | 358.4 | 429.4 |

英文移动表只在自身语义region横向滚动，实际ArrowRight后scrollLeft=40且region获得焦点。英文长标题在移动端换行，语言按钮位于下一行且可见；中文保持同一行。激活按钮黑字/金底，非激活白字，未发生页面横向溢出或遮挡。

英文桌面模型区域800×276，与来源799.254×275.976的高度/换行一致；宽差归于已有独立验证外框。模型链接键盘焦点underline，颜色rgb(253,203,104)，target/rel保留。临时viewport已恢复，最终语言中文。约1px表格边框量化和平板约8px外框差仍是整页装配验收项；不宣称整页像素验收完成。

## 工程与审查

npm run check（lint/typecheck/production build）通过。七份测试启用产品、参考及双语公开SSR，34 passed、0 failed、0 skipped。新增测试使用实际语言上下文，覆盖中文→英文→中文、cookie/html.lang/标题、表单输入保留，以及四条公开路由双语SSR；没有提交注册或业务请求。后端未改，不重复后端474项检查。

沿用原R1 code-review两轴代理，仅复核49cfc92...61ecf49新增差异：Standards 0、Spec 0。没有再次启动整阶段审查。来源全状态、完整pathname、所有章节实现及自有接入后对照仍待；R2尚未开始。
