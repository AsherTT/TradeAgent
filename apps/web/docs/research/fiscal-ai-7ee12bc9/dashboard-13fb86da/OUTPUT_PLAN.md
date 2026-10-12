# Dashboard门户正文输出计划 — 2026-10-12

Source https://fiscal.ai/dashboard/，v6.0.2；主维护 apps/web，site-key fiscal-ai-7ee12bc9、page-key dashboard-13fb86da（SHA256('/dashboard/')）。用户已要求按既定方案2继续/app门户正文，这是对已存在/app的明确更新授权；保留首页、登录/注册、公司/研究/报告及所有lab/来源命名空间。产品落点/app，来源证据不作为真实业务数据；不覆盖来源其他pathname。

本轮来源范围：Summary默认父布局、主页签形状、紧凑输入/操作/pill形状、表格容器/header/cell/公司标识及三尺寸。Performance点击实际触发Login/Signup且Summary仍选中；受限正文/新闻/市场/收益/持仓成本/券商/自定义资产/拖动/可编辑财务/指标选择/保存组合不在自有门户范围。不得把来源默认组合数据写进产品，不新建证券或资格。

仅追加components namespace中的FiscalDashboardTabs/Toolbar/Table/Frame和完整小spec。现有Fiscal字体与图标复用，0远程下载；公司产品无logo的26px代码fallback为自有适配。CSS全部局部，公共壳与首页不变。AccountShell新增fiscal外观仅用于Workspace，其他页原外观保持。

产品四页签：Following/我的关注、Active research/活动研究、Recent research/最近研究、Company directory/公司目录。数据仍来自原portal/companies认证请求与轮询，保留本人研究变化、窗口/分析截止时间/未知值、分页、刷新、关注取消/注销、迟到401清空与稳定内部href。切换视图只改展示，四panel保留挂载但hidden不参与访问；切语言/视图保留query、分页和状态。账户信息放可展开区域，#account仍可到达；邮箱/退出可查看，不在门户标题中重复邮箱。

Actions与长文字、计数、无障碍、产品状态为明确适配：不伪造源Performance图/真实组合等价性，不放不会工作的排序/拖动或Brokerage按钮。研究问题/证据缺口不能用source ticker缩略规则隐藏。测试继续实际挂载UI与HTTP/router seam，source形状用真实浏览器核对；R1未完成/R2未启动，模型/worker/beat关闭。

顺序：采样/三个控件spec→隔离builders→逐次合并build→父布局builder→产品装配→中英三尺寸与实际状态/安全检查→一次新固定diff定向两轴复核/修复→中文提交/正常push。任务状态只维护DEVELOPMENT_PLAN.md。
