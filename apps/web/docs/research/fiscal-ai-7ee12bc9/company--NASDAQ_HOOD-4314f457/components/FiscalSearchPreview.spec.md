# FiscalSearchPreview 开发验证入口规格

## 范围与依据
- 用户要求继续 R1、打开 Docker 并提供可手动查看的当前效果。
- 本页是独立开发验证容器，不复刻未采完整的搜索父层、结果列表或公司整页。
- 唯一新增路由 `/labs/r1-fiscal-search`；原十个页面、正式 `/app` 与源 pathname 保留。
- 复用已验收 SearchClearButton、SearchEmptyMessage、SearchGuidance 原文件和字体；不修改其来源 DOM/CSS/文案。
- 来源三个组件的字体、样式、响应式与交互由既有逐组件规格/证据定义；本页外围是自有验证界面，无来源一比一声明。
- 无新增来源资产、全局基础、API、身份/模型/队列/数据库契约。

## 文件与结构
- `src/app/labs/r1-fiscal-search/page.tsx`：服务端路由，accountMetadata、本地 fiscalJakarta.variable 与预览组件。
- `src/app/labs/r1-fiscal-search/FiscalSearchPreview.tsx`：命名导出客户端组件。
- `src/lib/account-page-titles.ts` 与已有 shared/i18n/zh.json：增补此路由标题及中文映射。
- 外层 main 深色背景、白字、上下32px，容器水平16px，h1及说明、统一语言按钮、内部导航。
- 顺序：清空操作演示；静态无结果提示样本；静态搜索提示样本；验收步骤。
- 每个来源样本容器 `lang="en"`、背景 rgb(41,41,49)，水平居中。
- 样本容器宽317.375px，min-width768px时657.2px，min-width1024px时966px，max-width100%；这是验证宽度，不表示完整搜索父层。
- 自有容器使用 Tailwind；不得用全局选择器改来源组件。
- 实际主应用测量后：按钮验证父容器用普通行内布局居中，避免 flex item 将来源 inline-block 计算成 block；样本容器内 span 的 outline-color 作用域恢复为 currentColor，抵消主应用 Tailwind preflight 的未显示 outline 色。不改来源子组件或全局基础。

## 交互状态（自有验证容器）
- 初始 query="HOOD pages"，清空计数0。
- 明确可读 label 对应 input；输入仅用于清空演示，不查询证券或调用接口。
- query非空显示真实 SearchClearButton；query空不显示。
- onClear置 query空，计数加1；原生按钮 mouse、Enter、Space各触发一次。不增加手动键盘处理。
- 重置示例按钮恢复初始 query 并把计数置0；用户能反复验收。
- 计数用普通可访问状态文案/aria-live polite；不显示内部调用堆栈。
- 静态无结果提示始终显示、明确标记静态来源样本，不冒充输入查询返回值。
- 静态搜索提示保留示例原文；说明其中键盘提示不代表本页已实现搜索结果选择。
- 统一 LanguageSwitcher/useLanguage 切中文/英文，只翻译外围说明与操作；不清空 query 或计数。
- 说明来源控件保留英文供逐项对照；语言偏好沿用既有上下文 cookie。
- 内部链接：`/app` 正式功能工作台、`/labs/r1-company-data-status` 公司来源组件、`/` 首页。
- 手动步骤覆盖输入、hover、Tab焦点、Enter/Space、重置、语言切换、三宽度无横向溢出。

## 验收与边界
- 必须实际 Next 客户端浏览器验证 mouse/Enter/Space、语言切换保留输入/计数、刷新偏好及1440/768/390。
- 新容器不引入重复清空、不抢输入焦点、不请求新接口。
- 浏览器测量真实导入三来源组件，复核原字体/尺寸/关键样式，保存本地预览截图。
- builder在隔离工作树实现，完成 typecheck，中文提交；主仓合并后完整 check。
- 沿用 R1 原 code-review 两轴仅新增差异定向复核，不重启整阶段。
- 完整搜索、投资者结果、公司整页与 `/app` Fiscal布局尚待；P10/R1继续，R2未启动。
