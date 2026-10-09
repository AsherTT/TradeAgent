# 源码持久化与远程同步验证

本轮对应用户2026-10-10“扫描Docker与本地/GitHub遗漏并补齐”要求；规格见[SOURCE_SYNC_SPEC](SOURCE_SYNC_SPEC_20261010.md)。

## 遗漏原因与恢复

- 主仓原main领先origin/main 43个提交；前端在独立模板目录，master为60e6316，且未设置远程。主仓apps/web原来只有说明文件。源码未统一维护和及时push是主要缺口。
- 只读扫描五个Python应用容器；运行中的API没有源码挂载，加载/workspace中的构建快照。比对当前本地和全部Git历史后，仅beat旧快照有两个无法逐字匹配历史的源码变体；差异已被当前版本修正，保留补丁作为审计记录，不反向覆盖。详细统计见[恢复档案](../06_验证与审查/源码同步恢复_20261010/README.md)。数据卷、缓存、环境变量均不入库。
- 531个前端tracked文件逐文件完整迁入apps/web，初始字节全部一致。未合入前端分支/孤立builder提交均为master中已有patch，无额外遗漏。旧目录和两个完整Git bundle保留。清单保存初始哈希及整合后的9个文件差异，包锁、原skill、许可和资产保持。
- apps/web现在是唯一维护入口；四个OUTPUT_PLAN及恢复/进度入口已修订。未建立嵌套Git仓库。来源整页、/app布局重构仍未完成，此次迁移不改变P10/R1资格。
- 只重建43个未发布线性提交的消息，其中7条早期英文消息改为中文，保留树、作者、日期和GitHub已发布祖先。备份分支audit/pre-source-sync-20261010只留本地，不推送；[提交映射](UNPUSHED_COMMIT_MAP_20261010.json)保留旧验证记录的可追溯性。后续正常快进推送，不需强推。

## 本地验证

- 新目录npm ci离线锁定安装成功；npm run check通过ESLint、TypeScript和Next生产构建，原10个page路径完整保留。
- npm test：35通过，1项需预览URL的SSR测试条件跳过；新目录生产预览3118单独运行该项，通过。合计原36项全部通过，预览已停止，既有3107预览未操作。这是行为/SSR验证，不代替来源视觉QA。
- Ruff通过；mypy 106文件通过；pytest排除live_model后486通过、1项被排除，覆盖率89.65%。没有启动模型、worker、beat或迁移。
- 根GitHub CI补后端检查及apps/web锁定安装/check/test/生产预览双语SSR检查；Azure补前端安装/check/test。云端运行结果须远程实际执行后确认。
- 后端Docker上下文排除前端和.test-output；Ruff排除来源研究生成器所在apps/web，pre-commit遵循该边界。已知来源资产/截图允许超过默认500KB，但最大仅2,070,322字节，其余文件大文件门槛保留。
- 常见私钥/令牌模式扫描未命中。最终入库前检查gitlink、真实环境文件、依赖及构建输出；真实.env、node_modules、.next、.test-output均不入库。

## 定向审查与同步

原R1 code-review仅对本轮迁入/路径/配置增量做一次Standards和Spec复核；此前产品功能不重复全量审查。发现与修复及远程HEAD核对结果在完成后补录。

后续开发顺序保持：Fiscal搜索及导航等缺失来源状态采样→完整小组件spec→隔离builder与检查→来源路径装配和三尺寸视觉/交互对照→方案B的/app工作台适配及自有接口对照。R2财务、行情与估值等能力仍按开发计划依赖推进。
