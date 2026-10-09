# Simply 门户来源：初步采样

日期：2026-10-09。来源为既定 https://simplywall.st/portfolio/demo，输出隔离计划见OUTPUT_PLAN.json。完整首页及现有业务路由保持原样；尚未创建来源门户实现或派发构建代理。

首次导航及绑定读取超时，后续实际读到了“Discover the power of the Simply Wall St Portfolio”引导弹窗。点击Explore Demo Portfolio，关闭随后出现的注册提示后取得Holdings默认页面。没有注册来源账户、接受条款、绕过验证或用HTTP抓取页面。

## 实际观察

主导航：Dashboard、Portfolios、Watchlist、Community、Discover、Screener。页面导航：Holdings（当前）、Analysis、Valuations、Dividends、Returns、Updates。Holdings内Value/Performance、Stacked/Combined、All Time、Holding View及排序控件存在；本轮尚未逐一操作，不能确定全部交互机制和其他页签内容。

默认区域包含总额/回报概览、组合净值/成本图、回报分项、Portfolio Snowflake、15条Holdings表格、FAQ及页脚。来源实测组合金额、估值、雪花评分和收益只是原站演示，不能接到自有账户作为真实指标；组合/筛选仍按首版范围延期。AMZN、NVDA等公司链接可见，Apple公司目标尚未取得完整有效样本。

## 可追溯样本与限制

- holdings-observed-754.json.gz：浏览器只读DOM采样1958个元素，属性、直接文字、矩形和完整计算样式；含DOM可见style/link样式库存。标准gzip，保留原始JSON内容，压缩避免大量重复CSS进入Git。
- [首次长截图](../../../design-references/simplywall-st-1b042a47/portfolio--demo-128b5e04/holdings-first-capture.png)：实际取得的截图394×2382，查看后确认右侧内容不完整。
- 请求viewport1440×1000，但来源DOM返回754×523，body/scroll宽754；截图宽394。请求尺寸与真实样本不一致，文件按observed754命名，不能标记为1440基线、手机基线或完整全页。
- 文档化浏览器viewport和CDP诊断接口未恢复可靠尺寸，Page.getLayoutMetrics读取超时。没有转到shell/CDP或抓隐藏应用状态绕过工具限制。相同viewport接口在本地页面的三尺寸测量成功，来源问题的根因仍未确定。

继续先恢复来源尺寸与全页截图、逐分区滚动/时间/hover/click及全部页签/菜单/状态，补1440/768/390、字体媒体库存和组件规格，再确定共享基础并实现。当前buildersReady=false；未观察的状态、交互和章节不能凭记忆或原创卡片补齐。这里仅解除“完全无门户内容样本”的状态，不宣布FE-02/FE-03或R1/P10验收通过。

## 同日后续状态

点击Analysis后，首次DOM仍为Holdings（holdings-after-analysis-before-gate.dom.txt）；后续显示“Sign up to continue. Free forever.”，保存analysis-gate-observed.dom.txt。未取得Analysis正文，不能把点击成功等同页签切换完成。

analysis-signup-gate-diagnostic.jpg虽导出1440×999，采样时门户DOM仍是754×523，请求/实际尺寸没有统一，保留为登录提示诊断图，不作为桌面响应式基准。未操作登录、创建账户或接受条款；提示不是机器人验证。

Apple公开公司概览已另取得实测1440/768/390分块样式、桌面/移动全页截图和首个独立静态组件，见相邻stocks--us--tech--nasdaq-aapl--apple-eed85140目录；这不补齐门户的来源状态或尺寸缺口。
