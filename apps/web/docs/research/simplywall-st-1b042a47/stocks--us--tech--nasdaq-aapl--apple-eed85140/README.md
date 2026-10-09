# Apple 公司来源采样

2026-10-09，Asia/Shanghai。R1/FE-03与QA-01继续开发，整页未验收。

本次进入公开公司概览，未遇到机器人验证，未登录或创建第三方账户。只读取公开页面和素材；来源行情、估值、新闻及财务数值是复刻样本，未经自有后台数据资格验收。

## 有效基准

`overview-{desktop,tablet,mobile}-bounded.json.gz`分别保存实测1440、768、390宽度的元素、父节点ID、文字、公开属性、矩形及32项布局样式。元素按250条分块，捕获数量与total一致：3967、3936、3747。SVG完整属性/额外图形见素材盘点；其他CSS属性需要时定向补采，不能把32项称为全部计算样式。

有效全页截图是`overview-desktop-full-calibrated.jpg`（1440×8067）和`overview-mobile-full-calibrated.jpg`（390×11010），已读图确认包含页面右侧、末尾数据来源和页脚。来源桌面DOM总高8071，截图存在4px换算舍入差；移动DOM总高11004，截图存在6px舍入差。不可把该舍入或默认截断图当作缺失分区。

`overview-observed.dom.txt`是公开概览语义样本；`source-css/`是页面link实际观察到的两份公开CSS静态文件，下载未读取任何第三方业务API。

## 尺寸问题的处理

来源viewport请求尺寸与实际页面尺寸约相差1.909倍；截图clip坐标也存在同类换算。校正输入2751×1909、1467×1909、745×1611后，实际DOM为1440×1000、768×1000、390×843；按同一实测比例校正clip才能保留完整宽度。该比例只是本次浏览器实测，未确认根因，不能硬编码为通用浏览器规则。每次必须重新读取实际尺寸并检查生成图片的尺寸/内容。临时viewport在结束前恢复。

最初`overview-observed.jpg`、`overview-desktop-calibrated.jpg`、`overview-desktop-explicit-clip.jpg`是尺寸诊断证据，右侧/下部被截断，不作为组件基准。最初两个`overview-*-observed.json.gz`也有大数组/文本上限；保留诊断记录，后续使用分块基准。一次全属性大型读取返回错误；未使用其结果。

## 素材

页面盘点173个inline SVG，已保存原始markup。实际复制3个图片资源到该页独立public目录：Apple标识、公开用户头像、favicon；格式以响应Content-Type为准，AVIF保持.avif。复用shared/fonts的BureauSans/BureauSerif。ASSETS.json提供来源与本地路径。统计/广告像素、脚本和查询元数据不进入产品。

## 开发边界

OUTPUT_PLAN.json保留Apple源pathname，整页buildersReady仍为false。更新时间表、数据来源、分析模型组件（含行业指标说明）已按规格实现；三尺寸、工程检查和原R1流程新增差异定向复核见[更新时间表验证](components/CompanyDataStatusTable.validation.md)、[数据来源验证](components/CompanyDataSources.validation.md)及[双语与模型验证](components/CompanyBilingual.validation.md)。开发验证页/labs/r1-company-data-status展示这些静态区域并提供中文/English按钮，不称为完整公司详情或自有实时数据；所有现有产品路由和数据权限继续保留。

同日继续补公开分析师三行表，见[分析师来源验证](components/CompanyAnalystSources.validation.md)。当前四个组件/五个静态区域；源站完整85行展开仍受登录提示限制。该lab仅直接预览访问，其他src路由未链接到此地址，也未接自有公司/研究API。用户要求研究工作台先提供三个方案再选择，本轮未改/app布局。

尚缺：平板全页截图、公司滚动/点击/hover/展开/加载等状态、各章节完整spec和实现、接入自有对象后的三尺寸对照。其他公司子pathname未采样，不能用主概览样本宣布它们完成。

新增风险弹窗桌面采样见BEHAVIORS.md。公司页出现登录提示；关闭后仍可读公开概览，但More details后的状态又出现提示。没有机器人验证；没有操作登录、注册或接受条款。操作/测量多次超时留下可读DOM，但缺失的滚动、动画和受限内容继续保留为待办。

本轮平板全页导出768×12737，但读图发现注册/登录提示覆盖，保存为overview-tablet-full-signup-gate-diagnostic.jpg，不能作为默认无弹窗基准。数据来源区域provider链接的真实键盘焦点采样已保存，新增单组件参考及验证图见上方验证记录。
