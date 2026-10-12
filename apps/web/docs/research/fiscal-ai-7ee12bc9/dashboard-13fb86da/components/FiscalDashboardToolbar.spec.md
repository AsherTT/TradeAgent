# FiscalDashboardToolbar Specification

## Overview
- Target同namespace FiscalDashboardToolbar.tsx + .module.css。
- Screenshot同source-dashboard三尺寸；SOURCE_controls_desktop_20261012.json与frame完整样式。
- 复用source Add companies输入、read-only pill与Connect操作形状；自有过滤/计数/动作代替指标、券商与来源组合，不复制这些业务。

## Contract / DOM
- Named props metrics:readonly {label:string;value:string|number}[], actions:ReactNode, search?:{id:string;label:string;value:string;onChange:(value:string)=>void}。
- div.toolbar > div.row > optional div.inputWrapper(label sr-only + div.surface(searchSVG + input)) + div.actions；div.metrics > span.pill > span。
- input native type=search id+aria-label/maxLength64，controlled；无网络/异步/Provider。actions由父层真实Link/button传入。
- 把input native属性及事件留可用，原生删除/输入/快捷键保留。source readonly或弹层指标行为不移植。

## Source computed shapes
- row flex/width100%/gap4px；source两输入、source mobile隐藏大工具栏，本版单输入+真实actions，移动wrap/输入全宽是明确适配。
- surface36px/min-height36、box-sizingborder-box、positionrelative，bg28/28/33，radius24px/border0，padding5.5px12px5.5px34px；fontJakarta14px/21.7px/400/white。
- input displayblock/width100%、height22.4px、border0/backgroundtransparent/padding0/margin0，font14px/16.1px/400/white；nativefocus由自有surface focus-within outline1.6 rgb94 offset1.6。
- searchSVG18×18/stroke2/round，circle11/11/r8与line21/21/16.65/16.65；absolute slot左0/宽34/居中，color175/175/182。
- metrics flex-wrap/gap10px（从source stack xs），pill inline-flex/center，height22px，padding0 9.6px（source原有删除按钮，本版无删除右补同padding为适配），radius16000px，border0，bg64/64/79/color216/217/223，font12px/12px/400；label block/line22px。
- actions flex/aligncenter/gap4/wrap。a/button均realnative，height30/min-height30、inline-flexcenter、box-sizingborder-box、padding0 9.33333px、border.8transparent、radius24、font12px/12px/600/white、bg64/64/79，nowrap/cursorpointer。
- actions [data-primary=true] 按Connect源bg rgba56/217/169/.15、color195/250/232；原图标/New标签省略为适配。disabled opacity.5/cursor default与focusoutline为自有状态，不虚构sourcehover。

## Content / states / assets / responsive
- Source labels Add companies or ETFs、Market Cap/Daily % Chg./Stock Price/P/E、Connect brokerage；产品真实labels/values父层传入，pending/error计数不得显示虚假0。
- 只保留实测默认形状；原指标删除/过滤菜单/ownership/currency/可编辑持仓/券商不属本轮。搜索事件用于现有本地目录，完整产品空/加载/错误另验。
- fonts既有Fiscal变量，无新远程素材；SVG上述实测原形。
- 1440/768同行、小屏wrap并输入占全宽；不硬编码两source输入的绝对宽度或来源业务栏高度。
- 只改两个指定文件，npx tsc --noEmit、中文commit、无push。
