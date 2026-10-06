# 本地账户开发与云数据库配置

前端仍在独立预览项目 `D:/桌面/ai-website-cloner-template`；真实账户和关注接口、迁移在本TradeAgent仓库。网页通过同源代理调用FastAPI，没有远程认证服务或运行时SQLite回退。

## 本地入口

- 注册：http://127.0.0.1:3107/register
- 登录：http://127.0.0.1:3107/login
- 工作台：http://127.0.0.1:3107/app（未登录会回到登录页）

使用自己的开发邮箱创建账户，密码12–128字符。当前邮箱仅作为账户标识，没有声称已发送或验证邮件。没有默认管理员账户；浏览器验证创建的`preview-20261006@example.test`仅为无特权测试账户，验证结束已退出。

账户、scrypt密码哈希、会话令牌的SHA256摘要、关注记录保存在本地PostgreSQL的`tradeagent`数据库。会话原始令牌只通过HttpOnly、SameSite=Lax cookie交给浏览器，默认有效7天；退出撤销当前会话。密码和会话不放localStorage，也不保存明文。数据库连接禁用参数日志输出。

新增表：app_user、account_session、auth_throttle、user_watchlist。迁移0015_local_accounts追加表，保留既有研究数据。Compose的postgres_data卷负责本地持久化，停止容器不会等于删除数据卷。

## 服务重启

当前前端、API、PostgreSQL、Redis已运行。需要重启时，在TradeAgent目录依次启动Docker Desktop、执行：

```powershell
docker compose up -d postgres redis
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

另外在独立预览项目运行：

```powershell
npm.cmd run dev -- --hostname 127.0.0.1 --port 3107
```

已有服务在端口上运行时不重复启动。无需启动会执行模型任务的worker来测试账户和关注列表。

本地后端环境配置见根目录.env.example，前端配置见独立预览项目.env.example。AUTH_ALLOWED_ORIGINS使用JSON数组；网页请求的Origin必须在明确列表内。每个邮箱的注册/登录分别限制10次/10分钟，后端连接来源IP限制100次/10分钟，计数保存在数据库；共享代理IP不是最终公网部署的真实客户端IP方案。

## 后续切换云数据库

后端与迁移读取同一DATABASE_URL；配置同一云PostgreSQL后，账户和既有SQL业务数据均使用该连接。示例（凭据仅使用占位符）：

```dotenv
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@CLOUD_HOST:5432/tradeagent
DATABASE_SSL=true
AUTH_COOKIE_SECURE=true
AUTH_ALLOWED_ORIGINS=["https://YOUR_SITE"]
```

前端服务器配置：

```dotenv
TRADEAGENT_API_URL=https://YOUR_PRIVATE_API
TRADEAGENT_APP_ORIGIN=https://YOUR_SITE
```

不要把数据库密码放入NEXT_PUBLIC变量。HTTPS账户来源要求Secure cookie，远程HTTP来源会被配置校验拒绝。内置docker-compose.yml仍是本地基础设施配置，其服务环境将连接指定为本地postgres容器；云部署使用自身环境配置，不能直接把该本地Compose作为云连接验证。

改连接地址不会自动搬迁本地数据。后续需备份/恢复或采用数据库迁移工具搬运，再在云连接上验证迁移版本、用户数、研究记录、关注关系和会话策略。当前没有上传数据、连接云数据库或部署。

## 当前范围

已接通账户、工作台真实公司目录、个人关注新增/删除和访问保护；公司目录目前来自数据库中已有的开发测试记录，不是已接通的全市场实时行情。

既有内部research/RAG/evaluation接口未通过网页代理暴露，未把历史研究自动归属到新账户。Google/Apple、邮件验证、找回密码、完整研究提交/报告页面、计费及公网部署另行开发。公网部署还需按真实代理拓扑与现有内部接口边界进行专项验收。

依据：[OWASP密码存储](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)、[会话管理](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)、[CSRF防护](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)。
