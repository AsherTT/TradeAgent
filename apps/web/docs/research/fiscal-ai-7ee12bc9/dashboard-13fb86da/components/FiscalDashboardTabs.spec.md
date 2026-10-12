# FiscalDashboardTabs Specification

## Overview
- Target src/components/sites/fiscal-ai-7ee12bc9/dashboard-13fb86da/FiscalDashboardTabs.tsx + .module.css。
- Screenshot source-dashboard-desktop/tablet/mobile-20261012.png同截图namespace。
- Evidence SOURCE_*_frame.json, SOURCE_tab_hover_20261012.json, SOURCE_performance_login_gate_20261012.json。
- 来源Summary/Performance/News/Markets；只复刻公共页签形状，受限来源正文不复制。产品四页签及可用内容为已授权契约适配。

## Contract / DOM
- Named export FiscalDashboardTabs props items:readonly {id:string;label:string}[], activeId:string, onChange:(id:string)=>void, idPrefix:string, label:string。
- div.viewport > div.list role=tablist aria-label=label > button typebutton role=tab > span.label。
- id `${idPrefix}-tab-${id}`，aria-controls `${idPrefix}-panel-${id}`，aria-selected active，tabIndex active0其余-1。
- 仅组件内键盘focus refs，无网络/Provider/路由；click调用onChange。Left/Right循环、Home/End聚焦首尾，Enter/Space原生激活；聚焦目标scrollIntoView nearest，可选链便于JSDOM。manual activation为自有a11y适配。

## Computed styles
- 由父Frame提供外padding-inline16px，不重复padding。viewport width100%, min-width0, overflow-x:auto；隐藏自身scrollbar为可访问性适配，不写全局。
- list display:flex, flex-direction:row, justify-content:flex-start, align-items:normal, gap:10px 4px, padding4px0, margin0 0 10px, width:max-content/min-width100%, nowrap；自然高43.6px。
- button flex row/center/center，positionrelative/z0，box-sizingborder-box，padding10px16px，border.8px solid transparent，radius4px，cursorpointer，white-space:nowrap；Jakarta14px/14px/400/white，bg44/44/53。自然height35.6。
- active bg64/64/79、font-weight500；label block/14px/line14继承weight，margin/padding0。transition无时长（computed all）。
- 真实Performance:hover仍bg44/44/53、weight400，无变化，不造hover色/动画。
- focus-visible自有outline1.6px solid rgb94/94/116 offset1.6；不冒称来源focus已验。

## States / content / responsive
- 默认/active/inactive/真实hover已采；来源Performance点击打开登录且Summary保持active，受限正文未验。
- 文案全部父层传入，中英；源字体文件已在shared/fonts.ts。N/A新图片/视频/SVG。
- 1440/768/390 buttontoken相同，小屏自然横滚，不能wrap成两排或改成select；未知源scrollbar全部状态不计1:1。
- 只改两个目标文件，npx tsc --noEmit、中文commit、无push。主任务merge/build/QA。
