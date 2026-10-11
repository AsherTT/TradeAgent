# Fiscal 上市地点增量验收 — 2026-10-12

代码检查点：b448d49规格/类型 → a013509隔离builder → 23216c3来源数据、父接线与可访问性修复。仍为P10/R1；仅此次上市地点增量完成，完整搜索、公司报告和整个/app未完成。

## 工作流与来源

沿用迁入apps/web的clone-website技能：真实来源DOM/计算样式/图片 → 完整小规格 → 独立工作树builder → 主仓接线 → 实际Next三尺寸/状态验证。原模板项目保持历史只读，apps/web为唯一前端维护根。来源公开 https://fiscal.ai/company/NASDAQ_HOOD/ 的搜索弹窗，采集版本v6.0.2；不调用私有接口、不假造账户历史。

九家默认参考公司的展开数量：NVDA40、AAPL36、GOOG65、MSFT42、AMZN39、SPCX27、TSM15、META38、AVGO29，总331。保留来源market、href、国旗及顺序；同href别名不去重、不推断ADR/股类或同证券。HOOD历史搜索22条不冒充本地默认结果。下载21个实际SVG，来源URL、bytes、SHA256见listing-flags-manifest-20261012.json；脚本支持缓存重放、URL域/path约束及SVG签名检查。

## 三尺寸对照与视觉纠偏

英文AAPL展开36条，1440×1000、768×1000、390×1000逐行比对链接/market文字/国旗的x、y、width、height，共324个矩形、1296个几何值，最大差0px，market/href匹配。证据：listings-geometry-comparison-20261012.json，来源桌面query-open及平板/手机fresh档案，本地listings-local-{1440,768,390}档案。这里的“0”只覆盖这些测量，不是整页像素或全部交互验收。

截图检查发现国旗虽矩形尺寸一致，矩形SVG仍需原站object-fit:cover/center才有正确圆形裁切，已补子行和主公司图像样式并重拍；最终源码/三尺寸截图包含修复。列表行30.3px、gap2px，36条stack1160.8px；头部到子区域gap10px，底部分隔线.8px/opacity.3。来源hover/输入焦点、背景公司页面、自定义滚动条与lab不同，不能由局部几何推断这些内容还原完成。

认可截图在页面design-references目录：listings-source-desktop-open-20261012.png、listings-source-tablet-fresh-20261012.png、listings-source-mobile-fresh-20261012.png、listings-local-{1440,768,390}-20261012.png及中文listings-local-zh-final-20261012.png。

**不用于fresh父布局验收的档案：** apple-tablet-query-open、apple-mobile-query-open及对应source-tablet/mobile-open截图为桌面弹窗打开后resize；apple-tablet-fresh-open虽文件名含tablet，实际viewport为390（窗口覆盖作用于当时选中本地标签），不能记768。mobile-exact-css仅内在样式参考。apple-open-default/desktop-open用于早期内容与多展开采样。正确768首次打开已另开来源页重新采集。

12个大DOM/CSS档案存为.json.gz，无损解压字节核验通过，清单见listings-archives-20261012.json；原始JSON另外保留在D:/桌面/Trade/.scratch/r1-listings-raw-20261012。数据、比较、行为与素材manifest仍为普通JSON。

## 交互与审查

额外边界：默认1280×720窗口下，现有父modal被90dvh上限限制为648px，内容662px，仍有外层原生滚动槽（clientWidth985px）。本轮三个正式对照高度均为1000px；720px父壳与滚动条状态仍待补来源采样/适配，不能计入上述0差异范围。最终中文展示截图为1440×1000验收尺寸，已恢复浏览器默认窗口。

- mouse/Enter/Space展开和折叠；展开不选择或关闭，36子行折叠后移除。
- NVDA+AAPL同时76条；9公司全展开331子链接、30主结果，无重复ID、失败图像或页面横向溢出。
- 原始子链接Enter和鼠标选择DB:APC，关闭后反馈Apple Inc. · DB:APC及XFRA_APC真实链接；焦点回到打开按钮。
- AAPL筛选保留展开；过滤成NVDA后再清空，Apple折叠、仍可见NVDA保留展开。Escape恢复body overflow；切中文保留AAPL、公司分类、36条展开。
- 原R1 spec轴新增diff0项；standards轴1项P2：listbox内独立按钮/链接与选项导航不匹配。已改命名region+原生链接，移除option/aria-selected/活动后代关系，补隐藏键盘说明/原子播报；空query Tab自然前进。仅该问题定向复验关闭，剩余0项，未重启阶段code-review skill。

行为记录见listings-behavior-local-20261012.json；其中早期option计数在可访问性修复前，末尾三项验证最终模型。源码检查通过lint/typecheck/build；真实3107入口前端36 passed、0 skipped。浏览器无error，记录中有编辑过程中Fast Refresh整页刷新提示。未改后端、环境配置或数据库，未启动模型/worker/beat。

## 适配与下一项

本地仍只筛选30条主参考结果，331条不是全球可搜索证券目录。语言/关闭重开保留上下文、原生disclosure与读屏语义是适配；原站关闭重开会清空query/展开。完整全球数据、47页模式、滚动条全状态、来源公司整页仍待。下步优先来源搜索的页面导航/返回状态和滚动，再补公司报告，之后按正式计划整站重构/app，R1退出后进入R2。
