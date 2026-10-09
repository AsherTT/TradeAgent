# 数据来源区域增量验证

2026-10-09，Asia/Shanghai。P10/R1/FE-03/QA-01仍进行中。

## 实现与来源

f58d910先持久化spec、三个宽度92节点的有界DOM样式子集、补采样式与桌面区域图，并建立文本类型和同surface装配slot；共享基础lint/typecheck/build通过后，专用小工作树提交4de1386，合入主前端为f01f37a。d78757a校正验证页长内容产生的系统滚动条宽度干扰。均为中文提交，未push。

CompanyDataSources仅接文本props；四列六行、原生列表、混合文字/公开来源链接、脚注及TTM说明；没有网络、账户、模型、财务计算或真实数据声明。静态fixture仅用于/labs/r1-company-data-status，不进入自有/app，完整源pathname尚未装配。两组件共用原来源section，不增加独立卡片。

CompanyDataSources.source-{desktop,tablet,mobile}.json.gz来自已取得的完整分块DOM；source-extra.json补充中间宽度的vertical-align、sup、列表、边界等；source-focus.json实测provider链接焦点为underline、gold、transition none。hover来自页面实测CSS规则，动态hover仍未验。所有12条链接href与来源样本逐条核对，没有访问外部链接目标或第三方业务API。

## 三尺寸

| 实测视口 | 本地内容/表格宽度 | 来源内容/表格宽度 | 本地/来源表高 |
| --- | --- | --- | --- |
| 1440×1000 | 800 / 800 | 799.254 / 799.254 | 393.663 / 394.169 |
| 768×1000 | 704 / 704 | 696.217 / 696.217 | 414.425 / 413.344 |
| 390×844 | 358 / 429.4 | 358.377 / 429.359（来源高843） | 706.925 / 705.785 |

各宽度document.scrollWidth均等于视口；只有手机表格在自身region溢出。h3 18/27/500→lg20/30；正文14/23.8→lg16/27.2；表格13/19.5→lg14/21；单元格8×16、顶对齐、ul16缩进、原生sup均已读取。不同页面坐标缩放导致边框0.8与0.837696、约0.5～1.2px表高差；平板独立外框仍约8px宽差、部分文字断行及截图坐标舍入需在整页装配后复核。不宣称逐像素或整页通过。

首次本地手机长页面由系统纵向滚动条挤占15px，使内容343px；验证页新增preview.css仅当html包含.sws-company-preview时隐藏根滚动条，保留原生纵向滚动与358px内容。该规则是隔离验证框架适配，不能视为来源整页滚动机制已还原；离开lab时选择器失配，其他路由仍保持原规则。

手机region tabIndex=0及语义名称为明确的键盘适配。通过实际ArrowRight操作，scrollLeft由0增加到4、随后8；clientWidth358、scrollWidth429，焦点保持region。provider焦点下划线/gold/无过渡与来源相同。keyboard-validation.json和mobile-scrolled图保留证据。

## 工程与复核

最终lint/typecheck/production build通过；六份已有前端行为/SSR检查启用实际预览，31 passed、0 failed、0 skipped。静态组件以浏览器三尺寸、键盘和href对照验证，没有新增镜像实现的测试。后端无代码变更，未重复后端474项检查。

沿用原R1 code-review代理，只复核0940aee...f01f37a新增：Standards0、Spec0；未重新调用整阶段审查。验证页d78757a由主代理按三尺寸定位、修正和复验，记录为框架适配。

## 截图及限制

- data-sources-source-desktop.jpg：实际桌面区域参考，已读图。
- data-sources-local-{desktop,tablet,mobile}.jpg：修正后的三个宽度；desktop-region为便于阅读的局部图，mobile-scrolled为键盘滚动状态。
- overview-tablet-full-signup-gate-diagnostic.jpg：768×12737，来源DOM高12743，6px舍入；已读图发现注册/登录提示覆盖，故仅诊断，仍不能补充默认平板全页验收。

本轮没有出现机器人校验；来源登录提示没有代为注册/登录或接受条款。完整滚动/图表/菜单/展开/异常状态、其余章节spec/实现、完整pathname、自有契约适配和接入后对照仍待。
