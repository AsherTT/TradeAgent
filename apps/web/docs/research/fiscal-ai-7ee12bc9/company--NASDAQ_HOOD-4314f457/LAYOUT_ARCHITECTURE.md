# 来源拓扑与布局检查点

本次为公开公司 Overview，并非登录后的 Holdings 门户样本；提供方案 B 的控制台壳与公司上下文，账户门户内容另行采样/映射。

```text
AppShell
├─ fixed Sidebar（桌面80px；手机/平板离屏抽屉）
│  ├─ Fiscal logo / version
│  ├─ Main：Dashboard / Analysis / Charting / Screener / Query / Earnings / Fund Letters / Resources
│  └─ Account：Settings / Updates（手机另有 Help Center / Dark mode / 注册）
├─ fixed Header（64px，搜索 / 帮助 / 注册 / 小屏菜单）
└─ Main（桌面左偏移80px，上偏移64px）
   ├─ Company identity / exchange-symbol / price / actions / event
   ├─ 10 个内部页签（小屏横向滚动）
   └─ Overview body
      ├─ Company Overview / Statistics
      ├─ Bulls / Bears / source
      ├─ What's happening / Earnings
      └─ Price chart / periods / tools / footer
```

桌面内容从 y≈205.8125 开始，两栏并排：左资料内部滚动、右图表；左滚动容器高 756、scrollHeight 2541。768/390 为整页单列，图表在 Company Overview 前，不未经核验复用桌面顺序。tabs 为 Overview、Financials、Investor Relations、Research、Estimates、News、Ownership、Industry、Modeling、Filings，目前只观察 Overview。

| 来源区域 | 现有 TradeAgent 对象/路由 | 后续 |
| --- | --- | --- |
| 主壳/搜索 | `/app`、目录、关注分页 | 全状态采样后本地导航，未实现功能不伪装可用 |
| 公司身份/研究 | `/app/companies/[instrumentId]`、预选研究 | 稳定证券 ID、本人关注与研究上下文，不只用 ticker |
| 财务/行情/估值 | 当前有限财务契约 | R2 期间/报价/股本资格，界面还原不授予数据能力 |
| Research / 阅读 | 研究列表、`/app/research/[runId]` | R3 原文核验、R4 完整研究，不跳原站代替实现 |
| 账户/语言/主题 | 自有登录注册、统一语言入口 | 保留自有契约，来源登录提示不覆盖本地账户 |

先完成壳及公开区域全状态规格，分组件还原，再接既有数据。完整来源未装配前，不建空壳源路由或登记门户完成。
