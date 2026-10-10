# Fiscal 清空控件与投资者状态增量验收

2026-10-10，P10/R1、FE-02/QA-01。唯一入口 TradeAgent/apps/web，来源公开公司 Overview v6.0.2。

## 来源与独立实现

f1e54c5先保存SearchClearButton完整spec、三节点的三尺寸计算样式及hover/focus-visible/pressed/原生mouse/Space清空状态。012a29a由clone-website独立builder在复用隔离工作树实现TSX与CSS Module，类型检查后快进合并。组件仅必需onClear回调、native type=button和两层span，不管理query、显示、焦点或路由。

当前原站有一条Recent Searches和30条默认结果。最新native mouse/Space清空、按钮移除后BODYfocus；此前locator清空序列保留inputfocus、30links。两种观察保留，父组件焦点行为不能由子按钮决定。Clear All/历史项移除未操作。

## 真实Next渲染与交互

Git忽略的.test-output/fiscal-controls-20261010独立Next应用实际导入主仓SearchClearButton及shared/fonts.ts的next/font/local，Next16.3.5默认Turbopack，临时监听127.0.0.1:3120。没有加入产品路由。客户端harness在form中保留query、callback/submit计数；onClear清空query并条件移除组件。

本地字体family为fiscalJakarta、fonts.status=loaded，使用与来源Plus Jakarta Sans相同的已归档Jakarta600。此次验证了独立Next字体loader/客户端组件，不证明产品父布局、全局样式或/app接入。

| 样本 | 按钮/Inner/Label | 记录样式与相对尺寸 |
| --- | --- | --- |
| 1440×1000默认 | 100×30 / 78.4×28.4 / 73.5875×28.4 | 138项一致 |
| 768×1000默认 | 同上 | 138项一致 |
| 390×1000默认 | 同上 | 138项一致 |
| 桌面hover | root opacity0.7、child opacity1 | 138项一致 |
| hover+focus-visible | ring1.6px rgb94/94/116，offset1.6 | 138项一致 |
| 非hover+focus-visible | opacity1、相同ring | 138项一致 |
| 稳定pressed | translateY1px、opacity0.7 | 138项一致 |

CLEAR_BUTTON_COMPARISON_20261010.json保存七组对照。字体family别名单列；绝对坐标由不同验证父容器决定，不作为来源位置验收。首次pressed即时opacity0.998198仍处于0.2s hover过渡，另存transient；保持鼠标按住后补采稳定opacity0.7，没有修改来源transition。不宣称整页逐像素验收。

真实mouse release/Enter/Space顺序使callback累计1/2/3，每次恰增1；query为空、按钮移除、submit始终0。来源mouse/Space清空已采；本地Enter通过，不额外宣称来源Enter清空已采。浏览器error/warn日志为空。三尺寸及桌面focus/pressed截图归档，平板/手机实际截图已查看。

## 投资者新增证据

v602-investor-{desktop-default,desktop-hover,desktop-focus,mobile-default}-20261010.json.gz保存Investors空query下首条JFS、第5条Pacific Select长标题和末条OFI各12节点HTML/样式/矩形。桌面实际1440×1000，各966×48；手机实际390×1000，短标题317.375×40.3、长标题317.375×60.6，头像隐藏、自然换行。已有HOOD匹配样本另存，不合并宣称完整卡片规格。

类别切换后首条父键盘选择背景rgb28/28/33，非hover；其余透明。第5条从真正非hover透明变为hover rgb64/64/79；首条选择背景保持。长标题键盘focus-visible ring1.6px rgb94/94/116、offset1.6，hover仍保留。来源桌面截图已查看，父选择/hover/DOMfocus分开。

首次桌面重设实际仍390，未作为桌面证据；恢复后读取确认1440，正确覆盖归档。平板请求768实际仍1440，未保存或登记完成。浏览器定向尺寸/绑定调用超时后重新获取现有标签成功，不是网站打不开或skill失败。后续仍补平板、非hover焦点、query高亮/类型标签、分类键盘/跨路径选择；没有派发投资者card builder。

## 工程验证

首次npm run check的lint误扫描Git已忽略.test-output的临时Next第三方bundle，出现323errors。6ca0cef将同目录加入ESLint globalIgnores，不忽略src/产品脚本，TypeScript/build配置未改。修复后完整lint/typecheck/production build通过，原10个page路由保持。无后端代码修改，不重复全后端套件。

## Standards

沿用R1原code-review流程，仅f1e54c5...012a29a组件及追加012a29a...6ca0cef单个lint hunk定向复核，没有重启阶段skill。0项可行动发现：named export/native callback/无独立状态符合AGENTS/spec；CSS Module、固定尺寸和明确重置是来源契约，不形成可行动异味。临时目录排除与.gitignore一致，不屏蔽产品源码。

## Spec

0项可行动发现：DOM/原文/必需onClear/type=button/默认与伪状态符合规格，没有查询存储、focus restoration、额外props或路由。追加lint排除合理支持spec实际浏览器验证。主流程补齐渲染，结论限于子组件。

## 剩余范围与资源

SearchGuidance/SearchEmptyMessage/SearchClearButton三独立组件已有实现和有界渲染证据，均未接正式路由。完整搜索/来源pathname、导航、公司页签/内部滚动/图表及/app仍未完成，R2未启动。API/模型/worker、数据库、环境/部署未操作。

3120服务通过原会话停止，成功本地验证标签关闭。来源定向临时1440尺寸已清除，最终恢复既有390×1000、Investors空query，标记保留。viewport capability已reset，后续以实际读数为准。本地connection-refused错误标签因URL policy不能再操作，未标记保留，交由临时标签生命周期结束；未绕过错误页。复用工作树和原junction保持，不重试前轮被策略拒绝的链接清理。
