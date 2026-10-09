# EnhancedANavigation：原导航结构适配

Target: src/components/sites/simplywall-st-1b042a47/product-a/EnhancedANavigation.tsx
Source: https://simplywall.st/，原SourceNavigation，2026-10-06 computed-full root0。
Screenshot: docs/design-references/simplywall-st-1b042a47/root-8a5edab2/source-desktop-1440-20261006.png及768/390同名截图。
Interaction: 原桌面Features hover打开、鼠标离开关闭；补同等click/Enter/Space和Escape键盘可用性；手机hamburger展开原菜单布局。

Foundation无需重写：复用.sws-source下source-styles.css、preview-interactions.css、locale.css。
DOM沿用section.navigation.section-55 > div.navbar.w-nav > brand + nav.nav-menu.w-nav-menu(main-links dropdown、search、authentication) + mobile link + menu-button。
精确CSS来自来源类名，不手估：navigation position relative z999；navbar原宽度/间距/高度；dropdown w--open白色6px圆角。mobile<=991菜单top72px、margin0 12px、padding0 24px、white background。原搜索245.6x38px，6px圆角，#fafafa，sans13px。原按钮.in-nav字体/内边距/颜色均复用。不新增居中max1360公共header。
原brand图片宽108px作为槽位，自有TradeAgent文字/mark在同一brand位置，是明确品牌差异。不要复制原公司logo冒充自己。
桌面产品功能下拉三项：公司与研究门户/#portal；财务分析/#financials；报告与证据/#reading。原Plans/About位置改研究流程/#workflow、数据说明/#data；广告不属首版。移动端显示同一功能落点；所有links本地。
搜索槽位为真实链接/app#companies，明确“登录后搜索公司”，保留source-search-preview/source-search-link样式和SVG；不伪装匿名全市场搜索。不调用来源search接口。
认证区保留原.button.in-nav/.button.login.in-nav及LanguageSwitcher，开始研究/app和登录/login；手机登录与原菜单按钮位置保留。
click菜单选项关闭features/menu；Escape关闭并回summary/menu焦点；outside关闭。ARIA labels双语，所有本地链接可键盘操作。
Assets复用shared/icons.tsx中的已实测NavSearchIcon；不下载新资产、不加外链。内容是用户批准范围的品牌/落点适配，原verbatim内容仍在参考页。
Responsive沿用源991和1199搜索隐藏、原navbar布局；不要把手机menu改成第二行常驻导航。
Build: 2空格、命名导出、无any/inline style；npx tsc --noEmit + npm run build。只修改目标文件，禁止改原SourceNavigation/CSS/其他产品文件。
