# 容器源码比对与恢复记录

2026-10-10只读复制五个应用容器的backend/alembic/项目配置，逐文件与本地HEAD及全部本地历史比对（仅归一化CRLF）。不复制真实.env、数据库、Redis、运行缓存或模型配置。

正在运行的API：201文件与本地一致，一份门户研究变化测试是已提交的旧版本。三个旧迁移/worker容器各119文件相同、38文件可在Git历史找到。停止的beat容器79文件相同、44文件有历史对应，另外两处特有变体与a25278017270高度接近，差异归档在本目录patch。

旧workflow用字符串rag-guard-v1替代SCANNER_VERSION，旧测试将UUID类型放宽为object；当前本地代码采用扫描器版本常量和明确UUID类型。没有需要覆盖当前运行后端的遗漏功能，两处旧差异仅作为恢复证据保存，不能导入运行代码。Docker diff显示运行容器修改为yfinance缓存，beat为/tmp调度文件；源码并非最近在容器内改写。

完整只读提取及两个Git bundle备份留在本地忽略目录.test-output/source-sync-audit-20261010，不推送运行数据。比较统计和patch可在GitHub核查。
