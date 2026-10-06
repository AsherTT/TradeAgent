# 本地账户与工作台接口

用户授权：开发自有登录与其他后端；先连接本地PostgreSQL开发调试，之后通过配置切换到云数据库；修正跳往Simply Wall St的账户入口。
固定起点：后端f568b37b0fd957d8ac19402a7138d948b8f69f88；前端fe34910b7c31ee8f6c8768cf5988b9c6168647bd。

- 本次完成邮箱/密码注册、登录、当前用户、退出；Google/Apple、邮件验证与忘记密码不作为已完成能力展示。
- 用户、密码哈希、不可逆会话令牌摘要及个人关注公司保存到PostgreSQL；无内存账户或SQLite运行回退。密码使用随机盐scrypt，强度按OWASP建议；不保存明文密码或原始会话令牌。
- 会话使用HttpOnly、SameSite=Lax cookie，配置有效期，退出撤销服务端会话；拒绝过期、伪造、已撤销会话。修改请求核对Origin；持久化限制登录/注册请求频率。
- 登录后的/app工作台从真实数据库读取当前账户、可关注公司和本人关注列表；支持添加/移除关注且账户之间隔离，未登录不得访问。公司来自现有instrument表，空表明确显示空状态，不制造实时行情或虚假报告。
- 浏览器经同源/api/backend代理调用仅允许的auth/workspace接口。内部研究、RAG等旧接口不通过该代理暴露；本次不声称全研究工作流或多租户SaaS已经完成。
- 首页及所有注册/登录/试用账户入口改为本地/login、/register，已有关注列表及工作台入口使用/app；注册CTA改为TradeAgent账户，生成脚本保持此改动。新页面使用TradeAgent标识、与当前页面协调的样式，并支持中文/英文。
- DATABASE_URL与数据库TLS设置从环境读取；本地Compose保持持久化卷。配置云数据库后账户和业务数据采用同一云连接，不自动迁移现有数据或部署。
- 验证实际PostgreSQL迁移与注册→登录→刷新→关注→退出流程；测试错误密码、重复账户、过期/撤销会话、Origin拒绝、速率限制、跨账户关注隔离、后端不可用状态；完成全套后端检查、前端构建和独立Standards/Spec审查。

密码与会话依据：[OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)、[Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)、[CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)。
