# 方案2第一个收尾项：搜索短窗口

日期2026-10-12，当前P10/R1。方案2最终定义已生效，本轮只修改现有SearchDialogFrame.module.css的.modal两属性，不宣称选定搜索全部状态或/app整站完成。

## 来源与规格

按clone工作流复用既有页面命名空间/字体/组件，重新实测Fiscal公开NASDAQ_HOOD页面v6.0.2的1280×720首次打开搜索。浏览器DOM/计算样式和截图保存为search-short-source-1280x720-20261012.json/png。先更新components/SearchDialogFrame.spec.md的短窗口章节，再修正代码；基础build通过，阅读适用AGENTS和Next本地CSS Modules文档。

来源modal仍overflow:auto/max-height90dvh，自然内容662px、clientHeight648px；color-scheme:dark继承自来源html，scrollbar-width:thin。原实现normal/auto产生浅色15.2px滚动槽，来源薄滚动槽10.4px；本地Card950.8px而来源955.6px。

纠偏仅在.modal设置color-scheme:dark与scrollbar-width:thin，不修改全局Simply样式，不隐藏滚动条或裁剪尾部。中文/英文长度导致自然内容高度不同；不能拿一语言的溢出范围断言另一语言一定有滚动。

## 验证范围

修正后英文1280×720的modal、input、close、card四矩形x/y/width/height共16项与来源差值0，clientWidth990/scrollHeight662也一致。1440×1000、768×1000、390×1000修正前后同四节点几何最大差0；scrollbar/color-scheme样式按本次来源纠偏改变。这只证明父壳范围，不是整页像素或所有搜索状态。

search-short-local-before/after/comparison-20261012.json保存实测值。英文及中文1280×720截图见页面design-references的search-short-local-{en,zh}-1280x720-20261012.png。源码未改变query/category/展开回调；实际Escape退出恢复打开按钮焦点和body overflow，中文重开后AAPL展开36条、37个链接含主公司，验证记录见search-short-behavior-20261012.json。

本次R1审查仅定向核对两个CSS属性及其规格：Standards0、Spec0，未重启全R1阶段skill。npm run check的lint/typecheck/build通过；无后端修改，不重复后端测试或授予真实数据/模型资格。

明确英文1280×720下，PageDown后outer scrollTop13.6px/scrollRange14px，原生外层滚动实际可操作；不是仅由overflow样式推断。其余记录及截图没有改变来源历史数据或实际产品证券身份。

## 开发服务与下一块

检查发现3107及Docker此前已停止，恢复已有前端开发服务和Docker Desktop/API/PG/Redis。Compose启动依赖执行现有迁移检查，数据库仍0016_account_research；没有新增迁移或改.env。models_enabled实测False，worker/beat未启动。

下一块继续选定搜索清空/关闭/焦点状态与Simply已选区块的边界验收，随后/app应用壳/门户及公司概览。完整商业来源页/全球与47页搜索不作为R1前置；未验证区块保留显式缺项，不能提前把整个R1完成。
