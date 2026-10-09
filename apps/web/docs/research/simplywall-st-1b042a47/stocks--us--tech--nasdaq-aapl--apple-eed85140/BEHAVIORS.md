# 来源行为采样记录

2026-10-09，Asia/Shanghai。状态：进行中。

已实际观察：公开公司概览可访问，无机器人验证；三个实测宽度都呈现更新时间表，静态表无按钮/链接/切换。桌面顶部导航和章节侧栏，窄屏横向章节导航及固定底部入口。更新时间表section内距16→32（md=768），表格字号13→14（源CSS明确1024）；标题24px/32px不随这三个尺寸改变。

已读到公司子页面的真实href，以及More details的#about；未点击所有子页，不把href存在当作目标页面已验收。

新增公开交互：点击See All Risk Checks打开Risk Checks对话框，14条检查含13条Pass和1条No data；关闭按钮返回概览，DOM确认对话框消失。保存risk-checks-desktop.dom.txt、分块32项样式和1440×999截图；弹窗内部滚动、键盘、动画与窄屏仍未采完。

公司页随后出现“continue analysing AAPL”的注册/登录提示。关闭后新DOM无该提示；点击More details后的DOM再出现提示，About段落为完整描述且按钮显示Show less。URL元数据仍为主概览，不把href=#about推断成已经验证的滚动/导航行为；滚动位置读取超时，无有效测量。more-details-about.dom.txt和company-signup-gate.dom.txt是状态证据，不是成功进入登录后内容。

未观察：公司滚动后的header/章节侧栏状态、其他按钮和hover、价格区间切换、展开/数据菜单、加载/错误、登录后内容。图表tooltip在默认采样时可见，但触发机制和其余状态仍待采集。

门户Analysis点击后保持Holdings选中，并显示注册/登录提示。未登录、未接受条款、未绕过；其内容仍未采到，不能登记Analysis成功。该限制不是机器人验证。

数据来源表在390宽度保持四列，原生auto table约429.36px宽、父容器约358.38px，overflow-x:auto；没有切换或折叠控件。provider链接通过键盘聚焦，text-decoration从none变为underline，gold颜色不变、transition none（source-focus.json）。来源hocus CSS还规定hover underline，但动态hover仍待。平板全页导出出现注册/登录提示，保留诊断图而不登记默认全页采样完成。

继续分析模型采样：保存三宽度9节点定向样式及新鲜桌面outerHTML；来源四条链接均target=_blank、rel=noopener noreferrer nofollow。前三条不同标签指向同一support分类地址；英文团队说明存在缺词/三空格且没有team链接，按真实来源保留，不补造链接。完整细节见CompanyAnalysisModel.spec.md与CompanyBilingual.validation.md。

点击Show 85 more analysts后仍只有默认三行，出现“continue analysing AAPL”的注册提示。保存analyst-expand-signup-gate.dom.txt；没有观察到85行展开内容，不实现虚假展开或推测机构名单。这是登录限制，不是机器人验证；未登录、注册或接受条款。

用户要求中英双语属于自有适配：在现有全局语言上下文下切换验证页、标题和组件文本，金融样本日期及公开href保持不变。真实浏览器验证英文刷新、跨页保留、中文返回与刷新；已有登录状态使/register跳转/app，记录为门户语言入口验证，不冒称实际注册页浏览器验收。注册页无会话双语SSR与表单输入保留由独立测试验证，无创建账户操作。390英文数据来源表ArrowRight后scrollLeft=40；模型链接键盘焦点underline/gold与来源一致。
