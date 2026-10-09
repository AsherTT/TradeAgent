# 账户研究工作台接续（2026-10-07）

从登录后的 `/app` 进入 `/app/research`，搜索数据库公司、提交受限研究，打开 `/app/research/{runId}` 阅读状态、取消和报告。任务地址可刷新恢复。UI中英文，正文沿用后端原文；空指标、未知费用、证据不足和不完整报告保持明确。

后端需要迁移 `0016_account_research`，本地API8000，前端3107。仅通过同源账户BFF访问；真实会话、Origin、路径/方法、预算和所有权均由服务端校验。公司查询仅转发query。内部研究/RAG/论点路径未开放。

完整模型研究默认关闭，资料采集LLM预算为0；本次未启用真实模型worker和付费调用。浏览器截图为明确的合成验收数据，不代表真实市场/完整分析资格。临时账号已退出清理。

检查：lint、typecheck、build通过；13项Node测试全部通过（含实际3107双语SSR）；独立Standards复审和Spec复审均无剩余问题。

后端完整验收、两轴审查及截图见 `D:/桌面/Trade/TradeAgent/docs/07_前端与部署/ACCOUNT_RESEARCH_VALIDATION_20261007.md`。运行代码审查固定基准 `cfc6e48ecb529c0c7533110df33a4d28ed26cf16`，最终运行代码HEAD `141b0a47271538499f743a66df5602374dc1efc4`。实现提交ff73608、修复提交141b0a4；后续仅文档交付。

本地预览：http://127.0.0.1:3107/app/research（需要登录）。沿用master，未push、未部署，本仓库无remote。下一阶段先核对供应商资格和预算，再开启受限执行。

```powershell
npm.cmd run check
$env:LOCALIZATION_PREVIEW_URL='http://127.0.0.1:3107/'
node.exe --test scripts/*.test.mjs
```
