# R1 公共应用壳增量规格 — 2026-10-12

关联FE-02/FE-03/QA-01，方案2范围。前序选定搜索清空已验；Simply现有四组件/五区域的默认、中英、表格横滚和公开链接focus沿用已有有界验收，不重做。不把完整来源报告、章节目录全状态或受限分析师当本次前置；未采状态保留，不借此称R1完成。

## 本轮出口

整个 `/app` 共用来源规格化顶栏/窄栏/抽屉和自有导航；现有账户、目录、本人研究与BFF不变。源码apps/web为唯一维护根，来源公开HOOD仅提供公共外框；其商业公司内容不作为本人门户数据。门户正文、公司、研究、报告及账户逐页重构仍按后续任务。

来源证据与两个小spec在 [Fiscal namespace](../../apps/web/docs/research/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/)，精确字体、80/64框架、1023/1024边界、3尺寸、抽屉开关和slash已采。输出计划复用该site/page namespace，新增shared两个组件；不覆盖原来源路由/素材/全局基础。自有品牌/入口数量/语言/键盘行为分别登记，不以黑背景或通用卡片声明整页复刻。

## 产品接线

- 新增 `src/app/app/layout.tsx` 作为该路径唯一公共壳，加载Fiscal字体变量；各page现有getAccount、redirect、DTO与权限继续自行执行，公共壳不缓存账户或读取第三方。
- `components/workspace/AppShell.tsx` 管理抽屉/焦点/快捷键和共享布局上下文，使用两个已冻结的来源组件；CSS只作用于自己的外框。没有第二语言Provider。
- 导航：Portal/研究门户→/app；Companies/公司→/app/company-search；Research/研究→/app/research；Account/账户→/app#account；品牌→/。英文文案与中文为自有适配；不造未完成的Financials/估值/筛选入口。
- active：/app为Portal，/app/company-search及/app/companies/*为Companies，/app/research及子路径为Research。Account锚点不虚构独立账户页；Workspace既有账户控制区域加id=account，不改logout行为。
- 容器顶部让出64px，>=1024左让出80px。跳过导航链接到workbench-content，可键盘聚焦；正文不中断原表格/读报滚动。
- AccountShell在这个公共壳内只呈现原业务内容和footer，移除重复ProductHeader；/login、/register、首页和lab保留原框架。原正文米白色、组件样式暂时保持，逐页重构时再按各来源spec改变，不利用全局CSS强刷黑色。
- 搜索/候选详情原独立页面适应公共壳内容高度；保留真实SEC请求/目录信息/状态，搜索modal仍覆盖整个viewport且不与drawer同时打开。
- 不新增API、迁移、研究准入或私有对象查询。目录候选仍不能关注/发起研究。

## 状态/行为与明确适配

- drawer默认关闭；burger打开并聚焦close。关闭、Escape恢复burgerfocus；Tab/ShiftTab圈定可见enabled控件。背景header/content inert，body原overflow捕获/恢复。
- Source Escape未关闭且closefocus留在隐藏按钮；产品的以上行为是明确无障碍适配，不声称源交互相同。
- 路由变化立即关闭抽屉，A→B→A不重新恢复；导航close不把focus抢回旧按钮。切语言不改query/form/预算/权限，drawer本身保留状态。
- 临界resize进入>=1024时关闭drawer、恢复overflow，若focus原在drawer则转到公共搜索入口，不能聚焦已隐藏burger。随后回小屏不会自动重开。
- `/` 无修饰、非repeat、非composing时进入真实公司搜索；INPUT/TEXTAREA/SELECT/可编辑祖先、已打开modal时不截获。字段中的斜杠仍可输入。搜索入口同时支持真实Link鼠标/Enter/修饰键语义。
- 标签和aria文案中英；自有共享LanguageSwitcher保持偏好。加载/空/503/401/404继续原页面行为；不会因壳出现而提高数据或模型资格。

## 验收

来源spec→隔离header/sidebar builders→每次merge/build→产品接线。普通测试沿用已确认的实际挂载UI/路由HTTP边界，新增壳测试聚焦路由/字段保护/快捷键、drawer焦点/溢出恢复/resize与语言，不用CSS镜像测试代替浏览器。

中英1440/768/390及1023/1024、短窗口/导航/刷新/返回验证；公共框架64/80和来源子控件相对几何/CSS单独比较。来源帮助/登录、品牌、菜单数量和语言宽度是已知适配；原业务正文尚未重构，不能声称整个/app/P10完成。

每个大R阶段审查一次，本R1仅对本轮新固定diff定向双轴复核并闭环，不重审旧实现。中文commit、正常push；模型/worker/beat/采购/部署继续关闭。
