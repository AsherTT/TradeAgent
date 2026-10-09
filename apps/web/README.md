# TradeAgent 前端

本目录是当前前端源码与后续开发的唯一维护入口，已从本地ai-website-cloner-template的60e6316完整迁入。原目录保留作历史备份；后续修改、审查和提交都在本仓库完成，避免代码只留在独立预览目录。

Node.js使用根目录.nvmrc指定的24系列版本，依赖沿用package-lock.json。从TradeAgent根目录执行：

```powershell
npm.cmd ci --prefix apps/web
npm.cmd run dev --prefix apps/web -- --hostname 127.0.0.1 --port 3107
```

访问 http://127.0.0.1:3107 。后端地址见.env.example，本地FastAPI默认为 http://127.0.0.1:8000 。真实配置只保存在未提交的环境文件中。

```powershell
npm.cmd run check --prefix apps/web
npm.cmd test --prefix apps/web
```

已有首页、账户、关注、公司与有界研究页面及独立来源组件均保留；Fiscal控制台、完整财务和Quartr原文核验仍待开发，迁入不等于P10验收或生产部署。来源原样素材和未接入组件边界以docs/research/和根项目开发计划为准。

复刻继续严格运行 [.agents/skills/clone-website/SKILL.md](.agents/skills/clone-website/SKILL.md)，保留逐组件规格、隔离builder、构建和真实来源对照流程。AGENTS.md中的模板基础规范仍适用，当前迁入位置以本说明和根项目进度为准。

模板MIT许可见 [LICENSE](LICENSE)，原始说明见 [TEMPLATE_README.md](TEMPLATE_README.md)，字体许可与素材出处保持原位置。迁入清单见 [FRONTEND_IMPORT_MANIFEST_20261010.json](../../docs/07_前端与部署/FRONTEND_IMPORT_MANIFEST_20261010.json)。
