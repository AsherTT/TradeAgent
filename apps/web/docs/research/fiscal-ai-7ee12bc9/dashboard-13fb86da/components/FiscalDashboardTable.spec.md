# FiscalDashboardTable Specification

## Overview
- Targets同namespace FiscalDashboardTable.tsx/.module.css，命名导出FiscalDashboardTable与FiscalDashboardCompanyLink；两相关subcomponents同一个builder。
- Source source-dashboard桌面/平板/手机截图与SOURCE_*_grid.json、SOURCE_mobile_identity、controls。图标/字体沿用既有，不新增来源数据接口。
- 原11财务列/4组合行供形状采样；产品headers与rows自有安全DTO，不复制持仓/收益/价格/估值，不放无效sort/drag。

## Contract / DOM
- Table props label:string, columns:readonly {id:string;label:string;kind?:"identity"|"text"|"numeric"}[], children:ReactNode。
- div.scroll role=region aria-label=label tabIndex0 > table > thead > tr > th scope=col（column.kind用data-kind）及tbody children。空/加载行由父层真正td colSpan传入。
- CompanyLink props href:string,name:string,symbol:string,exchange:string,logoSrc?:string。真实next/Link aria-label含name+exchange:symbol；div.identityRow > div.logoBox(image或26px代码fallback) + div.identityStack > span.fullName > p.name、p.mobileSymbol、p.desktopExchange、p.mobileExchange。
- 无状态/API/排序/拖动；仅原生Link鼠标/Enter/修饰键和可键盘滚动region。图片eslint定点说明允许原source尺寸，用img alt `${name} Website`、width/height26。

## Source computed styles
- scroll relative/min-width0/max-height75vh、overflow:auto、bg44/44/53、fontJakarta16px/24.8px/400/white。
- table width100%/table-layoutauto/border-collapsecollapse/font20px/28px/400。border-left/right/bottom .8px solid64/64/79；source无border-top；不估来源所有列总宽。
- thead displaytable-row-group/positionsticky/top0/z3/background44/44/53；headrowfont12px/28px。
- th padding4px6px/font12px/28px/700，bg28/28/33/text-alignleft/vertical-aligntop，border-right .8px solid64/64/79。
- tr font12px/28px/400/border-bottom .8px solid64/64/79；even bg64/64/79，odd透明，transitionbackground .1s（不造未实测hovercolor）。
- td padding4px6px/border-right .8pxsolid64/64/79、vertical-alignmiddle、font12px/28px/400，overflowhidden/text-overflowellipsis；ordinary numeric right。内容文字（td直接p或本版直接文字适配）desktop14px/21.7px，mobile12px/18.6px。
- identity th/td positionsticky/left0/z4(header)/z1(body)，bg44/44/53(body)/28/28/33(header)，opacity.97；desktop原left1（因Move列存在），本版无Move列统一left0为适配。min-width30px/max-width200px mobile，>=768 min/max-width350px；source数据行自然44.8mobile/50.8desktop，不能把多行研究缺口硬裁到此高度。
- text kind为自有长文本适配：left/normal whitespace/overflow-wrap:anywhere、min-width280/max-width440，保留问题/证据缺口；numeric nowrap。不固定所有行height或隐藏全文。
- companyLink block/widthfit-content/max-width100%、colorwhite/text-decorationnone；sourceclass hover:underline，产品focus-visible outline1.6rgb94 offset1.6为适配。
- identityRow flex aligncenter/gap4pxmobile、8px>=768；logoBox block26×26/min26、margin-right4px、radius6/overflowhidden。img26×26/object-fitcontain/object-positioncenter；fallback代码无假logo，为自有明确适配。
- stack flex-column/gap0。fullName仅>=768显示，p.name font14px/21.7/400、margin0、3行lineclamp/overflowhidden；mobileSymbol12px/18.6。desktopExchange14px/20.3，仅>=768；mobileExchange12px/17.4。aria-label始终保留完整身份。

## States / content / responsive / assets
- 实测默认/striped、三尺寸及滚动container；source无私有空/失败资格，产品状态独立验。链接返回稳定本地公司/研究地址。
- Source NVIDIA/NVDA/NasdaqGS、Apple/AAPL、Microsoft/MSFT、Amazon/AMZN只作来源证据，不能硬编码产品。既有source四logo可仅参考区域复用，产品缺logo用fallback。
- 768断点公司全名→代码/交易所缩略，small min30；研究长文仍全文，horizontal scroll局部，不能扩大整页宽度。
- 只改两个目标，npx tsc --noEmit/中文commit/无push。source完整组合以及受限功能不计为本轮交付。
