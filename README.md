# EasyTradeAgent — P1–P9 后端基础

当前分支：`feature/dev-EasyTradeAgent`。从 main 的 `59bdebe` 创建，后端与设计文档以正式前端开发前的 `f568b37` 为核对基线。

本分支保留原 P1–P9 的契约、模型网关、数据库/队列、证券身份与公司行动、研究图、证据/论点/预测、安全检索、回放评估、确定性量化/回测/风控。历史模拟验证不代表全部真实数据或模型资格已具备；完整边界见[后端检查点](docs/01_项目总览/P1_P9_CHECKPOINT_20261003.md)和[架构](docs/02_架构与契约/ARCHITECTURE.md)。

旧前端源码、复刻素材、门户/账户/公司发现后端增量、对应迁移及开发方案均已移除。新的前端范围和参考网站等待用户需求，当前不预先制定方案。main 的源码和构建配置仍保留，可在切回后重建原版本。

## 本地检查

Python 3.12，安装开发依赖后检查：

```powershell
python -m pip install -e ".[dev]"
python -m pytest -m "not live_model"
python -m ruff check .
python -m mypy backend/app
```

普通测试不调用真实模型。模型、来源和worker启用仍需原契约规定的独立准入。

## Docker

本分支保留P1–P9的Dockerfile、docker-compose.yml和迁移0001–0014。重建镜像用 `docker compose build`；运行迁移/API或worker前分别核对配置，不自动启动执行器。

切回main后，可用其根目录Compose重建原后端，前端构建配置位于该分支的apps/web。本次从未修改的main提交导出独立上下文，成功构建后端镜像、导入API并检查到0016_account_research迁移头；验证镜像随后也清除。旧容器、镜像、数据卷和构建缓存已按请求清理，数据库与卷恢复备份只保存在本机临时目录。

开发文档入口：[P1–P9 文档导航](docs/README.md)。分支边界：[基线说明](docs/01_项目总览/EASYTRADEAGENT_BASELINE_20261013.md)。
