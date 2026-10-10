# Fiscal 搜索固定预览与主应用组合验收

2026-10-10，P10/R1、FE-02/QA-01。依据用户“继续开发、打开Docker、说明当前R1手动验证/查看效果”。

## 实现与边界

9473a79先保存新开发验证容器完整小规格与输出计划，再由原clone-website隔离builder复用主仓工作树实现；f2b0f8f快进合并。新增 `/labs/r1-fiscal-search`，真实导入 SearchClearButton、SearchEmptyMessage、SearchGuidance 和既有 next/font/local 字体，配自有双语说明、输入/计数/重置及内部导航。原三个来源控件未改；无新增来源资产。

源码唯一入口为 TradeAgent/apps/web。新页面与原十个page同时构建，共十一个page；不替换既有首页或正式/app。来源 https://fiscal.ai/company/NASDAQ_HOOD/ 的完整源pathname仍未装配；本页是子组件开发验证，不是公司Overview、搜索父层或结果列表的一比一复刻。输入不查证券、静态提示不冒充查询结果。

## 主应用样式组合

实际主应用浏览器发现：flex父层将按钮来源inline-block计算为block；Tailwind preflight还改变span未显示的outline-color。2db6a9c修复验证容器：普通行内居中与只限定样本span的currentColor，避免修改来源子组件、Simply全局基础和现有路由。

验证通过真实Next客户端和真实字体loader，验证域为来源已验收子组件与主应用全局CSS组合。与前次已逐项对照来源的独立本地记录复核；字体family别名单列，保持同一来源Jakarta400/600文件。绝对坐标由开发容器决定，不宣称完整弹窗位置一致。

| 语言 / 视口 | 验证项 | 结果 |
| --- | --- | --- |
| 中文1440×1000、768×1000、390×1000 | 各246项记录样式与宽/高 | 各0差异、字体loaded、无横向溢出 |
| 英文同三视口 | 各246项 | 各0差异、字体loaded、无横向溢出 |
| hover、hover+keyboard focus、非hover keyboard focus、focus+pressed | 各138项按钮/两span记录样式与宽/高 | 同前置条件下各0差异 |

按钮三尺寸均100×30，inner78.4×28.4，label73.5875×28.4。无结果段落为966/657.2/317.375宽×56.8高；Guidance桌面/平板37.6高，手机71.2高，文字自然三行。

第一次原生mouse-pressed从其他控件转入，focus-visible=false，相比历史已keyboard-focus的pressed记录，outline及offset有2项前置状态差别；保留原样本和差异，不作为实现错误。之后先Tab聚焦再按压，focus-visible=true，复核同状态0差异。原生非keyboard焦点不强制显示ring。hover过渡即时opacity也不冒充稳定值。

默认/交互原始记录、比较JSON与三尺寸本地完整截图归档在当前research/screenshots namespace；未修改/覆盖来源证据。

## 实际操作与语言

原生鼠标release、Enter、Space分别从重置0开始：query置空、按钮移除、清空次数为1；每次仅一次回调。Tab从输入准确到按钮；hover opacity0.7，focus-visible ring1.6px rgb94/94/116与offset1.6，pressed translateY1px。

清空后计数1，再输入自定义文字切EN：query和计数仍保留，外围标题/说明/导航/步骤切为英文，来源仍英文。刷新后document.lang/title保持英文，示例query/计数回初始值；恢复原中文偏好。没有修改已有账户数据、关注或研究任务。

## 工程检查

Builder typecheck/diff检查通过。主仓合并完整check通过；实际样式纠偏后再次lint/typecheck/production build全部通过，原路由保持。现有普通前端测试35 passed、1 skipped、0失败；未配置PRODUCT_PREVIEW_URL的首页SSR测试为跳过，并非本次全首页验收。未改后端代码，未重复后端全套测试。

浏览器无runtime error；开发期间标题字典接入触发一次Next Fast Refresh full-reload提示，属于热更新行为，实际语言切换/刷新验收仍通过。

## Standards

沿用原R1 code-review，仅9473a79...f2b0f8f及追加f2b0f8f...2db6a9c新差异定向复核，未重新调用阶段skill。0项可行动发现：命名导出、Tailwind、原生回调、语言状态和开发容器范围符合AGENTS/spec；默认导出仅Next路由契约；作用域样式纠偏不改变全局基础。未发现可行动Fowler异味。

## Spec

0项可行动发现：路由/三叶子复用、初始状态/条件显示/重置/计数、双语保留、静态样本边界、导航和三宽度均符合规格；追加纠偏与实测依据一致，无完整父层装配或新增请求。两个轴线仅复核本轮差异。

## 本地运行与后续

Docker Desktop、PostgreSQL/Redis健康，当前源码API镜像重建并启动，health status=ok。数据库只读确认0016_account_research与仓库head一致；首次旧migrate镜像找不到该revision，构建后仅重建为停止状态，API以--no-deps恢复。未运行新迁移、未改.env，account_research_models_enabled=false，worker/beat停止。既有等待执行任务保留。

当前主仓3107开发服务保留供用户手动验收。浏览器临时尺寸结束后reset，预览作为可查看结果保留。完整搜索、投资者分类/卡片/路由、导航/图表、来源公司页与正式/app Fiscal布局仍待；P10/R1继续，R2未启动。手动入口和恢复方法见根文档 R1_MANUAL_VALIDATION_20261010.md。
