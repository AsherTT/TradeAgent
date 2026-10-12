# R1 搜索清空装配增量验收 — 2026-10-12

本轮只推进 FE-02 / QA-01 的选定搜索状态。代码固定点 `c89675f87f2cddc04c48d937c7295ec7305d9d66`；R1仍未完成，R2未启动。任务状态只维护在 [正式计划](../01_项目总览/DEVELOPMENT_PLAN.md)，不扩成新阶段或第二份待办表。

## 来源、规格与产品适配

严格使用主仓 [clone-website 工作流](../../apps/web/.agents/skills/clone-website/SKILL.md)。实际打开 Fiscal HOOD 页面，普通 AAPL 查询没有 Clear Search，HOOD pages 有。采集 1440/768/390 实际 innerWidth/innerHeight、按钮及父条 DOM/CSS、截图，再冻结 [小组件规格](../../apps/web/docs/research/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/components/SearchClearBar.spec.md)。

来源父条是 sticky top0 / z-index10 / padding4px0 / rgb(28,28,33)，自然高度38px；子按钮100×30。补采发现按钮 vertical-align:middle，隔离builder局部对齐，保持原按钮CSS。规格提交747ef30，隔离分支codex/fiscal-search-clear的f8b9f20/cc30d4c合并后build通过，再接产品父层c89675f。

**明确适配：** 正式 SEC 搜索非空输入显示清空条，空输入隐藏；中文为“清空搜索”。清空query/分页/键盘选择、结果滚动回顶并focus输入，保持弹窗/语言/权限。来源样本模式保持原实现，未建设47页内部搜索。来源此轮是打开后resize的弹窗，产品窄屏采用现有fresh-open布局；不比较不同模式的整页坐标，也不称完整弹窗或公司页1:1。

## 验证证据

- [来源及本地证据目录](../../apps/web/docs/research/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/)：CLEAR_ASSEMBLY_SOURCE三尺寸、ALIGNMENT补采、LOCAL中英三尺寸、COMPARISON、INTERACTIONS和SCROLL。
- 英文45个局部相对几何值最大差异0.0000152587890625px；156条选定CSS属性比较0差异。Next字体内部名、父条宽度/绝对位置、无时长transition序列化和不可见none-outline宽度列为排除项，不冒称所有CSS或像素一致。
- 中英三尺寸自然bar38px、按钮100×30，无document横向溢出；截图实际查看。中文文字宽度是翻译适配。
- 正式 `/app/company-search` 的真实SEC AAPL结果验证；鼠标/Enter/Space清空后query为空、控件消失、dialog仍开、focus返回输入，无导航。
- 1280×720、真实多结果查询A：滚动720px后bar顶部仍与结果viewport顶部一致；点击清空后scrollTop为0，输入focus，dialog仍开。
- 前端lint/typecheck/build通过，运行中SSR验证启用时完整49项测试通过，0跳过。新增3项真实挂载组件/HTTP边界测试，覆盖翻页后清空和迟到响应、清空后迟到401仍失效、关闭/重开与Tab焦点；首个测试先失败（找不到Clear Search），装配后通过。
- 后端运行代码未变，不重复运行既有497项后端测试；不将其旧结果描述为本轮重跑。

截图入口：[英文桌面](../../apps/web/docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/local-clear-assembly-en-desktop-20261012.png)、[中文桌面](../../apps/web/docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/local-clear-assembly-zh-desktop-20261012.png)、[中文手机](../../apps/web/docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/local-clear-assembly-zh-mobile-20261012.png)、[短窗口滚动](../../apps/web/docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/local-clear-short-window-scrolled-20261012.png)。浏览器临时viewport覆盖已reset。

## 新增固定差异定向审查

沿用R1既有code-review双轴规则，只检查 `ed721a6...c89675f` 新增固定差异；旧会话代理句柄不复用，本会话重新绑定两名定向复核代理，没有重审全R1或启动新的阶段审查。Standards 0项，Spec 0项；无需修复。视觉QA与代码审查分列，不以静态复核推导全产品已验收。

模型/worker/beat仍关闭；没有后端/迁移/目录写入/数据采购/部署。主仓apps/web是唯一维护根，隔离builder只贡献小组件。下一步按正式计划核对选定搜索/Simply剩余状态，再冻结/app应用壳与门户来源规格并逐页接线；完整商业报告与受限分析师仍非R1前置。
