# CompanyAnalystSources Specification

2026-10-09，R1/FE-03/QA-01；仅开发公开默认三行，完整展开待来源资格，不改研究工作台。

## 输出与来源
- Target: src/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyAnalystSources.tsx
- Fixture: src/app/labs/r1-company-data-status/analyst-sources-fixture.ts
- Lab: /labs/r1-company-data-status，在CompanyAnalysisModel之后；不接自有/app。
- 既有有效基准overview-{desktop,tablet,mobile}-bounded.json.gz；本次定向提取CompanyAnalystSources.source-{desktop,tablet,mobile}.json.gz各18节点，保留原ID、父节点、文字、32项布局样式。
- 截图：overview-desktop-full-calibrated.jpg、overview-mobile-full-calibrated.jpg；区域坐标以各尺寸归档节点的rect为准，不以估算位置充当实测，也不编辑图片伪造新截图。
- 前轮analyst-expand-signup-gate.dom.txt确认点击Show 85 more analysts只触发第三方注册提示，仍是三行；本轮来源读取超时，不虚称重新采到展开。

## DOM与内容
- Fragment：h3、p、div overflow容器、table；容器中不制造展开按钮。
- h3: Analyst Sources
- p: Apple Inc. is covered by 88 analysts. 40 of those analysts submitted the estimates of revenue or earnings used as inputs to our report. Analysts submissions are updated throughout the day.
- table / thead / tr / th scope=col：Analyst、Institution；tbody三行，两格。
- Amman Saeed / Accountability Research Corporation
- Warren Lau / Aletheia Analyst Network Limited
- Richard Kramer / Arete Research Services LLP
- 人名和机构名是来源标识，两种语言均保持；不制作平台自有分析师或当前覆盖统计。

## 精确样式
- 使用已存在BureauSans变量与作用域section背景；组件不添加section/card/global CSS。
- h3复用companySourceHeadingClassName：margin32px 0 16px；<1024为18/27/500，>=1024为20/30/500，white。
- p复用companySourceParagraphClassName：margin0 0 16；14/23.8/400→16/27.2/400；white70%。
- div：padding-top16px，overflow-x:auto，role=region aria-label=heading tabIndex=0；native表格，不设固定列宽或min-width。
- table：width100%，table-layout:auto，border-collapse:collapse，1px实线rgba(238,236,226,.1)。字体由thead/tbody设13/19.5→14/21（1024断点），white，tbody400。
- thead背景#1a1a1a，th700，所有格8px 16px；第一列左对齐，第二列右对齐；默认vertical-align继承（middle），不改为top。
- tbody各tr同色1px border，包括末行，格无额外border；不添加额外分隔线或列表。
- 来源table宽799.254/696.217/358.377，高152.147/146.152/185.144；移动三行高55.825/36.329/55.825，人名可自然换行，无竖线。
- 已有独立lab外框在768宽约8px差、原生边框量化约1px差继续保留为整页装配事项，不宣称整页像素验收。

## 类型、行为与双语
- 新类型CompanyAnalystSourceRow：id、analyst、institution string；CompanyAnalystSourcesContent：heading、description、columns readonly[string,string]、rows readonly CompanyAnalystSourceRow[]。
- 纯文本props、命名导出、strict TS、无any/网络/账户/状态/第三方登录。
- 组件本体只呈现来源公开默认表格；实验页在其后增加普通文本限制说明，属于明确的验证页适配，不是来源原文：Only the three publicly captured rows are shown. The source website requires sign-in to show the remaining 85 analysts; the expanded list has not been captured.
- 不渲染无效的Show 85 more analysts，不伪造85行、登录流程或完整性。
- 翻译在既有CompanySourcePreview装配层使用统一LanguageProvider；heading/description/columns/限制说明中文，专有姓名和机构保留；切换不重新获取数据。
- 不改/apps工作台布局、正式导航、后端/API权限或源pathname整页ready状态。

## 验证
- lint/typecheck/build，沿用现有前端行为/SSR套件；静态表格不写镜像测试。
- 中英1440/768/390浏览器读图、表格自然换行、三行稳定、语言/数据边界声明、document.scrollWidth无页面溢出。
- 沿用原R1两轴代理只复核新增差异，不重新启动整阶段code-review。
