# FiscalAppSidebar — 2026-10-12

## Overview
- 同Fiscal HOOD来源，目标 `src/components/sites/fiscal-ai-7ee12bc9/shared/FiscalAppSidebar.tsx`、`.module.css`。
- 来源截图 source-app-shell-desktop/mobile-open-20261012.png；证据APP_SHELL_SOURCE三尺寸/open/mobile_details/hover/controls。
- 范围仅来源固定栏/抽屉、导航项图标/标签与关闭控件；不构建商业菜单/筛选/收费API。
- 自有入口数量、标识、角色、语言、返回焦点为明确适配；不称整个源sidebar所有菜单1:1。

## Contract / DOM
- interface AppNavigationItem { id:string; href:string; label:string; icon:"dashboard"|"analysis"|"query"|"settings"; selected:boolean }，命名导出。
- props items:readonly AppNavigationItem[], open:boolean, navigationLabel:string, closeLabel:string, searchLabel:string, searchHref:string, onClose:()=>void, onNavigate:()=>void, sidebarRef:RefObject<HTMLElement|null>, languageControl:ReactNode。
- aside#workbench-navigation ref > brand row(Link.home + close button) > mobile search Link > nav(label) > ul > li > Link(icon span + label span) > mobile language区域。
- 自有brand Link.href=/、aria-label TradeAgent；复用现有TradeAgent gold T标识SVG：viewBox0 0 64 64，rect64/rx14/#fdcc6a；path M17 18h30v7H36v24h-8V25H17z/#191816。品牌槽desktop72px高/mobile76px高是明确自有适配，不能声称源logo/版本组件。
- 图标复用同shared/icons.tsx的DashboardIcon/AnalysisIcon/QueryIcon/SettingsIcon/CloseIcon，全部已有源SVG；不要用新通用图标替代。
- Links用真实href，selected时aria-current=page；正常/修饰键点击语义保持。onNavigate在本地点击用于关闭产品抽屉。
- open时aside role=dialog/aria-modal=true/aria-label navigationLabel；关闭移动端靠visibility:hidden隐藏与不可聚焦，desktop始终可见。不能给closed aside全局inert/aria-hidden，导致桌面失效。
- close native button typebutton，aria-label closeLabel，onClick onClose；组件无body/style/focus/route状态逻辑。

## Computed styles
- aside fixed top0/bottom0/left0，width100%，z101，flex-column，bg28/28/33，border-right.8px solid64/64/79，Jakarta16/24.8/400，colorwhite，box-sizing:border-box；mobile translateX(-100%)/visibility:hidden，open translateX0/visible；transition transform .2s,top .2s,height .2s。
- >=1024 width80px/transform:none/visible，mobile search/close/language隐藏。
- mobile brand row padding16px，44px close alignright；close44×44/min44，bg64/64/79/radius12/border.8透明，flex-center，CloseIcon16×16。
- mobile搜索容器padding0 16px；Link42px高，padding0 14px0 40px，border.8px solid175/175/182/radius12/bg44/44/53，font16/40/400;color175/175/182，overflowellipsis。可复用真实search SVG16×16（同header源SVG）；源search在mobile y72，高42，本版品牌槽不同位置列为适配。
- mobile nav padding12px16px8px；ul margin/padding0/list-style:none；Link display:flex/align-center，width100%，min-height44/box-sizing:border-box，padding8px12px8px10px，radius10，margin-bottom2px；icon22×22及margin-right12px；label14px/20.3px/400/color175/175/182。selected背景64/64/79，正文white（适配标识当前自有页面）。
- desktop nav padding8px0；ul flex-column/align-center/gap10px；Link flex-column/center，padding0/border0/bg透明，gap2px，自然高63.05px；iconbox44×44/border.8透明/radius4/inline-flex-center，SVG22×22；label11px/17.05px/400/white/nowrap。自然文字宽度，不硬编码来源英文标签宽。
- selected iconbox背景64/64/79；source Dashboard真实hover iconbox背景从透明→44/44/53，无时长动画，hover同样用于本地未选项。

## States & behaviors
- 所有链接真实导航，无原站外跳伪装自有业务。模型/worker不启动。
- 原来源Escape不关，close后focus留在隐藏按钮；产品由父层处理Escape/Tab圈定/返回focus/断点关闭，这是明确无障碍适配。
- keyboardfocus适配outline1.6px rgb94/94/116/offset1.6；desktop link outline不碰原未知sourcefocus。
- languageControl父层同一Provider，drawer切语言不关菜单/不清数据。
- reduce-motion媒体查询可移除自身transition，属于明确可访问性适配。

## Assets / responsive / QA
- 只复用既有字体/SVG及自有T路径；无图片下载/第三方请求。
- 1440 desktop80，768/390全宽抽屉；实际1023/1024切换，不能用768当桌面断点。
- 默认/selected/hover样式和open/closed布局有证据；品牌/目录数量、导航语义/键盘/语言明确适配。局部相对形状与状态QA，不声称全源sidebar像素一致。
- 只改两个目标文件，npx tsc --noEmit、中文commit；主代理每次merge后build。
