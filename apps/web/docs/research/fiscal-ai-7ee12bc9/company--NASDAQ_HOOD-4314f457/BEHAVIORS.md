# 已观察行为与待采状态

## 2026-10-12续开发：选定清空条与产品适配

真实源站普通AAPL查询无Clear Search，HOOD pages模式有；父条sticky/top0/z10/padding4px0/background28/28/33，高38px，button100×30，补采vertical-align:middle。三尺寸来源是打开后resize状态，不泛化为fresh-open弹窗布局。来源直接页面模式47项仍不在R1本增量。

正式SEC搜索新增非空query清空入口（明确适配），源样本筛选模式不改。中英三尺寸bar/按钮大小与无横向溢出已验；鼠标/Enter/Space清空保持dialog、focus回输入；1280×720滚动720px后父条保持结果viewport顶部，清空scrollTop回0。普通迟到结果拒绝、迟到401仍失效。证据为同目录CLEAR_ASSEMBLY_*及components/SearchClearBar.spec.md，产品功能不等同原站所有模式。

## 2026-10-12 公司身份/概览选定区块

重新采集来源三尺寸默认态、概览描述展开态；真实指针移至控制：hover下划线；Tab到网站链接、Shift+Tab回展开控制：focus-visible描边1.6px rgb(94,94,116)/offset1.6px。描述默认60px、展开随内容宽度，源声明max-height200ms transition；其余选定身份logo/name/market静态，不滚动切换。公司其他报价/收藏/音频/整页章节不在此次选定范围。完整小spec、builder与有界QA见[本轮验收](COMPANY_IDENTITY_VALIDATION_20261012.md)，下表是早前更宽范围的采样缺口，未因此全部关闭。

| 行为 | 证据 | 状态 |
| --- | --- | --- |
| 手机 burger 开 / close 关 | 页面操作后 DOM、矩形、样式和展开图 | 两端已采；动画、Escape、焦点回归未采 |
| 桌面变小屏 | 1440/768/390，80px侧栏变负translateX抽屉 | 默认已采；临界断点、打开后旋转未采 |
| 默认公司 | Overview、10 tabs、5Y图、季度Revenue | 其他 tabs/图表状态未采 |
| 桌面内部滚动 | 756px viewport / 2541px scrollHeight | 未完成 sweep，fullPage图未覆盖内部全部内容 |
| Analysis菜单 | 恢复前后默认按钮可读，点击操作连接超时 | 未采，尝试不算成功 |
| 搜索/Resources/Settings/Help/Updates | 默认控件、CSSOM | 展开/hover/键盘未采 |
| 公司操作、Earnings/图表控件 | 默认控件和文本 | 交互/公开限制待采 |
| 手机统计与 Bulls/Bears 的 Show More | 380×4040 默认图已读图，统计和观点区均有截断/展开控件 | 两处展开/收起未采；默认DOM完整文字不代表默认视觉全部可见 |

没有得到验证码，也未验证 Analysis 点击后一定是登录弹窗。旧会话其他 URL 的登录限制不能代替本次状态，连接恢复后据实际状态重采。


## 2026-10-10补采

普通点击已打开Analysis/Resources/Settings，点击公司标题后菜单关闭；展开内容与样式见RECOVERY_20261010.md及完整gzip。Analysis可见12项，隐藏Dividends不计入。Escape未证实关闭、hover未完成，Updates未取得展开内容；不能把上述采样作为完整交互模型或builder派发资格。


## 2026-10-10 搜索与静态提示增量

搜索是点击打开独立dialog并聚焦input；空All有30条，公司/ETF/投资者各10条，HOOD有匹配，无匹配显示No results found...。手机清空恢复默认，Escape关闭；投资者ArrowDown/ArrowUp移动data-active及rgb(28,28,33)背景。静态提示三尺寸内容相同，手机自然三行，指针前后全CSS相同。SearchGuidance已按spec实现并合并，未接路由。完整行为与未采边界见SEARCH_RECOVERY_20261010.md；不能泛化为搜索/导航组件全部合格。
