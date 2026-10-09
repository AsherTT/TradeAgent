# 07_前端与部署

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
