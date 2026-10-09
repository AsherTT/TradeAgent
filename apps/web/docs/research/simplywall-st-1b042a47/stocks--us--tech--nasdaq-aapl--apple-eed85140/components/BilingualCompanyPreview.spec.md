# 公司来源双语验证页与页面语言入口

用户2026-10-09要求继续开发，并为这些页面添加中文/英文语言按钮。基准49cfc92。

- 复用根LanguageProvider及既有LanguageSwitcher，默认中文，使用同一个tradeagent-preview-locale cookie；无重复全局按钮，无新语言库。
- 盘点/保持首页、参考首页、注册、登录、门户、公司详情、研究列表、研究详情、功能联调和公司组件验证页。已有产品与账户页共用ProductHeader或来源导航的按钮；补齐公司验证页，功能联调横幅按当前语言显示。
- 验证页入口page保留server metadata，在client CompanySourcePreview读取useLanguage，同一切换即时更新标题、静态免责声明、表格内容与后续说明；SSR首屏依根cookie选择，无英文闪回。
- 英文保留来源文字和href，中文翻译所有静态说明、标题、表头、列表、时间范围与语义名称。日期、UTC、公司/机构名称、SEC表号和链接地址保持真实含义；不翻译用户输入、原文证据或发起任何研究。
- 语言按钮在手机和桌面可见，选中状态aria-pressed明确，暗色背景选中按钮用深色文字以保持可读性。
- 新页面后续沿用相同按钮/全局语言选择，加入统一page title映射，刷新与跨页保持。
- 来源组件继续接文本props；翻译发生在隔离lab装配，静态样本不接自有/app。
- 复用已认可的React DOM/HTTP seams：实际provider按钮切换后，中文/英文标题与说明变化，lang/cookie/aria-pressed同步，href与表格结构保持；SSR带zh/en cookie核对页面首屏和title。CSS以实际浏览器三尺寸校验。
- 保留完整公司页pageBuildersReady=false；公司分析师展开当前触发来源注册/登录提示，不能虚构85条或制作假展开按钮。
- R1原code-review流程只定向复核新增，不重复整阶段调用；提交中文，未授权push或启用模型worker。
