# FiscalAppHeader — 2026-10-12

## Overview
- 来源 https://fiscal.ai/company/NASDAQ_HOOD/；范围为公共顶栏布局、搜索入口和burger，不复制账户/帮助服务。
- 目标 `src/components/sites/fiscal-ai-7ee12bc9/shared/FiscalAppHeader.tsx` 及 `.module.css`。
- 截图同page screenshot namespace `source-app-shell-{desktop,tablet,mobile}-20261012.png`。
- 证据 `../APP_SHELL_SOURCE_{desktop,tablet,mobile}_20261012.json`、controls及1023/1024断点。
- 品牌/语言/入口文案与账户属于自有适配；源header含帮助和登录，本版替换成既有双语控件，不建设原站账户或无资格功能。

## DOM / contract
- header > div.container > div.row > Link.search + languageControl + button.burger > div.lines。
- 命名导出，props searchHref:string, searchLabel:string, languageControl:ReactNode, navigationLabel:string, expanded:boolean, onOpenNavigation:()=>void, buttonRef:RefObject<HTMLButtonElement|null>, searchRef:RefObject<HTMLAnchorElement|null>。
- 搜索采用真正本地Link，pointer/Enter到searchHref；不放不能输入的假搜索框；图标绝对定位在左34px区，SVG保留来源circle11/11/r8、line21/21/16.65/16.65、16×16、stroke2。
- burger type button，aria-label navigationLabel、aria-expanded expanded、aria-controls workbench-navigation；ref交给父层。组件无状态、事件监听或网络。
- 搜索shortcut键帽“/”仅>=1024显示；实际快捷键由产品父层提供，不伪造功能。

## Computed styles
- header fixed top0/right0/left0，height64px，display:flex/flex-direction:column/justify-content:center，z-index100，bg rgb(28,28,33)，border-bottom0.8px solid rgb(64,64,79)，box-sizing:border-box。
- >=1024 left80px；transition transform .2s,left .2s,right .2s。
- container width100%，margin-block:auto，padding-inline10px；>=768为12px。row flex align-center，gap6px，min-width0。
- search flex1，min-width0，height/min-height36px，box-sizing:border-box，relative，padding0 34px，border.8px solid rgb175/175/182，radius32px，bg44/44/53；Jakarta14px/34px/400，color175/175/182（实际placeholder颜色），cursor:pointer，overflow:hidden/nowrap/ellipsis，text-decoration:none，transition .2s ease-in-out。
- search左图标16px，center34px区域；kbd右区域34px；kbd12px/18.6px/700 monospace，padding3px5px，border.8px solid175/175/182，bottom2.4px，radius8px，bg94/94/116，color216/217/223，margin-right4px；沿用已验收Fiscal键帽样式。
- burger 28×28，padding5px，border0/bg透明，CSS block；>=1024 display:none。内部线width18px/height1.5px/white/relative；before/after absolute left0 top-6/+6，高1.5px/宽18px，content空；三层transition background-color .3s,transform .3s。

## States & behavior
- 来源默认、三尺寸、burger展开、关闭和搜索slash已采。源slash打开modal并聚焦；产品slash转自有搜索地址。
- self accessibility adaptation：search/burger focus-visible 1.6px solid rgb94/94/116 offset1.6px；不可声称其为已采来源focus态。无虚构hover背景或动画。
- languageControl复用已有LanguageSwitcher；父层负责语言和状态。其宽度使搜索框长度区别于源帮助/登录组合，明确适配，不比较整顶栏所有子项绝对宽度。

## Content / assets / responsive
- 所有自有文字由父层传入；source占位“Search 50,000+ companies”替换为真实SEC目录文案，不许诺全球覆盖。
- 复用Fiscal Jakarta/Mono变量；只有上述真实SVG，不新增远程素材/依赖。
- 1440窄侧栏左偏移80；768/390左0；1023/1024实际确认切换。选择形状与子节点相对几何验收，中英/短窗口另验。
- 现有路由/全局CSS不修改。npx tsc --noEmit后中文commit；合并后build，产品接线后再浏览器QA。
