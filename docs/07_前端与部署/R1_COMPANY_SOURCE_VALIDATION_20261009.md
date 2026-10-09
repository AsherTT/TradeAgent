# R1 公司来源基准与更新时间表验证

2026-10-09，Asia/Shanghai。关联正式开发计划FE-02、FE-03、QA-01。按同日增量顺序记录公司来源采样、静态组件与双语验证，R1/P10尚未完成。

## 当前结果

继续在D:/桌面/ai-website-cloner-template开发；主仓后端和apps/web未改。前端013cc7a建立公司独立来源基准/类型/作用域，1aceffc合入更新时间表，1d99091修正验证页窄屏外侧留白造成的额外换行；中文提交，未push或部署。

来源https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple本轮公开默认页面可读，没有遇到机器人验证。实测1440/768/390宽度分别保存3967/3936/3747个元素及父节点关系、文字、属性、矩形和32项布局样式；不称全部计算样式。桌面/移动全页截图分别1440×8067、390×11010，已读图确认正文末尾和页脚；平板全页截图仍缺。

来源页面观察到的两份CSS仅作公开静态素材下载，保存原始与存储哈希及末尾空白规范化记录；没有HTTP抓取HTML或第三方业务API。复用已有Bureau字体，只复制3个公开图片素材，173个inline SVG保存为库存；统计/广告/脚本不进入产品。

## 组件与三尺寸

先写CompanyDataStatusTable.spec.md和共享基础，再通过小工作树实现。组件仅接文本props，原生四行两列表格，不读网络、账户或解析来源时间。独立/labs/r1-company-data-status明确为来源静态样本；未接到自有/app或创建完整Apple来源路由。

最终本地1440/768/390实测无横向页面溢出；h2为24/32/500，格内8×16，数据格1024以下13/19.5、以上14/21，组件内距768以下16、以上32；手机表头和记录恢复来源换行。首次额外外侧留白已修正、重建并刷新复验。原生边框量化导致表高约1px差；平板独立容器与来源整页外框仍有约8px宽差，保留为完整页装配验收项，不宣称像素逐点/整页验收通过。

工程最终lint/typecheck/production build通过；已有六份前端检查启用产品及参考SSR，31 passed、0 failed、0 skipped。后端未修改，未重复474项后端检查。

## 原R1流程新增差异复核

沿用既有code-review两轴代理，仅复核前端17d6599...1aceffc新增组件、types、作用域CSS和实验页，不重新调用整阶段审查。

| 轴线 | 结果 |
| --- | --- |
| Standards | 0项；符合严格TS、命名导出、Tailwind、移动优先，作用域不影响首页 |
| Spec | 0项；结构、文字props、静态交互和来源样本声明符合spec，完整pageBuildersReady仍false |

验证页外框纠偏由主代理三尺寸对照完成，不改变组件契约。审查结论与来源全状态/整页验收分开。

## 剩余问题与证据

公开See All Risk Checks可打开和关闭，保存14条检查的DOM/分块样式及1440×999截图；弹窗内部滚动/键盘/窄屏仍待补。来源检查不代表TradeAgent风险分析结果。

公司页随后出现注册/登录提示，关闭后可读公开概览；点击More details后的状态再出现提示，About文本展开并显示Show less。URL元数据仍为主概览，滚动/导航位置读取超时，不能登记锚点跳转已验证。门户Analysis仍被“Sign up to continue”限制；未采到其正文。两者均未遇到机器人验证，没有操作第三方注册、登录或接受条款。

公司默认三宽度采样解决了“完全没有有效公司样本”的旧阻塞；整页仍缺平板截图、滚动/hover/图表/展开/菜单/异常状态、所有章节spec/实现、完整源pathname及自有对象适配后对照。门户来源尺寸和其他页签仍缺。当前P10→R1→来源采样与独立组件实现；R2尚未启动。

前端证据根：docs/research/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140；详细三尺寸数据与截图索引见components/CompanyDataStatusTable.validation.md。门户限制在portfolio--demo-128b5e04/README.md记录。正式待办以DEVELOPMENT_PLAN.md为准。

## 同日继续：数据来源区域与开发服务

沿用cloner项目，f58d910先保存CompanyDataSources.spec及三宽度样式、桌面图和类型；小工作树实现合入f01f37a，d78757a修正验证页系统纵向滚动条挤占手机15px宽度的问题，49cfc92保存证据。增加四列六行数据来源、原生列表、12条精确公开href、脚注及TTM说明；静态fixture仅在原lab，与更新时间表共用section，不接自有/app或声明真实金融数据。

本地1440/768/390内容宽800/704/358；手机表格429.4，只在自身语义region横向滚动，document.scrollWidth均等于视口。实际键盘ArrowRight令scrollLeft由0变4、随后8；provider焦点underline/gold/无transition与来源一致。验证页根滚动条隐藏规则仅当存在专用class时适用，注册页实测该class不存在且scrollbarWidth=auto，其他路由不受影响。框架差异、约0.5～1.2px表高量化和约8px平板外框差保留为整页验收项。

lint/typecheck/build通过；31项已有前端行为/SSR检查全部通过，无跳过。原R1 code-review两轴只定向复核0940aee...f01f37a新增，Standards0/Spec0，没有再调用整阶段审查。后续验证页外框修正由主代理三尺寸定位及复验；静态实现没有新增镜像测试。后端未改，未重跑474项普通后端测试。

平板全页导出768×12737、DOM高12743，但读图发现注册/登录提示覆盖，归档为overview-tablet-full-signup-gate-diagnostic.jpg；不登记默认平板全页验收完成。本轮仍无机器人验证，没有操作第三方登录/注册/条款。详细证据见前端components/CompanyDataSources.validation.md和三个宽度图；公司完整主概览及门户全状态仍待。

按用户要求启动Docker Desktop与已有postgres、redis，并重建/启动api镜像，包含当前R1代码。数据库和缓存healthy，api的127.0.0.1:8000/health返回200；容器内数据库SELECT 1成功，Redis PING返回PONG，schema现为0016_account_research=head，无需迁移。前端127.0.0.1:3107/register返回200；无账户cookie的BFF auth/me与portal正确返回401。worker和beat保持停止，模型开关实测False；未修改.env、删除卷、创建账户或发起研究。

当前为P10→R1→FE-03公司来源分块实现/QA-01验证，已完成两个静态区域。下一项补Analysis Model与分析师来源说明，并继续完整交互采样、各章节装配和自有契约接入后的对照；R1尚未完成，R2尚未启动。

## 同日继续：中英语言入口与分析说明

用户要求所有当前及后续页面提供中英按钮。继续使用cloner工程，b66fc9a先建立CompanyAnalysisModel.spec和BilingualCompanyPreview.spec、三宽度定向样式、实时outerHTML与共享类型/样式；d9147e1合入小工作树静态模型组件，61ecf49接入公司实验页的中英翻译、语言入口、功能联调提示与标题、输入保留及公开双语SSR检查。提交中文，无push/部署；不迁入apps/web。

公司实验页现有更新时间表、数据来源、分析模型三个组件，含独立行业指标说明，共四个静态区域。首页/来源参考、账户、门户、公司、研究与报告保留已有统一语言入口；新实验页按钮复用同一个LanguageProvider。语言切换更新文本、html.lang、文档标题和偏好cookie；金融样本日期、UTC口径、公开href及数据权限保持原契约。英文保留来源基准，中文是明确适配，不把来源样本接为自有产品数据。

来源模型区域799×276截图已读图，三宽度9节点定向档及桌面实时outerHTML已归档。英文团队说明原本缺词且没有team链接；前三条不同标签均指向同一support分类地址，行业说明原文使用section，按来源保留。中文仅描述模型设计与构建，不推测团队。四条模型链接均新标签页、noopener noreferrer nofollow，实际键盘焦点underline/gold通过。

中英各1440/768/390六张全页图均读图，document.scrollWidth始终等于视口。表容器800/704/358.4，中文表格同宽，英文手机表429.4，仅自身region横向滚动；ArrowRight后scrollLeft=40且聚焦。英文移动标题与语言按钮分行，不遮挡；激活按钮金底黑字。英文桌面模型区域800×276，与来源高度及换行一致；已有约1px表高量化、平板约8px验证外框差仍保留为完整页装配验收项。

真实浏览器英文刷新、跨页到门户/功能联调页、中文返回及刷新通过。浏览器已有登录状态使/register跳转/app，仅记为门户语言入口验证，未退出会话或创建账户。注册页无会话中英SSR、真实AuthForm切换前后输入保留由独立测试覆盖。最终恢复中文和正常viewport。

工程lint/typecheck/production build通过，七份前端检查启用产品、参考、双语SSR，34 passed、0 failed、0 skipped；新增测试使用真实语言上下文，不提交注册或业务请求。原R1 code-review两轴仅定向复核49cfc92...61ecf49：Standards0/Spec0，没有重新启动整阶段审查。后端未改，未重复后端474项检查。

点击Show 85 more analysts仍保持默认三行并出现“continue analysing AAPL”注册提示，正文称88位分析师、40位提交估计；analyst-expand-signup-gate.dom.txt归档此状态，未实现虚假85行或展开按钮。不是机器人验证，没有第三方登录、注册或条款操作。Docker postgres/redis仍healthy，api继续运行，模型/worker未启用。

详细证据由前端bf19db8保存，见components/CompanyBilingual.validation.md、CompanyBilingual.local-validation.json、CompanyBilingual.interaction-validation.json及六张company-bilingual图。当前仍P10→R1→FE-03分块实现/QA-01；下一步补公开公司章节、完整交互规格/装配与自有接入后对照，受限分析师状态待补。完整来源公司页、门户全状态及R1未完成，R2未启动。
