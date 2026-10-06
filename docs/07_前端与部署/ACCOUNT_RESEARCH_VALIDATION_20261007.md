# 账户研究闭环：本地验收与接续

日期：2026-10-07，Asia/Shanghai。对应规格：[ACCOUNT_RESEARCH_SPEC_20261007.md](ACCOUNT_RESEARCH_SPEC_20261007.md)。

## 实现结果

登录后从工作台进入 `/app/research`，搜索数据库中的公司，给出问题、期限和预算，提交并打开持久任务地址。本人最近50项任务支持状态、取消、刷新恢复和报告阅读。详情展示执行步骤、预算用量、质量门槛、缺口、原始证据及时间；指标沿用后端投影，缺失值和未知费用保持明确。

账户归属与研究任务同事务写入。不同账户、历史未归属任务、未知任务均不可读取或取消。旧内部研究接口拒绝操作账户所属任务，网页代理只开放明确的账户路径/方法。每账户 request_id 唯一，同内容重试不重复派发；内容冲突409。数据库行锁保护并发重复；每账户最多3项活动任务。队列失败保留本人可见的失败记录。

完整模型研究由 `ACCOUNT_RESEARCH_MODELS_ENABLED` 控制，默认关闭。本次不启动真实模型worker、不调用付费模型；资料采集强制模型调用预算为0。未改真实 `.env`，未重置数据库或数据卷。旧内部接口的公网隔离与真实供应商资格仍需独立验收。

## 自动验证

| 检查 | 结果 |
| --- | --- |
| 后端完整 pytest | 452 passed，1 skipped；覆盖率89.66%，项目要求80% |
| Ruff：backend / scripts | 通过 |
| Mypy：项目默认配置 backend.app | 104个源文件通过 |
| 前端 lint / typecheck / build | 全部通过，研究列表与动态详情路由生成成功 |
| 前端 Node 测试及本地双语SSR | 13 passed，0 skipped |
| PostgreSQL / BFF 验收 | schema 0016_account_research；并发幂等、冲突、跨账户和旧接口隔离、刷新、未知费用、持久取消通过 |

新增7项账户研究测试通过HTTP边界验证权限、输入与预算、活动上限、幂等、队列失败、历史隔离和预算耗尽。最后一项从账户提交进入真实离线 `execute_research_run`，外部模型适配器若被调用就让测试失败；结果为0模型调用、insufficient_evidence和不完整报告，归属仍可读取。SQLite仅用于隔离测试，不作为运行时数据库替代。

前端代理测试覆盖仅转发账户cookie、Origin、8KiB流式读取限制、超时/后端错误、精确路径方法和仅允许公司的query参数。双语SSR检查实际访问本地3107，未跳过。

曾临时把Mypy目标扩大到整个backend（含现有测试），出现测试文件类型诊断；最终按仓库配置的backend.app范围验证。本记录不声称全部测试文件通过静态类型检查。

## 浏览器与本地数据库

已在本地3107/8000和真实PostgreSQL验证：

- 中文及英文桌面、390×844手机布局，手机内容宽度375与页面宽度375一致，无横向溢出。
- UI实际提交资料采集任务，展示持久任务ID，取消后刷新/返回仍为终态。
- 报告章节、空指标原因、未知费用、完整性提示和证据锚点；报告正文保持后端原文。
- KLAC公司代码搜索、无结果提示及继续搜索恢复；非法UUID在中英文显示独立提示。

截图目录：[research-preview-20261007](research-preview-20261007/)。包括列表、报告的桌面/手机双语版本及非法ID提示。截图中的账号、公司目录和报告使用明确标注的测试数据：OFFLINE FIXTURE合成来源，不是实际新闻采集或完整投资分析的证明。

验证脚本 `scripts/qualify-account-research.py` 使用随机命名空间的两个临时测试账号，真实BFF提交4个并发同内容请求，确认只有一个任务。验证后取消任务，删除这些测试账号、会话和归属，保留已取消的持久任务终态，让已有队列重投正常结束，避免缺失记录无限重试。

浏览器预览临时账号已退出并清理，预览身份文件已删除；保留2个已取消测试终态。随后默认资格脚本再次通过。用户账号和历史记录未清理。

## Standards

两仓库独立代码规范复审均通过：硬性违规0，可操作Fowler smell 0。首轮前端发现1项非阻断Duplicated Code，ResearchRun的3处401处理已统一为expireSession；修复后独立复审确认关闭。

## Spec

两仓库独立规格复审均通过：后端0、前端0剩余发现。首轮3项P2已关闭：公司搜索覆盖目录、非法编号区别于404、资格脚本保留队列终态。提交成功后保持按钮禁用、查询参数白名单及离线worker测试均在原规格范围内。

审查固定基准为后端 `de911878207c6e2a5003dba5918a33c9d72f3095`、前端 `cfc6e48ecb529c0c7533110df33a4d28ed26cf16`。最终运行代码审查HEAD为后端 `18290536803c1d22eb0f5a9a0f3ce7c315f926dc`、前端 `141b0a47271538499f743a66df5602374dc1efc4`；后续交付提交仅增加本记录、接续说明与截图。

## 提交与继续开发

本地提交：后端 `eb22b5e`（实现）及 `1829053`（修复/测试）；前端 `ff73608`（实现）及 `141b0a4`（修复/测试）。当前分支沿用后端main、前端master；未push、未部署，前端仍无remote。既有README等dirty文档原样保留，未混入提交。

预览：[研究工作台](http://127.0.0.1:3107/app/research)，需要登录。浏览器已退出测试账号并恢复普通桌面尺寸。

下一阶段需要先取得真实数据源与模型预算资格，再决定开启受限worker和模型研究。本地此轮只证明账户边界、预算/队列持久性、离线执行与报告显示，不证明真实市场或完整分析资格。现有集中push门槛不变。

复验（后端目录）：

```powershell
.venv/Scripts/python.exe -m ruff check backend scripts
.venv/Scripts/python.exe -m mypy
.venv/Scripts/python.exe -m pytest backend/tests -q
.venv/Scripts/python.exe scripts/qualify-account-research.py
```

复验（前端目录，服务需在3107运行）：

```powershell
npm.cmd run check
$env:LOCALIZATION_PREVIEW_URL='http://127.0.0.1:3107/'
node.exe --test scripts/*.test.mjs
```
