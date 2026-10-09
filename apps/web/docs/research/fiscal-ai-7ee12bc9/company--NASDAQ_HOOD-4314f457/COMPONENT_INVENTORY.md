# 组件候选与派发门槛

这是拆分清单，不是组件 spec；所有 stateful 候选有未采状态，当前不派发 builder。

| 候选 | 已取得 | 仍缺 |
| --- | --- | --- |
| AppShell / Sidebar | 三尺寸关闭默认、手机展开、扁平计算样式/SVG/文字 | 桌面菜单、手机子菜单、hover/焦点/关闭机制、主题/临界断点 |
| Search / Header | 三尺寸默认、占位文字、注册及 burger 显隐 | 搜索打开/输入/结果/空/关闭、帮助、公开账户限制、hover/键盘 |
| CompanyContext | 默认身份/价格/活动/按钮/tabs | 动作语义、收藏/备注/活动展开、切换、全页签 |
| CompanyOverview | 默认简介/五字段 | Show more 开关、逐元素三尺寸样式、链接状态 |
| CompanyStatistics | 默认DOM所有分组/USD，手机默认图只有部分字段并有 Show More | 手机 Show More 开/关、控件状态、逐元素三尺寸样式及章节图 |
| BullsAndBears / Happening | 默认DOM文字、整体图；手机 Bulls/Bears 有截断及 Show More | 手机 Show More 开/关、独立提取/截图、链接状态、时间变化范围 |
| Earnings | 默认季度/Revenue及图 | Annual、EPS、图表 hover/选中、响应式样式 |
| PriceChart | 默认5Y图、工具/日期/周期 | 周期、技术分析、搜索、日期、指标、下载等完整状态，资产和技术选择 |

skill pre-dispatch checklist 明确要求：**“For stateful components: every state's content and styles are captured”**。不把默认 CSS 补成猜测状态，不建看似合格的 `.spec.md`。小组件证据完整后可逐个派发，不必等后端全部完成，但基础构建和完整 spec 必须在先。
