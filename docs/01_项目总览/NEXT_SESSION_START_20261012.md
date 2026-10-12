# 下一会话开发入口 — 2026-10-12

最新续开发：公共应用壳 `e8c6e85` 已装配整个`/app`，顶栏/侧栏/抽屉通过中英三尺寸、断点、短窗口、焦点与真实导航验收；52项前端测试/check通过，新增固定diff两轴0项。先读[公共壳验收](../07_前端与部署/R1_APP_SHELL_VALIDATION_20261012.md)及[唯一任务表](DEVELOPMENT_PLAN.md)。下一块冻结门户正文来源规格→关注/活动任务/最近研究/变化/目录接线；随后公司→研究列表/提交→任务状态/预算/取消→报告/引用及账户→R1整站验收，再R2。已完成壳和选定来源状态不重做，下面旧检查点不能恢复为更宽前置。

仓库：`D:/桌面/Trade/TradeAgent`。如新会话工作目录是`D:/桌面/Trade`，下列仓库相对路径前加`TradeAgent/`。唯一前端维护入口为`apps/web`，旧独立模板只作历史。

续开发检查点：`c89675f`已接正式SEC搜索清空条，前端check/49项测试及新增diff定向两轴0项；见[清空增量验收](../07_前端与部署/R1_SEARCH_CLEAR_VALIDATION_20261012.md)。来源普通query无该按钮，产品非空query显示为明确适配；不要重复开发或将47页模式提前。下面阅读顺序与R1剩余→/app路线保持。

## 按顺序读取

1. [正式待办与下一步](DEVELOPMENT_PLAN.md#下一会话交接检查点2026-10-12)：唯一任务状态表；P10/R1未完成、R2未启动。
2. [方案2最终定义及P10之后路线](../07_前端与部署/DEVELOPMENT_EXECUTION_OPTIONS_20261012.md)：已选方案，无需重新选型。
3. [最新进度](DEVELOPMENT_PROGRESS_20261008.md)与[实现状态](IMPLEMENTATION_STATUS.md)：优先顶部2026-10-12记录，较早文本仅历史。
4. [整体架构](../02_架构与契约/ARCHITECTURE.md)、[前端架构](../07_前端与部署/FRONTEND_ARCHITECTURE.md)、[股票投研后端补充](../02_架构与契约/EQUITY_RESEARCH_BACKEND_EXTENSION_20261009.md)。
5. [公司发现实现契约](../07_前端与部署/R1_COMPANY_DISCOVERY_20261012.md)、[最新手验](../07_前端与部署/R1_MANUAL_VALIDATION_20261012.md)、[增量审查闭环](../07_前端与部署/R1_COMPANY_DISCOVERY_REVIEW_20261012.md)。
6. [Fiscal身份/概览clone验收与spec索引](../../apps/web/docs/research/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/COMPANY_IDENTITY_VALIDATION_20261012.md)，按具体下一组件继续读取source namespace中的OUTPUT_PLAN/BEHAVIORS/spec，避免重采已验收状态。

## 实施入口与约束

下一可做增量按正式计划：冻结/app门户正文来源规格并接既有接口→公司/研究/任务/报告/账户逐页接线验收→R1整站出口。公共壳与选定搜索/Simply有界状态已验，不重做；仍未采的商业/受限状态明确排除。不能把全部商业公司报告/全球目录提前为R1必做，也不能用黑色背景、通用卡片、lab或首屏冒称整站1:1。

先读[apps/web/AGENTS.md](../../apps/web/AGENTS.md)与[clone-website skill](../../apps/web/.agents/skills/clone-website/SKILL.md)，执行来源采样/spec/隔离builder/build/三尺寸状态对照完整流程。每个大阶段code-review一次；本R1已审查，后续仅检查新增固定差异，不因换会话重复全阶段。commit正文中文、正常push，不强推。模型/worker/beat仍关闭；发现身份不等于研究准入或报价/财务资格。

本轮代码检查点`9418123`已推送，[云端检查通过](https://github.com/AsherTT/TradeAgent/actions/runs/38238128605)。handoff整理只更新文档；交接文件按skill保存在系统临时目录，不复制到仓库。

运行状态需新会话重查：3107前端和Docker api/postgres/redis在交接时运行，不保证之后持续在线；不得因服务暂时停止而改业务源码。浏览器绑定、子代理及工具会话句柄不能跨新会话复用。
