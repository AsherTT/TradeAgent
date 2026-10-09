# Fiscal 公司控制台来源检查点（2026-10-09）

2026-10-10最新增量：89db998补搜索默认完整630节点、HOOD匹配/无结果与三宽度静态提示规格；f5f7121按隔离builder流程实现首个SearchGuidance。随后补手机清空、四分类和Escape/上下键选择；合并lint/types/build与原R1增量两轴0项。完整搜索/导航状态、来源页装配和/app接入仍待，详见[搜索恢复与实现](SEARCH_RECOVERY_20261010.md)。下方记录按历史保留。

2026-10-10最新：自动化菜单采样已取得连续成功证据，Analysis/Resources/Settings和外部关闭状态已归档。较长等待与分批调用可继续操作；CDP鼠标移动等仍未全部核验，不再以工具超时断言网站打不开。见[恢复记录](RECOVERY_20261010.md)。本轮仅来源采样，完整规格/门户实现仍待。

用户已选方案 B，并要求复刻严格执行本仓 `.agents/skills/clone-website/SKILL.md`。本目录保存真实公开页面采样；不是已完成的参考页面或产品界面。

最新续开发：已实现隔离的本地字体配置、默认实测tokens、15个来源SVG及参考类型，尚未导入任何产品路由。原生本地页面读取/点击成功，同一标签切换Fiscal后导航/资产读取仍超时，不能再笼统描述为全面输入通道失效；已请求手动检查来源菜单。诊断与基础范围见 `FOUNDATION.md`。下方原采样检查点按历史保留，菜单等全状态及派发门槛仍未满足。

## 输出隔离与当前阶段

- 来源：<https://fiscal.ai/company/NASDAQ_HOOD/>，实际重定向后的 URL，页面版本标记 v6.0.1。
- 输出计划：`OUTPUT_PLAN.json`；源 pathname 保留为 `/company/NASDAQ_HOOD/`，当前尚未创建该路由。
- 已盘点 10 个现有 page 路由，源码、账户流程、首页、Simply 参考页和原有 lab 保留。
- 三尺寸默认截图、DOM、导航/页头扁平计算样式、CSSOM、SVG 和资产清单已归档；手机抽屉开/关已采。
- 当前为 Phase 1 来源检查及 Phase 2 资产归档的部分完成状态。没有完成全页面 scroll/click/hover sweep，没有冻结可派发组件 spec，也没有派发 builder、创建实现 worktree、装配来源页或改造 `/app`。
- 作用域字体/CSS与15个图标基础准备已实现，但未导入页面；归档字体不等于接入页面。恢复全状态采样后，按 skill 顺序建立基础、保存完整 spec、隔离 worktree 派发，再对照和产品接入。

## 证据文件

| 文件 | 用途及边界 |
| --- | --- |
| `desktop-chrome.json.gz` | 桌面导航/页头逐元素计算样式与矩形，567 行 |
| `mobile-closed-chrome.json.gz`、`mobile-open-chrome.json.gz` | 手机抽屉开/关样式，分别 565 行；关闭时离屏节点仍在 DOM，不能当可见内容 |
| `tablet-closed-chrome.json.gz` | 平板导航关闭默认样式，565 行 |
| `desktop-extraction.json.gz` | 桌面骨架、内部滚动容器、图片和布局；深层 children 部分被浏览器输出序列化为字符串，不能当完整递归组件提取 |
| `shell-assets-and-css.json.gz` | 浏览器读取的 CSSOM 和 56 个控件 SVG 条目；未实测 hover 规则仅作待验证线索 |
| `asset-inventory.json.gz` | 已观察界面资产（57 URL、262 inline SVG）；移除脚本、追踪像素及遥测项 |
| `source-desktop.dom.txt`、`source-mobile.dom.txt` | 默认公开文字/ARIA/链接；不同时刻截面，不是产品数据资格 |
| `mobile-navigation-open.dom.txt` | 手机抽屉展开的实际内容 |
| `download-manifest.json` | 下载成功/失败、URL、文件、字节数、SHA256 |

JSON 用确定性 gzip 归档，Python `json.loads(gzip.decompress(path.read_bytes()))` 可读取。截图目录：`docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/`。

## 截图尺寸与滚动边界

| 文件 | 请求视口 | 实际 JPEG | 核验结果 |
| --- | --- | --- | --- |
| `source-desktop-full.jpg` | 1440×1000 | 1440×1000 | 桌面 body 固定，左侧内部滚动内容高 2541、视口高 756；fullPage 并没有拍全内部内容，仍需逐段滚动 |
| `source-tablet-full.jpg` | 768×1000 | 757×3793 | 全页默认截图已读图；clientWidth/scrollWidth 均 758，JPEG 与客户区宽度不完全一致，后续对照保留差异 |
| `source-mobile-full.jpg` | 390×1000 | 380×4040 | 默认全页截图；clientWidth/scrollWidth 均 380，原站约 10px 滚动条占宽；不能拿 390px 成品直接声明逐像素一致 |
| `source-mobile-navigation-open.jpg` | 390×1000 | 390×999 | 展开截图已读图；展开后 clientWidth/scrollWidth 均 390 |

行情及正文只作来源参考，刷新和采样时间差可能改变值，不向自有 API 导入这些数字、新闻或结论。

## 资产归档

63 次请求中 8 成功、55 失败（48 个 HTTP 403，7 个 HTTP 429）。成功项为 Google 字体 CSS、6 个 TTF 和一个页面观察到的推广 JPG；JPG 尚未证明为默认主区必需图片。公司图标、样式表和部分图表资源未成功下载。SVG 有 DOM 证据，但未整理为运行组件。

脚本只访问已观察且限定来源主机的资源，4 并行、每请求 12 秒超时；失败保留，不用代理、绕过或猜造资产。重跑先核验并复用已有成功文件（字节数与 SHA256 一致才复用），缓存 CSS 继续发现字体，避免限流重试覆盖成功记录；缺失/损坏文件重新下载。重跑前检查失败类别，不连续刷请求。Google CSS 为归档，含远程字体 URL，不在运行页面直接导入；后续使用本地字体、限定 Fiscal 容器。

## 阻塞与续接顺序

资产 bundle 超时后，浏览器反复出现读取成功、点击超时。同浏览器原标签和恢复新标签均可读默认 DOM，Analysis 点击仍未取得可靠展开状态，不能从尝试推断已采到。本轮没有遇到验证码，也未验证登录阻挡，当前阻塞为操作连接超时；资产另有 403/429。

1. 恢复同一浏览器，优先 Analysis/Resources/Settings、搜索、帮助、更新；补 hover、键盘、关闭和各尺寸内容。
2. 补桌面内部滚动、公司页签及图表/公司操作完整状态，区分登录限制和公开状态。
3. 冻结作用域基础及第一批完整 spec，再依 skill 派发隔离 builder；目前合格待派发 spec 为 0。
4. 独立源路径三尺寸全状态对照后，映射 TradeAgent 门户/证券/研究契约并接入 `/app`；自有 Agent/预算流程单列，不宣称 1:1。
5. 接入后再三尺寸全状态验收。P10/R1/FE-02/QA-01 仍进行中，R2 未开始。

本轮基线生产构建通过，后续归档/helper 检查结果见主仓检查点。未修改应用行为，不重复运行无变化的后端套件；前轮 486 后端测试/36 前端行为检查仅为历史基线。

## 本轮增量闭环

最终全仓 lint/typecheck、helper 语法、7 gzip/8资产哈希/6TTF签名/10既有路由核验通过。离线模拟全部缓存有效复用及单字体损坏重取两种情况，其他请求模拟403时8条成功映射保持；外网请求0，不赋予真实来源资格。

沿用R1既有code-review流程，仅检查3fdaac3后的新增差异。Standards发现1项P2（重跑覆盖成功归档），963e487修复且原发现定向复核关闭；Spec初次0项，d8db3f0/963e487回归0项。未重审旧实现或重复整阶段skill。手机截断Show More缺项已单列，当前仍未达到builder派发条件。
