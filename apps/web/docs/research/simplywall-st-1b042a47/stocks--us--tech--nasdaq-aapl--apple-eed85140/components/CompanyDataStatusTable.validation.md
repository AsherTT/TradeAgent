# 更新时间表增量验证

2026-10-09，Asia/Shanghai。只验收本静态组件，不验收完整公司页。

## 实现与纠偏

前端013cc7a保存来源基准、spec、字体/颜色作用域与类型；1aceffc合入独立组件和/labs/r1-company-data-status。
首次本地手机截图发现验证页额外外侧padding使表头和End of Day Share Price换行；移除组件外侧留白，提示文字单独留白，重新构建、刷新、测量和读图。
组件保持四行文字props、原生table、h2、列标题scope，不读账户或网络。实验页明确为来源静态样本。

## 最终三尺寸对照

来源数据见overview-{desktop,tablet,mobile}-bounded.json.gz；本地数据见同目录CompanyDataStatusTable.local-{desktop,tablet,mobile}.json。
本地三个实际宽度分别1440、768、390，scrollWidth均等于viewport宽度。来源移动实际高度843，本地844；不把它们标成相同高度。

| 尺寸 | 来源标题/表宽 | 本地标题/表宽 | 来源标题/表高 | 本地标题/表高 |
| --- | --- | --- | --- | --- |
| 1440 | 799.254 | 800 | 32.003 / 189.974 | 32 / 189 |
| 768 | 696.217 | 704 | 32.003 / 182.480 | 32 / 181.5 |
| 390 | 358.377 | 358.4 | 64.005 / 182.480 | 64 / 181.5 |

字号、行高、字重、颜色和组件内距按spec：h2为24/32/500；数据格为13/19.5，1024起14/21；内距16，768起32；格内8×16。字体复用原来源本地字体，计算family名称因next/font重命名不同。
移动标题两行，表头和四条记录恢复来源换行方式。本地截图已读取检查。原生边框计算量化来源0.837696px、本地0.8px，导致表高约1px差；保留源码1px声明。
平板验证页独立容器宽度与来源整页存在约8px差，来源整页滚动条/外框尚未装配；该差异保留为整页对照待办，不能宣称像素逐点或整页验收通过。

最终截图位于该公司design-references目录data-status-local-{desktop,tablet,mobile}.jpg，实际图片分别1440×600、768×600、390×844；来源表格桌面裁剪为data-status-table-desktop.jpg。所有jpg实际为JPEG。

## 工程与审查

最终npm run check：lint、严格类型和生产构建通过，验证路由出现在构建清单。
同次已有六份前端测试启用产品/参考SSR：31 passed、0 failed、0 skipped。后端未变，不重复后端全量测试。
沿用R1既有code-review两轴代理，仅复核17d6599...1aceffc新组件、foundation、types和实验页：Standards 0项，Spec 0项。未重新审查旧R1整阶段。验证页外框纠偏由主代理三尺寸复查完成，不改变组件props/行为。

## 后续边界

完整Apple来源pathname尚未创建；pageBuildersReady=false。Data Sources、分析师展开、图表、章节/全状态、自有公司接入及接入后三尺寸仍待完成。
风险弹窗新增桌面公开DOM、分块样式和1440×999截图；14条检查包含No data，不将来源判断变成TradeAgent判断。弹窗滚动和窄屏尚未验收。
