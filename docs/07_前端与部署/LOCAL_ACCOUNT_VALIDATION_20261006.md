# 本地账户开发验收（2026-10-06）

后端功能提交：`8b590f7d6120f5dd1fc4429a52baf1b1e9a78972`；前端最终代码：`d50728e01b0ff1c208bbe4bbb5f9f934fe113def`。当前前端在 `D:/桌面/ai-website-cloner-template`，后端在本仓库。

## 自动检查

- 后端 Ruff 全仓通过，Mypy 103 文件通过；完整 Pytest：445 passed、1 skipped，覆盖率89.92%。跳过的是已有、需要外部条件的live gate测试，没有调用付费模型。
- 前端 `npm.cmd run check`：ESLint、TypeScript、Next生产构建通过。路由包含 `/login`、`/register`、`/app`、`/api/backend/[...path]`。
- 前端9项Node测试通过：两种本地Origin、非法Origin、内部研究路径拒绝、后端不可用、cookie转发、请求大小、云Origin和原有双语回归。
- 页面转换脚本在换行归一后重复执行，16个组件文件哈希保持不变；账户入口、账户CTA与中文翻译保留。两个仓库代码diff格式检查通过。

## 实际PostgreSQL与浏览器

本地数据库为PostgreSQL18.6，已有0014迁移升级到0015_local_accounts，保留既有业务数据和持久化卷。未使用SQLite作为运行数据库。

`scripts/qualify-local-accounts.py`经本地Next同源代理与实际API/PostgreSQL验证：注册成功、HttpOnly/SameSite cookie、密码哈希与会话摘要真实存储、刷新续会话、跨账户关注隔离、退出撤销、重新登录、服务端过期拒绝，以及不可信Origin/内部研究路径拒绝。探针在finally中仅清理自己创建的两项专用账户及其关联数据。

浏览器验证了首页登录与注册入口指向本地；注册进入工作台，搜索KLAC、关注后刷新仍保留；错误密码提示、正确登录与退出均正常；中文/英文标题、标签和提示可切换。独立浏览器测试账户无管理员权限，结束时已退出。页面从现有instrument表读取开发测试公司，界面明确说明不是实时行情。

正常桌面及390px移动尺寸均检查；登录页clientWidth/scrollWidth为390/390，工作台为375/375（存在纵向滚动条），无横向溢出。临时尺寸覆盖已还原。截图位于同目录 `account-preview-20261006/`。

## Standards

独立审查初审2项：新增账户样式未遵循Tailwind与移动优先约定；SSR元数据和客户端标题重复维护。已移除新增自定义CSS，改用移动优先utility classes；抽出共享标题表，服务端与语言切换复用。复核还指出按钮覆盖类冲突，已使用既有cn/tailwind-merge处理并再次通过前端构建。

独立复核剩余可行动项0；未发现后端硬性标准违规。账户关注使用永久instrument_id身份。

## Spec

独立审查初审1项：底部CTA与导航仍保留来源站账户/方案文案。已统一为创建TradeAgent账户，将永久免费表述替换为个人关注管理说明，并同步生成脚本和中英文。

独立复核剩余可行动项0；没有发现已定义范围中的遗漏、范围扩张或功能错误。

审查计数：Standards初审2、已关闭2、剩余0；Spec初审1、已关闭1、剩余0。两轴均无剩余最高严重项。

## 配置与开发边界

本地页面：`http://127.0.0.1:3107/login`、`/register`、`/app`，API监听本机8000端口。退出后访问工作台会进入登录页。开发服务保留运行。

云配置准备了统一DATABASE_URL、数据库TLS、HTTPS Origin与Secure cookie校验。没有连接云数据库、上传数据、发布网站或迁移本地数据。具体步骤见[本地与云配置](LOCAL_ACCOUNT_SETUP_20261006.md)。

Google/Apple、邮件验证、找回密码、研究提交与完整报告页面、历史研究归属及公网部署仍需后续开发。旧研究/RAG接口未通过网页代理开放。本次完成账户与个人关注这组前后端闭环，不代表全部原站功能均已接通。
