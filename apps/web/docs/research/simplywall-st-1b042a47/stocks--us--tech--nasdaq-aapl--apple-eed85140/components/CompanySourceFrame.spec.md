# 公司数据来源区域父框架纠偏规格（2026-10-11）

## 有界目标
- 修正`/labs/r1-company-data-status`孤立验证页的背景、报告列位置、语言工具与来源区边界，复用现有四组件。
- 来源是Apple概览报告底部数据来源区域，不是Apple公司页首屏。此次不能宣称完整公司页或全部状态1:1。
- 不修改已有四来源组件的DOM、padding、字体、表格结构；不增加新的证券/研究数据接口。
- 可复用已完整记录的桌面章节目录默认文案/href及公司身份；不虚构目录状态、图表交互、关注/账户、估值按钮或受限分析师列表。

## 核实证据
- `overview-{desktop,tablet,mobile}-bounded.json.gz`：h2及其完整父链；新紧凑摘录`artifacts/CompanySourceFrame.source-20261011.json`。
- 桌面h2/section为3555/3554，company-report ARTICLE476，右列475，flex306，框架SECTION78。
- 平板h2/section3492/3491，ARTICLE335，右列334，框架SECTION103。
- 手机h2/section3303/3302，ARTICLE335，右列334，框架SECTION103。
- 源root背景rgb26/26/26；source section背景rgb33/33/33、radius12px；现lab主背景rgb21/21/21，与来源外背景不同。
- 原data区以前有完整报告和View Valuation：桌面section文档y5456.688，平板5166.309，手机6783.050；不造同高空白。
- 原来源h2为Company Analysis and Financial Data Status；现lab额外“Company source component preview”h1与免责声明在其前面，不能当来源标题。

## 来源实测布局
| 视口 | source root宽 | source section x/宽 | source h2内容x/宽 | section内距 |
|---|---:|---:|---:|---:|
|1440×1000|1432.461|428.475 / 863.246|460.471 / 799.254|32|
|768×1000|760.209|0 / 760.209|31.996 / 696.217|32|
|390×843|390.366|0 / 390.366|15.995 / 358.377|16|
- 桌面外框max-width1199px、padding水平24px；观测框架宽1198.999，内部flex1151.001。
- 桌面report列max-width75%，实际宽863.246；左侧报告目录占其余25%，这是来源真实列关系。
- flex306的左右直接子列307/475：左列x140.726/宽287.749/max-width25%，右列x428.475/宽863.246/max-width75%；坐标相减gap=0（computed gap:normal，父display:flex）。不得添加24px列gap，24px是外框padding/侧栏内部右padding。
- 平板/手机report列max-width100%，外框padding0；没有当前labs桌面864px居中规则。
- 平板/手机左列332 display:none、矩形0；右列334填满760.209/390.366px。移动边距来自数据section自己的16px/32px，不来自额外外框。
- 当前lab1440的卡片x约288/w864，比来源向左约140px；tablet内容704比来源696.217宽约8px。
- 手机现lab358px内容已接近源358.377；不能为美化另加外padding缩窄表格。
- exact styled-component媒体查询未保存在下载CSS，只有三个实际样本；不能凭1024断点声称中间任意宽度已1:1。

## 可直接实施的最小纠偏
1. main外背景改源#1a1a1a；保留来源font variables和.sws-company-source，不把外围字体重置注入子组件。
2. 把自有h1/语言按钮/静态免责声明改为紧凑开发工具区域，放在来源surface外；source区域第一个标题仍是真实h2。
3. 创建作用域父frame：桌面外框最大1199px、左右24px；report列位于右侧75%，移动/平板使用完整可用宽度且外框padding0。
4. 左列用已采真实公司身份与章节目录上下文，不能填通用导航。完整默认侧栏168节点已存artifact；本次有界呈现采用身份+目录，未实现源雪花/账户控件须明确，不能造替代卡片。
5. 当前原scrollbar隐藏是lab历史适配；先测实际documentWidth，不能用viewport强塞源760.209像素或加8px假边距。
6. 保留native vertical scroll，只有数据表包装容器横向溢出；正确scrollbar/gutter取真实浏览器结果，源手机量化390.366不是声明width390.366。
7. 四组件继续位于同一section内，保留原顺序；额外“仅三行分析师”说明放在来源surface外，避免冒充源正文。
8. 英文用于来源逐项对照，中文仍由既有props adapter翻译；提供现有语言按钮，不从中文截图宣称与英文原站像素相同。
- 第3项若实现采用lg=1024作为现有项目断点，应在实现记录为有界frame适配，待补来源精确media query及临界视口；不是已核实来源声明。

## 可直接使用的真实桌面上下文
- 原侧栏：DIV307(25%列)>DIV308(fixed,top80px)>SECTION309(padding-right24px)>图形DIV310/身份DIV384/目录DIV445。
- 来源fixed面板实测宽297.997px，身份内容273.999px；目录NAV446宽297.997，UL447无margin/padding；LI为relative、list-item、宽266.996。
- 本次只用身份+目录时，其与源图形/账户操作之间的垂直位置不可伪称完整侧栏；可使用sticky top80px作为有界开发适配，必须与来源fixed机制分开说明。
- 身份：P387 `Apple Inc.`，BureauSerif16px/24px/500、white、padding-right10px、margin0；内部链接图标SVG/path原属性在identityNodes388–390。
- P391 `NasdaqGS:AAPL Stock Report`，BureauSans14px/21px/400、white70%、margin/padding0。
- DIV392 padding-top2px；P393 `Market Cap: US$4.9t`，12px/18px/400、white70%；这是2026-10-09静态来源值，不是实时自有数据。
- 身份容器386 padding-bottom12px；各节点额外CSS以artifact为准，不加头像/渐变/来源不存在的卡片边框。
- 目录a:block，BureauSans16px/24px/400，padding4px 0 4px 18px，border0、transparent、margin0；约32px自然行高。
- Company Overview文字white，其余white50%；默认selected伪元素未归档，不猜金色左边条。
- 顺序与精确href（公共前缀`/stocks/us/tech/nasdaq-aapl/apple`）：Company Overview→前缀；Valuation→`/valuation`；Future Growth→`/future`；Past Performance→`/past`；Financial Health→`/health`；Dividend→`/dividend`；Management→`/management`；Ownership→`/ownership`；Other Information→`/information`；Stock Community→`/stock/nasdaqgs/aapl`。
- href完整字符串在artifact.navLinks，不能把它们改为同页锚点或虚构已实现本地pathname；如保留跳转需明确来源链接域`https://simplywall.st`，不让Next自动落到本地404。
- 目录默认10条节点完整；hover/focus/active/切页尚无全状态采样，本次只能声明这些默认内容和样式已还原。

## 应保留的精确子区域样式
- h2 BureauSerif24px/32px/500、白字、margin0；手机真实换成两行，不能另加展示页大标题替代。
- section内距mobile16、>=768为32；第一张更新时间表padding-top32。
- 数据来源/模型/分析师小标题18/27/500，>=1024为20/30；正文14/23.8，>=1024为16/27.2，BureauSans。
- 表格保留13/19.5，>=1024为14/21；header#1a1a1a，卡片#212121，链接#fdcb68；详见既有组件spec。
- 不给这些子组件单独增加卡片、阴影、间距或圆角，不把表格转成卡片。

## 验收和不能宣称的部分
- 实际三尺寸记录section/h2/table的x/width、字体、内距、换行和overflow；比较scope内的来源区域截图，不将开发工具算来源DOM。
- 来源有边框像素量化，保持1px声明；现本地高度差约1px与平板约8px框架差均有旧validation记录，修正后重新测量再报告。
- 来源完整报告、完整桌面侧栏/窄屏章节导航、公司header、上下文图表、估值按钮状态和页脚尚未装配验证；目录默认节点已有，但交互全状态仍待。
- View Valuation只存静态DOM/样式，没有行为全状态证据；不新增会误导的假按钮。
- 分析师剩余85条由来源注册/登录门槛保护，未采数据不能造列表或假展开。
- 本轮有界父布局审计不替代实时来源全状态采样，也不重新调用阶段code-review。
