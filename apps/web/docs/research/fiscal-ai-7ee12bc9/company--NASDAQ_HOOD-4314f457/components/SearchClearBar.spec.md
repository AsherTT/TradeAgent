# SearchClearBar — R1 搜索清空装配规格（2026-10-12）

## Overview
- 来源： https://fiscal.ai/company/NASDAQ_HOOD/ ，当前 v6.0.2。
- 目标：同 namespace 的 `SearchClearBar.tsx` / `.module.css`；复用已验收的 SearchClearButton。
- 证据：`../CLEAR_ASSEMBLY_SOURCE_{desktop,tablet,mobile}_20261012.json`，截图同 screenshot namespace 的 `source-clear-assembly-*-20261012.png`。
- 只还原选定清空条；当前来源普通 AAPL 查询无 Clear Search，HOOD pages 有。47 页结果不在本增量。
- 产品适配明确为：SEC 搜索非空 query 显示同样的清空条；空 query 隐藏；样本参考模式保持原实现，不新增直接页面模式。

## DOM Structure
- div > SearchClearButton > span.inner > span.label。
- `SearchClearBar({ onClear, label? })`；命名导出，无内部状态。默认英文 Clear Search。
- 父页面决定显示和清空 query；组件不请求 API、不路由、不调用 focus、不改分页。

## Computed Styles
- bar：display block，position sticky，top 0px，z-index 10；background rgb(28,28,33)。
- padding 4px 0，margin 0，box-sizing border-box，font-family var(--font-fiscal-jakarta),sans-serif。
- font-size 16px，line-height 24.8px，font-weight 400，color white；自然宽度，高度38px。
- button：宽100px/高30px，复用既有 SearchClearButton CSS；父条内局部 `vertical-align: middle`。2026-10-12 mobile原DOM补采确认这一属性，消除浏览器默认baseline额外空间；不修改原按钮CSS。
- desktop bar966px，tablet657.2px，mobile317.375px；以上是同一来源弹窗 resize 后的实际结果，不硬编码父宽、不称 fresh-open 弹窗布局通过。
- button与bar左边界一致，top相差4px；inner与label相对矩形复用已验收spec。

## States & Behaviors
- 无自身动画。button hover opacity0.7/200ms，focus-visible outline1.6px rgb(94,94,116) offset1.6px，active translateY1px；沿用既有子组件。
- bar随结果容器滚动固定在该容器顶部；不覆盖分类栏或输入。
- 原生按钮 mouse/Enter/Space恰一次 onClear，type button，绝不提交表单。
- 产品父层：query清空，offset和键盘选择回0，结果滚动回顶部，输入focus；旧query迟到响应不得恢复。
- 保持弹窗打开、当前语言、既有SEC分类、源元数据及请求代次规则；无自动导航。
- 关闭按钮/Escape保持query和分页，返回打开入口focus，恢复body原overflow；重开focus输入。
- 中文label为“清空搜索”；翻译不改变数据、权限或100×30框架。

## Content & Assets
- 英文 Clear Search，中文清空搜索为明确产品适配。
- 复用来源Jakarta600字体，无新增图片、图标或远程依赖。

## Responsive Behavior
- 1440/768/390同一bar/按钮样式；宽度由结果容器决定，无组件断点。
- 因产品行/状态不同，不比较整页绝对y坐标；对比bar/按钮/inner/label相对矩形和选定CSS，视觉检查中英三尺寸、短窗口滚动。

## Validation & Output Plan
- 唯一app root为apps/web，现有路由全部保留；不改全局基础、SearchCategoryBar或参考筛选行为。
- 来源规格先提交，隔离builder只实现bar及label扩展，typecheck后中文commit；合并后build，再由主代理接产品契约并复验。
- 行为测试沿用已确认的真实挂载组件/HTTP边界：清空分页与迟到响应、语言与focus、关闭/重开/overflow、禁用分页的focus边界。
- 不启动模型/worker/beat，不新增schema、研究准入或全球目录；此增量不代表R1结束。
