# R1 本人研究记录变化：实现与验证

日期：2026-10-09，Asia/Shanghai。对应正式计划BE-01、FE-03、QA-01；[规格](R1_RESEARCH_CHANGE_SPEC_20261009.md)先于实现，不新建待办清单。

## 实现固定点

- 主仓da96256→02801e8：feat: 增加本人研究记录的有界历史变化投影。
- 主仓02801e8→802db09：fix: 在历史比较解析前排除缺少时区的旧记录。
- 实际前端edd38c5→523a4f3：feat: 在公司页接入本人研究记录变化与报告入口。
- 当前main/master分支，保留既有dirty资料与.test-output；未push、迁入apps/web或部署。

公司详情新增research_change，与研究列表分页独立。先按本人账户/公司/结束状态过滤，再取created_at、ID降序的50条窗口，第51条只判has_more；相同问题、期限、时间/回放/采集模式且截止时间严格更早才选择previous。未结束/取消/失败不用于变化；未知快照/差值为null。每份快照仅安全摘要、时间、质量、门槛、准入证据ID去重数和已记录缺口去重数；证据准入复用既有公司/时间/来源规则，无原文、state_json或内部元数据。

公司页增加真实章节锚点、中英文窗口/未知原因、两次报告本地入口和覆盖差值；沿用原会话失效机制。这里只完成本人研究记录变化，不等同财务/论点历史、真实PIT来源证明、市场表现、公司评分或收益。门户变化聚合以及R2/R4完整领域变化保持待补，BE-01/FE-03仍部分完成。

## 验证

| 边界 | 最终结果与限制 |
| --- | --- |
| 后端普通套件 | 474 passed，1 live_model deselected，89.70%覆盖；未调用真实模型/供应商 |
| 工程标准 | Ruff通过；strict mypy检查106个backend.app文件通过，不把它描述成测试文件也通过mypy |
| 新账户HTTP | 18项：分页独立、真实记录差值、证据准入/去重、不同问题/期限/模式、重复/未来/无时区时间、非结束状态、未知null、账户隔离、窗口外匹配及旧混合时间回归 |
| red→green | 新字段缺失、公司区块缺失先失败；审查发现仅cutoff无时区/UTC requested_at的旧记录不在当前页时导致TypeError，单项先失败，修复后通过 |
| 前端完整检查 | 31行为/SSR检查、0 skipped；包含新增4实际React页面回归、旧会话与BFF/轮询/首页/语言检查；lint/typecheck/默认Turbopack生产构建通过 |
| 本地真实PG/BFF | 合成新账户，通过新增字段、空历史、no-store；脚本自身会话退出，无研究提交/worker/模型/外部工具调用 |
| 浏览器页面 | 合成账户查看既有目录公司；中文1440/768/390与英文390截图，中文clientWidth=scrollWidth为1425/753/375；桌面中文及英文手机已查看，英文warn/error为空；available两记录由离线HTTP与实际React DOM核验，未向真实PG伪造结束任务 |
| 关闭后恢复 | 应用意外关闭中断退出检查，本地API/预览及Docker服务停止；恢复API/预览并经已安装Docker CLI重启原postgres/redis容器，复用原卷，未迁移/重置/启用worker；服务健康后私有公司地址回登录确认退出保护。临时脚本/凭据删除 |

前端证据在D:/桌面/ai-website-cloner-template/docs/design-references/r1-change-20261009/，含4张截图、measurements.json与README。新字段无需schema迁移，没有修改真实.env或用户已有关注/任务。

## 同一R1流程的定向双轴复核

沿用原r1_delta_standards和r1_delta_spec代理，只审da96256→02801e8及edd38c5→523a4f3新差异，规格轴再定向复验802db09；没有新启动整阶段code-review。

### Standards

0项必要修复，无应强制重构的smell。

### Spec

1项P2，旧无时区cutoff可能在完整域验证时先与UTC requested_at比较，导致整个新增窗口读取失败。read_change_state在域验证前排除缺时区/无效时间，不猜测时区、不写旧记录、不放宽其他契约。原代理通过真实HTTP复验关闭；未关闭0项。

## 来源与P10所在步骤

Simply既定portfolio/demo目标初次导航/绑定超时，随后读到引导弹窗；探索演示并关闭注册提示后取得Holdings默认DOM、15条表格、章节导航、图表/FAQ/页脚以及1958元素计算样式初样。没有注册来源账户、接受条款或绕过验证。

来源输出隔离在前端docs/research/simplywall-st-1b042a47/portfolio--demo-128b5e04/，DOM原始JSON以gzip保存。请求1440×1000，实际DOM754×523，截图394×2382且右侧截断；viewport与文档化CDP诊断未恢复可靠来源尺寸。样本不是有效三尺寸基线，全部页签/滚动/菜单/其他状态、媒体库存和完整组件spec仍待补，buildersReady=false。来源演示金额/评分/回报不进入自有账户；首版仍不做真实组合/收益/筛选。Apple公司尚无完整有效样本，Fiscal/Quartr代表页也未完成。

P10仍在R1“产品入口与公司门户”的功能补齐与来源采样/页面复查步骤。本有界记录变化已完成；后续仍需来源完整规格→视觉实现→自有接入后全状态/1440/768/390对照→效果认可，才进入R2多期财务。测试数不作为整体完成百分比。
