# 增强 A 纠偏：来源基底优先

用户2026-10-08再次明确：在ai-website-cloner-template里按增强A一比一复刻。上一版通用卡片首页是执行偏差，不能作为批准设计；公司/门户原创骨架也没有获得视觉认可。

## 输出与保留

- app-root: D:/桌面/ai-website-cloner-template。来源 https://simplywall.st/；site-key simplywall-st-1b042a47；page-key root-8a5edab2。
- `/references/simply-wall-st`、原root组件、source-styles.css、fonts、assets、source/computed截图均完整保留。
- `/`用户已要求纠正：以原站Navigation/Hero/Platform/StockSearch/FinalCTA/Footer对应区域的DOM和实测CSS为基底。禁止继续使用通用圆角卡片重排。
- 旧功能首页移到明确的`/labs/function-integration`联调预览，不出现在正式导航；账户/研究/公司接口继续复用，但尚未采样的公司/门户页面不作为视觉交付。
- 新产品适配组件隔离在`src/components/sites/simplywall-st-1b042a47/product-a/`；组件spec在当前components/EnhancedA*.spec.md。截图在原截图命名空间`enhanced-a-20261008/`，不覆盖历史截图。
- 根字体/CSS基底已存在，本轮复用sourceInter/BureauSans/BureauSerif和原断点，不修改原参考CSS。新功能逻辑使用命名导出、strictTS、Tailwind/no inline styles。

## 允许的适配差异

TradeAgent品牌、双语研究文案、自有按钮落点、原站视频替换为已确认的明确演示数据交互。原站第三方评分/评价、全市场规模、组合/分红/筛选/社区营销不属于首版，不挪用为自有能力；完整原站内容仍在参考页。自有demo内容与原站视频画面不同，不能宣称这部分像素完全相同；其占位、外框、阴影、响应式沿用来源。

已确认演示包含门户/财务/报告/证据、期间和引用操作；其他导航采用保留来源布局的可改候选，只调整落点/标签，不宣称最终确认。

## 证据与门槛

2026-10-06的三尺寸computed-full、组件spec和截图是来源基准。2026-10-08原站首页DOM、1440首屏截图及首屏computed样式已再次读取成功；原站390新采样调用超时，因此不声称当日全部尺寸重采样通过。产品双语三尺寸实际DOM宽度/字体已验证无溢出，截图工具的窄屏渲染比例异常，窄屏逐像素截图验收仍待补。继续使用现存有效采样，不猜测未采样公司/Fiscal/Quartr页面。先逐项差异表再请求用户效果确认；恢复原组件不代表已完成全部来源页或R1/P10。

媒体替换适配：四标签/年度/引用复用同一套已验证状态逻辑；source-frame采用来源媒体区域的深色表达，具体演示内部控件/数据为产品能力适配，不把这些自有内容声明为视频逐像素复刻。移动媒体容器补充原991断点的宽度约束，避免由交互内容的固有宽度撑出页面。

本阶段code-review已启动后被用户纠偏中断；仍使用原两个Standards/Spec审查代理继续同一轮，不新开整套审查。中文commit，不push/部署/启用模型。
