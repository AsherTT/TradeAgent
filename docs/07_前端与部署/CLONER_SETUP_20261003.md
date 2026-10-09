# ai-website-cloner-template 准备记录

- 开始日期：2026-10-03；最终验证：2026-10-04，Asia/Shanghai。
- 用户指定位置：`D:\桌面\ai-website-cloner-template`。
- 当前状态：**源码已克隆，依赖安装完成，规范、类型、生产构建及开发 HTTP 验证通过。**

## 来源与版本

- 来源：`https://github.com/JCodesMore/ai-website-cloner-template.git`。
- 固定提交：`f50066df3f4bdca057d3b239be6f49f17724bb13`。
- 模板版本：`0.5.1`。
- Node：`v24.21.0`；npm：`11.19.0`，满足项目 `node >=24`。
- 已核实 `nvm current` 为 `v24.21.0`；`node.exe`、`npm.cmd`、`npm.ps1` 均位于 `C:\nvm4w\nodejs`。沿用现有 nvm 环境，没有切换 Node 或全局升级 npm。
- 已有 npm 缓存位于 `D:\Tools\npm-cache`；本次未更改全局 npm 配置。
- 按 README 的独立项目设置移除了 `origin`；基础提交和上游地址保留在本记录。
- 执行规则：模板 [AGENTS.md](D:/桌面/ai-website-cloner-template/AGENTS.md) 和 [clone-website skill](D:/桌面/ai-website-cloner-template/.agents/skills/clone-website/SKILL.md)，均已读取；检查指南亦已读取。
- 依赖以模板原有 `package.json` 与 `package-lock.json` 为准，不做版本升级。

## 安装与验证

首次 `npm ci --no-fund` 因 npm 下载连接重置失败。随后使用相同锁文件、已有缓存和较低网络并发重试，未改变系统 npm 配置：

```powershell
npm.cmd ci --prefer-offline --no-audit --no-fund --maxsockets=4 --fetch-retries=4 --fetch-retry-mintimeout=1000 --fetch-retry-maxtimeout=10000 --fetch-timeout=120000
```

- 网络重试仍遇到大包停滞后，停止本次安装及下载进程，保留缓存。从 npm 镜像获取相同版本的 Next 和 Windows SWC 大包，二者均通过原锁文件 SHA-512 校验，再加入现有缓存。
- 最终通过 `npm.cmd ci --offline --no-audit --no-fund` 安装，新增 620 个包；`package.json` 与 `package-lock.json` 保持不变。本轮未运行完整依赖审计。
- 规范、类型、生产构建：初始模板和本地字体修复后均通过 `npm.cmd run check`。
- 原始生产启动：`npm run start` 返回 HTTP 200；上游配置为 `output: standalone`，生产部署应按 Next 文档使用 standalone server，本轮未改部署配置。
- 开发启动：`npm.cmd run dev -- --hostname 127.0.0.1 --port 3107` 验证通过；页面、实际 CSS 和两种字体均为 HTTP 200，脚手架内容符合预期。
- 验证用服务器完成后关闭，后续开发可以重新启动。
- 浏览器：已确认 Codex 内置浏览器工具可连接；原站视觉采样与截图验收另在复刻任务中执行。

## 协同工作方式

模板项目保持独立，具体复刻任务在其目录执行自身 skill；TradeAgent 后续接收经过验证的适配代码。当前模板的 `src/app/page.tsx` 为未复刻的原始脚手架。

已确认方案与尽量一比一复刻要求见 [V2-B 设计基线](FRONTEND_DESIGN_V2_B_BASELINE.md)。本准备记录不代表任何来源页面已复刻完成或后端功能已联调。

## 本地环境修复

原模板使用 `next/font/google` 加载 Geist 与 Geist Mono。开发首次请求因 Google 字体下载超时导致 500；保留字体本身，改用 `next/font/local`。

- 修改范围：模板的 `src/app/layout.tsx` 和新建 `src/app/fonts/`。
- 字体来源：初始成功生产构建实际生成的两种 Latin 可变字体；字号体系和现有字体变量保留。
- 保留 SIL Open Font License 1.1 与来源说明。
- 修复后完整检查再次通过，开发模式页面、样式和字体资源均正常加载。
- 这是模板启动修复；来源站的真实字体仍须按复刻 skill 实测提取，不以模板字体替代。

## 重新启动

```powershell
Set-Location -LiteralPath 'D:\桌面\ai-website-cloner-template'
npm.cmd run dev -- --hostname 127.0.0.1 --port 3107
```

开发入口：`http://127.0.0.1:3107`。核查命令：`npm.cmd run check`。
