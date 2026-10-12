# 07_前端与部署

> 最新交接入口（2026-10-12）：[下一会话索引](../01_项目总览/NEXT_SESSION_START_20261012.md)、[SEC公司发现契约](R1_COMPANY_DISCOVERY_20261012.md)、[最新手验](R1_MANUAL_VALIDATION_20261012.md)及[定向审查闭环](R1_COMPANY_DISCOVERY_REVIEW_20261012.md)。Fiscal身份/概览已按严格clone流程替换通用目录布局，正式搜索为真实SEC目录；完整/app与选定来源剩余状态仍待。不是整商业页或P10验收完成。

> 2026-10-12最终执行入口：[方案2最终定义、P10出口与网站后续路线](DEVELOPMENT_EXECUTION_OPTIONS_20261012.md)。用户已选择逐功能区同步交付，现有/app整站逐页重构；完整来源商业报告不再是R1前置，任务状态仍唯一维护[开发计划](../01_项目总览/DEVELOPMENT_PLAN.md)。

> 当前主工作台为用户确认的方案B（Fiscal式股票投研控制台），保留[增强A](FRONTEND_DESIGN_ENHANCED_A_20261008.md)的来源还原、统一身份与跨区域约束；已认可Simply首页保持，Quartr负责阅读。前端唯一维护入口为主仓apps/web，旧V2-B及独立目录记录为历史。

> 当前开发入口（2026-10-10）：按[开发计划与待办](../01_项目总览/DEVELOPMENT_PLAN.md)继续首版研究平台；[前端架构](FRONTEND_ARCHITECTURE.md)明确Simply门户、Fiscal财务、Quartr阅读的路由/接口与验收。下文采样摘要和历史资料不代表当前产品已完成或仍等待用户选型。账户与研究基础的已验收范围见[2026-10-07记录](ACCOUNT_RESEARCH_VALIDATION_20261007.md)。

**历史准备摘要（2026-10-03～06）：** 前端范围与进入条件。当时用户选择V2-B并要求使用模板项目复刻；这些选择和独立目录安装记录按历史保留。当前以方案B和2026-10-10迁入apps/web的源码入口为准，P11未部署。

[返回文档总导航](../README.md)

## 文档清单

| 阅读内容 | 文件 |
| --- | --- |
| 最新已确认方案：增强 A 的保留范围、体验统一与后端条件 | [FRONTEND_DESIGN_ENHANCED_A_20261008.md](FRONTEND_DESIGN_ENHANCED_A_20261008.md) |
| 最新首版范围、开发计划与任务ID | [DEVELOPMENT_PLAN.md](../01_项目总览/DEVELOPMENT_PLAN.md) |
| 三来源融合、路由/模块/接口与可见验收 | [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md) |
| 已选方案2最终范围、R1～R6与P10之后路线 | [DEVELOPMENT_EXECUTION_OPTIONS_20261012.md](DEVELOPMENT_EXECUTION_OPTIONS_20261012.md) |
| 真实SEC公司发现、缓存/身份/接口边界 | [R1_COMPANY_DISCOVERY_20261012.md](R1_COMPANY_DISCOVERY_20261012.md) |
| 最新产品搜索/自有详情及来源对照手验 | [R1_MANUAL_VALIDATION_20261012.md](R1_MANUAL_VALIDATION_20261012.md) |
| 本轮新增差异Standards/Spec及修复闭环 | [R1_COMPANY_DISCOVERY_REVIEW_20261012.md](R1_COMPANY_DISCOVERY_REVIEW_20261012.md) |
| 源码统一、GitHub同步、审查与云端CI验收 | [SOURCE_SYNC_VALIDATION_20261010.md](SOURCE_SYNC_VALIDATION_20261010.md) |
| Fiscal最新采样与待补状态 | [R1_FISCAL_SOURCE_CHECKPOINT_20261009.md](R1_FISCAL_SOURCE_CHECKPOINT_20261009.md) |
| 历史V2-B：来源分工与复刻要求 | [FRONTEND_DESIGN_V2_B_BASELINE.md](FRONTEND_DESIGN_V2_B_BASELINE.md) |
| 模板准备：固定版本、安装与验证结果 | [CLONER_SETUP_20261003.md](CLONER_SETUP_20261003.md) |
| 来源采样：实测基调、已归档素材与当前权限阻塞 | [CLONER_CAPTURE_CHECKPOINT_20261004.md](CLONER_CAPTURE_CHECKPOINT_20261004.md) |
| 浏览器权限冲突：已核对证据与可提交的故障说明 | [BROWSER_PERMISSION_DIAGNOSTIC_20261006.md](BROWSER_PERMISSION_DIAGNOSTIC_20261006.md) |
| Simply Wall St 融合：三个整体方案对比（历史提案） | [FRONTEND_DESIGN_OPTIONS_V2.md](FRONTEND_DESIGN_OPTIONS_V2.md) |
| 方案 C：整体基调、逐页参考分工与 SaaS 演进（历史提案） | [FRONTEND_DESIGN_C_V1.md](FRONTEND_DESIGN_C_V1.md) |
| 前端开发策略与分阶段准入 | [FRONTEND_STRATEGY.md](FRONTEND_STRATEGY.md) |

当前源码入口：[apps/web](../../apps/web/README.md)；[源码同步规格](SOURCE_SYNC_SPEC_20261010.md)。设计/采样历史不能替代当前开发计划或来源验收。
