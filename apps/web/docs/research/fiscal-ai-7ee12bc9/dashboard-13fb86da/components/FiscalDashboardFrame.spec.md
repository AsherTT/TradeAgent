# FiscalDashboardFrame Specification

## Overview / DOM
- Targets同namespace FiscalDashboardFrame.tsx/.module.css，来源三尺寸frame.json及source-dashboard截图。
- Named FiscalDashboardFrame({tabs:ReactNode,children:ReactNode,footer?:ReactNode})：div.root > div.tabContainer(tabs) + children + optional div.footer。
- Named FiscalDashboardPanel({id:string,labelledBy:string,hidden:boolean,toolbar?:ReactNode,children:ReactNode})：section roletabpanel/id/aria-labelledby/tabIndex0/hidden > div.stack > div.card > optional div.toolbarSlot + children。
- 因AccountShell已有main，本Frame用div避免nested main。panel保留挂载，CSS [hidden]{display:none}，不能被displayblock覆盖。

## Source styles
- root flex/flex-directioncolumn/width100%/min-heightcalc(100dvh-64px)/padding-top10px；fontFiscalJakarta16px/24.8px/400/colorwhite/bg28/28/33。
- tabContainer width100%/padding0 16px。Tabs自己管理43.6高及底10margin，不能重复padding或gap。
- panel margin/padding0/displayblock；stack flex-column/gap12px/alignstretch；card flex-column/relative/overflowhidden/radius8px/box-sizingborder-box、padding16px12px，>=768 padding16px。
- toolbarSlot margin-bottom16px（来源顶工具stack真实margin-md）。card无额外border/shadow或max-width。
- source页底Saved portfolio条80及main bottom150属于来源组合管理；本版不复制、不预留不存在的固定空栏。自有footer padding16px、color175、font12px/18.6/normal wrap，无来源商业声明。
- panel focus-visible outline1.6pxrgb94offset-1.6自有a11y适配。

## States / assets / responsive / behavior
- wrapper只渲染，无状态/network/globalCSS；隐藏语义、各panel IDs由父层契约决定。
- 桌面/768 card16px，390左右12，tab左右16不变；公共壳64/80由已有AppShell负责，不重复偏移。
- Source复制只公共Summary框架，其他source内容受限；父层自有状态/复制替换明确登记，不冒称整Fiscal Dashboard产品复刻。
- 文案/内容由props传入；字体复用既有，无新资产。动态正文height由数据决定，不硬编码来源样本547.3等高度。
- 在前三组件合并后独立builder/tsc/中文commit，主任务merge/build/产品接线QA。
