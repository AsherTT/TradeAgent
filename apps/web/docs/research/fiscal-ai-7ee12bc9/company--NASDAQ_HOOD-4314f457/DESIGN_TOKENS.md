# 实测基础（未冻结运行基础）

逐元素证据为 `*-chrome.json.gz`，CSSOM 为 `shell-assets-and-css.json.gz`。下列值属默认深色状态；主题和 hover 未实测，不据此猜造其他状态。

| 元素 | 已观察计算值 |
| --- | --- |
| body / 侧栏背景 | `rgb(28, 28, 33)` |
| 正文字体 | `"Plus Jakarta Sans", sans-serif` |
| 侧栏默认文字 | `rgb(255, 255, 255)` |
| 搜索输入背景 | `rgb(44, 44, 53)` |
| 手机已选 Analysis / 关闭按钮背景 | `rgb(64, 64, 79)` |
| 顶部注册按钮背景 | `rgb(34, 149, 73)` |
| 页头 | fixed，64px 高；桌面 left 80px，手机/平板 left 0 |
| 桌面侧栏 | fixed，80px 宽；标签 11px / 17.05px，图标按钮 44×44 |
| 顶部搜索 | 36px 高，14px 字号，32px 圆角，桌面 padding `0px 34px` |
| 手机抽屉搜索 | 42px 高，16px，12px 圆角，padding `0px 14px 0px 40px` |
| 顶部注册按钮 | 30px 高，12px / 600，32px 圆角，字距 1px |
| 侧栏动画 | transition-property `transform, top, height`，duration 0.2s；两端矩形已采，缓动详见原始样式 |

CSSOM 包含 `@media (min-width: 1024px)` 和 AppShell 的 `@media (max-width: 63.9937em)`；临界视口交互仍待实际核验，三宽度默认采样不代表断点全状态。

## 本地字体

实际格式为 TrueType，不以 `.woff2` 伪装；字重来自归档 Google CSS，接入时隔离到 Fiscal 容器。

| 字体/权重 | `public/sites/fiscal-ai-7ee12bc9/shared/fonts/` 文件 |
| --- | --- |
| DM Mono 400 | `38f8abefb8f8.ttf` |
| DM Mono 500 | `4da63a1b968e.ttf` |
| Plus Jakarta Sans 400 | `43adbc7c773e.ttf` |
| Plus Jakarta Sans 500 | `f2374e6da2f0.ttf` |
| Plus Jakarta Sans 600 | `0ee86126fb55.ttf` |
| Space Grotesk 500 | `56632cca6632.ttf` |

不覆盖 Simply 全局字体/排版，不直接注入来源整站 CSS。续开发已创建隔离字体、9个来源图标、默认基础CSS和来源类型，未导入产品页；见 `FOUNDATION.md`。未知主题/hover仍不实现。
