# Fiscal 搜索静态组件增量验收

2026-10-10，P10/R1、FE-02/QA-01。主仓唯一前端入口 `apps/web`，来源 v6.0.2。

## 实现和来源证据

74466b4先归档SearchEmptyMessage完整小组件spec、1440/768/390来源样式及截图、桌面指针点击前后状态。按clone-website派发独立builder到主仓Git工作树 `D:/桌面/Trade/.scratch/fiscal-search-empty`（应用根apps/web）；桌面工具创建因聊天cwd不在Git根而返回Not a git repository，改用主仓Git建立隔离工作树，未回写旧模板。ff07646实现单个命名导出的静态段落和CSS Module，快进合并。

仅段落在本组件范围内；表格容器、搜索开关、分类、结果选择均仍由尚未实现的父组件负责。组件没有新增focus目标、状态、接口或产品路由。无新素材下载；复用Jakarta400本地字体。截图实际字节为JPEG，已修正新截图扩展名并更新spec。

三尺寸采样是同一桌面弹窗打开后resize的过程。新的平板/手机样本不覆盖此前fresh-open平板全屏布局证据；不能由子组件尺寸推断整个弹窗响应式完成。

## 实际渲染对照

独立临时SSR验证页由真实SearchEmptyMessage和既有SearchGuidance的TSX、CSS Module生成HTML，直接加载已归档的Jakarta400/600字节。在1440×1000、768×1000、390×1000实际浏览器分别取样、截图并查看；验证页和服务代码留在忽略的.test-output，不加入产品路由。

验证页做了CSS类名映射、手动@font-face及明确的父容器宽度。这证明实际组件DOM/CSS与本地字体字节的渲染，不证明Next的font loader、产品父布局、全局样式组合或已接入正式/app。字体family别名FiscalJakarta与来源Plus Jakarta Sans的名称差异单列，使用相同已归档字体文件。

| 视口 | 段落宽×高 | 既有Guidance容器高/文字高 | 对照 |
| --- | --- | --- | --- |
| 1440×1000 | 966×56.8 | 37.6 / 16.8 | 段落记录样式、相对尺寸一致，底部单行 |
| 768×1000 | 657.2×56.8 | 37.6 / 16.8 | 同上，底部单行 |
| 390×1000 | 317.375×56.8 | 71.2 / 50.4 | 同上，底部自然三行 |

每尺寸fonts.status=loaded、focusTargets=0。自动对照记录的16项段落样式（字体family别名单列）及宽/高，0差异；绝对坐标由验证父布局决定，不作为源弹窗位置验收。详见STATIC_COMPONENT_COMPARISON_20261010.json及local-{desktop,tablet,mobile}-static-search-components-20261010.json/JPG。SearchGuidance此次只补独立运行渲染证据，未改其实现，也未接路由。

## 工程验证与增量审查

Builder npx tsc --noEmit、git diff --check通过；合并后npm run check的ESLint、TypeScript及Next生产构建通过，OUTPUT_PLAN原10个page路由全部保留。纯静态组件不添加镜像行为测试，不重复后端套件。

沿用R1原code-review过程，仅一次定向双轴复核74466b4...ff07646（两个新组件文件），没有重新调用整个阶段skill。

### Standards

0项可行动发现。命名导出/单段落/无新增状态符合AGENTS及规格；CSS Module是该来源规格明确约定。明确重置及少量共享测量值属于来源复刻要求，不需为此建立抽象。固定代码异味基线未发现需修改项。

### Spec

0项可行动发现。原文/三ASCII点、DOM、静态语义、计算样式、父宽度和自然换行满足spec，没有扩展到搜索、路由或账户行为。三尺寸渲染已由父任务补齐，结论保持在静态子组件范围。

本次无待修复发现。SearchEmptyMessage与SearchGuidance仍未导入正式路由；完整搜索、来源/company/NASDAQ_HOOD/和/app布局未完成，R2未启动。

临时3120验证服务已通过其原执行会话停止，浏览器视口已reset。自动审批拒绝工作树node_modules依赖链接清理命令（返回策略阻止，未提供细项原因），因此隔离工作树和其junction保持；主仓node_modules未操作、验证成果已合并，后续可复用该工作树或按允许的生命周期入口清理。该临时资源状态不影响产品代码检查或正常同步。
