# 搜索父装配与公司来源布局纠偏验收 — 2026-10-11

用户指出旧lab廉价、缺少来源整体感。本轮按apps/web canonical clone-website工作流重新采集公开页面，先冻结字体/类型和小spec，再复用隔离builder构建行、frame、输入分类、公司frame，主仓装配后实际浏览器对照。原独立模板只作只读历史，唯一维护根为apps/web。

来源：https://fiscal.ai/company/NASDAQ_HOOD/；公司来源区域为https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple。21个真实logo与4面SVG旗帜保存原字节，image-validation全数成功。历史BOVV11已按最新来源改PIBB11；不伪造源会话的Recent历史。

## 搜索父区域
1440×1000弹窗1000×843.6，x220/y78.2，输入966×42；768×1000与390×1000 fresh弹窗全屏。三尺寸投资者10行的文案、x/y/width/height及input/modal（已有来源项）相对0.1px阈值均0差异，见SEARCH_PARENT_GEOMETRY_COMPARISON_20261011.json。此结论仅几何/文案范围，不代表全部CSS与交互状态或整站1:1。

平板首次发现字号/头像误用了桌面值，已改14/20.3、gap6、头像20；桌面16/24.8、gap12、头像28。分隔线由误读浅色改来源rgb64/64/79；/键帽改实际12/18.6 weight700/p3x5。全部30条默认参考结果原序、素材成功加载，无横向溢出；隐藏内部native gutter保持默认行宽966，自定义来源scroll thumb全状态仍待。

已实际验证Companies+AAPL得到Apple一条；Enter确认参考选择并关闭，焦点回到重新打开；关闭→中文→重开保留AAPL与公司分类；不存在样本得到中文无结果；Escape关闭。空query Tab保持input并清active；其余页导航47条未装配。上下键选择为本地样本预览，非源全球查询服务。无新增后端接口或账户数据写入。

## 公司来源父区域
改来源背景#1a1a1a、桌面1199外框/24左右padding/25%与75% gap0分栏；真实Apple身份/10条来源目录；窄屏隐藏侧栏全宽。原四组件保持同一source section，说明移到surface之外。

本地1440：section宽863.25/h2内容799.25，与来源863.246/799.254接近；x427.050对来源428.475差1.425px。平板本地section757.600对来源760.209差2.609px（浏览器滚动槽适配差）；手机390.400/内容358.400对来源390.366/358.377。三尺寸无document横向溢出，table本身保留原横滚。完整记录company-report-frame-local-20261011.json。侧栏sticky、1024断点及滚动槽均明确为有界适配，未核实为原站完整机制。

## 检查和边界
lint/严格类型/生产build通过；PRODUCT_PREVIEW_URL指向真实主仓3107时现有36项前端测试全部通过（0跳过）。原R1已调用的code-review Standards/Spec两轴，仅bb8f9c0…0ff33af增量复核，各0项；后续小型滚动槽/翻译适配由主代理定向检查，不重新调用整个阶段。Docker API/PG/Redis保持运行；模型/worker/beat仍关闭，无新数据库迁移。

当前仍P10/R1，R2未启动。完整Fiscal导航/公司整页、47页模式、Listings展开、全球搜索、自定义滚动条拖动及全状态、来源断点临界、Simply完整报告/图表/受限分析师均待。/app仍功能骨架，不把labs改造等同正式工作台复刻。
