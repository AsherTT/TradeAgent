# 浏览器站点权限不一致：反馈材料

日期：2026-10-06，Asia/Shanghai。

**最新状态：后续正常浏览器访问已取得截图、DOM 与计算样式，未再返回本文的保存权限禁止拒绝。以下为此前诊断历史，不再要求用户执行文末恢复步骤。部分工具读取仍超时，恢复机制及超时根因未确定。** 最新开发见 [采样检查点](CLONER_CAPTURE_CHECKPOINT_20261004.md)末节。

## 可复现现象

在 Codex 桌面应用内置浏览器，通过正常浏览器工具打开 `https://simplywall.st/`，访问在加载页面前被安全检查拒绝。

工具返回的关键原因：

```text
A saved user permission setting blocks this action.
Browser use cannot access https://simplywall.st because the user has a saved preference that blocks it.
```

## 已核对事实

- 用户最新截图显示：设置 → 浏览器 → 智能体权限，`https://simplywall.st` 的“浏览”和“下载”均为“始终允许”。
- 截图中的默认“浏览”和“下载”也均为“始终允许”。不需要进一步扩大权限来排查。
- 2026-10-06 只读检查本机配置，确认 `browser_use.origins["https://simplywall.st"].access = "allow"`。
- 用户在聊天中明确授权公开页面采样。
- 建议重启后进行了再次验证，仍返回同一拒绝；最新截图后再验证也被同一原因拒绝。
- 本机应用安装包版本记录：`OpenAI.Codex_26.930.2377.0_x64`。
- 未绕过安全检查、未换浏览器访问被阻止来源、未开启完整 CDP、未改写隐藏审批状态。

## 尚未确认

界面与配置允许该站点，但浏览器安全检查仍将其视为保存的禁止项。具体原因尚未确定，不能将缓存、权限同步故障或应用缺陷作为已确定根因。

## 反馈请求

请排查此站点在浏览器安全检查中使用的权限来源，以及该来源与设置界面、本机 `browser_use` 配置之间的同步或优先级差异。希望提供清除冲突记录或恢复正常审批的正式操作入口。

建议用户自行通过应用 `/feedback` 提交本现象并附设置截图。本文没有被自动发送给任何第三方。

来源采样和开发现状见 [采样检查点](CLONER_CAPTURE_CHECKPOINT_20261004.md)。桌面来源资料已保留，完整响应式和交互采样仍未完成。

## 官方文档与后续只读诊断

再次经正常工具访问仍被同一安全检查拒绝。随后检索并打开以下官方文档：

- [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)：`access = "allow"` 只允许继续正常审批和策略检查；同一来源有多条匹配规则时采用更严格值，管理员与用户策略中的禁止均可能阻止访问。
- [配置层级](https://learn.chatgpt.com/docs/config-file/config-basic)：用户、项目、配置档和系统层分别参与配置读取。
- [管理员策略](https://learn.chatgpt.com/docs/enterprise/managed-configuration)：Windows 系统要求文件位于 `%ProgramData%\OpenAI\Codex\requirements.toml`。
- [App Server](https://learn.chatgpt.com/docs/app-server)：可通过 `config/read` 和 `configRequirements/read` 只读检查配置与要求。
- [浏览器排查](https://learn.chatgpt.com/docs/chrome-extension#manage-allowed-and-blocked-websites)：移除禁止记录后可再次请求授权。

只读检查结果：

1. 本机系统 `requirements.toml` 不存在；用户的 `managed_config.toml` 不存在；当前工作目录及其祖先没有项目 `.codex/config.toml`。
2. 用本机已安装的 Codex 运行独立的短时只读诊断进程：`configRequirements/read` 返回 `requirements: null`；配置层仅用户与系统两层，未发现浏览器禁止规则。
3. **本次最新读取的用户配置已没有 `browser_use` 表，独立进程读出的对应配置为空。** 这与较早读取到站点 `access = "allow"` 的记录属于不同时间的状态，不能把旧记录当作当前值。没有修改配置文件。
4. 独立进程的结果不代表桌面当前会话或所有服务端策略快照，不能据此排除所有权限来源。诊断进程已关闭，没有启动研究、模型推理或浏览器访问。

## 尚未执行的恢复步骤：重置站点记录并重新授权

只读检视当前安装包的 `browser-use-policy-site-permissions-a750092ac842.js`，确认站点行的删除操作针对该来源移除各权限类别的 `allowed` 和 `denied` 记录，并移除该来源的自定义配置。它不是删除浏览器历史、账号或项目文件。该实现事实不能证明全部策略缓存会同时刷新，也不保证修复成功。

请用户在现有设置界面完成：

1. “默认”行的“浏览”改为“需要批准”，使之后可以正常请求授权。
2. 点击 `https://simplywall.st` 行右侧垃圾桶，并确认移除自定义权限。
3. 保持该站点行已移除的状态，返回当前聊天告知完成。
4. Agent 经正常浏览器权限检查重试；若出现授权弹窗，由用户选择“允许此网站”。若仍被拒绝，停止来源访问并保留诊断。

此步骤是通过应用正式设置入口恢复正常审批，不涉及改写隐藏状态、关闭安全检查或通过其他方式访问被阻止网站。当前尚未执行，问题尚未解决。

## 后续正常访问观测

用户要求继续后，在同一内置浏览器刷新现有来源页，正常工具的截图和 DOM/计算样式读取成功，完成三种宽度默认状态采样及三份真实媒体下载。未使用另一浏览器、远程 HTTP 下载或原始 CDP 绕过。

页面正常打开与工具调用超时同时存在；部分有界字符串表达式成功，部分其他调用超时。这只能说明本次观测，不证明所有访问方式已恢复，也不能确认为序列化、缓存或权限故障。字体素材批次失败为 `TypeError: Failed to fetch`，并非保存权限禁止拒绝。历史恢复建议现已被本次成功采样事实更新，无需再让用户重复设置。
