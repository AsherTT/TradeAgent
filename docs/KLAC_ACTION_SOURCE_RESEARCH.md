# KLAC 公司行动一手来源调研（2026-10-01）

## 结论与现有门槛

免费一手来源能交叉核实 KLAC 的具体拆股与现金股息，但本次没有取得一个能证明 **当前完整价格窗口内全部行动、包括无事件期间均已覆盖** 的完整记录源。因此不能将 `yfinance-actions-observed-v1` 从 `UNVERIFIED` 升为 `ACCEPTABLE`，也不能把 SEC 财务接入完成当作市场质量已经合格。

仓库要求来自 `docs/KLAC_CURRENT_QUALIFICATION.md`、`docs/YFINANCE_QUALIFICATION.md`、`docs/ADR/ADR-0007-security-master-corporate-actions.md` 和 `docs/provider_quality/yfinance_actions_observed_v1.json`：独立金例、行动完整性、身份与期间一致性、`available_at <= analysis_timestamp`、版本化资格及最差质量传播。历史严格回测还要求可证明的历史发布时间。本文仅调研与提出方案，不改变资格报告或实现。

## 可核实的事件

| 事项 | 已核实字段 | 一手证据与限制 |
| --- | --- | --- |
| 2026 年拆股公告 | 10:1；record 06-04；06-11 收盘后生效；首个拆后交易日 06-12 | [SEC 2026-05-07 8-K](https://www.sec.gov/Archives/edgar/data/319201/000119312526212093/d116682d8k.htm)。公告为预期安排，不能单独证明最终实施。 |
| 拆股实施确认 | 已于 06-11 实施 10:1；年报股份与每股数追溯调整 | [SEC FY2026 10-K](https://www.sec.gov/Archives/edgar/data/319201/000031920126000027/klac-20260630.htm)，Item 5 与年报说明。该年报是后续确认，不能放回 5 月历史截止之前。 |
| 独立拆股日期核对 | ex-distribution/effective 06-12；payable 06-11；record 06-04；10:1 | [OCC memo 58941](https://infomemo.theocc.com/infomemos?number=58941)，2026-05-11。OCC 对其期权调整拥有直接权威，但备忘录附有摘要准确性/完整性免责，并不是 KLAC 全部股息与公司行动总账。 |
| 最新现金股息 | 08-06 宣布；普通股每股 USD 0.23；record 08-17；payment 09-01 | [SEC 8-K EX-99.1](https://www.sec.gov/Archives/edgar/data/319201/000119312526338242/d165938dex991.htm)。文本没有显式 ex-date 字段，不能把 payment 或 declaration 误写为价格调整日。 |

以上字段为原文事实；下述日期窗口、资格方案与完整性判断是工程推论或设计建议。按 2026-10-01 日期减 60/90 个**自然日**，窗口起点分别为 2026-08-02/2026-07-03，均晚于 06-12，且均包含 08-17 股息日期。真正请求必须以实际时区、截止时间和 lookback 定义重新计算；60/90 个交易日会得到不同起点，可能跨越拆股，不得套用这个结论。

## 免费入口的可靠性差异

1. [KLA IR Dividends](https://ir.kla.com/stock-data/dividends) 是发行人的正式入口，文字明确表示提供股息历史。本次网页文本提取没有出现可核对的历史数据行。它证明入口存在，不证明动态表的完整返回，更不能将未提取到的行解释为没有股息。后续应采集浏览器实际表或公开正式下载，留存原始响应与行数，核对支持的日期范围和数据供应方。
2. [Nasdaq KLAC Dividend History](https://www.nasdaq.com/market-activity/stocks/klac/dividend-history) 本次读取显示数据暂不可用；页面说明历史股息不做拆股调整、可能合并普通/特别股息，并提示部分数据来自合作方 Quotemedia。域名属于交易所不等于该页面的每个字段都是交易所原始公告。不能用空表证明无事件，也不能把未来动态读取成功当成历史 PIT 数据。
3. [Nasdaq Trader Ex-Date](https://www.nasdaqtrader.com/Trader.aspx?id=nasdaq-ex-date) 说明正常 T+1 股息 ex-date 为 record date，页面主要公布例外情形。本次页面呈现无结果，但没有完成指定窗口查询及覆盖验证，不能声称 KLAC 没有例外或没有股息。
4. [Nasdaq T+1 官方提示 ETA2024-29](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2024-29) 说明 2024-05-28 开始 T+1、正常股息一般同日。由此可以**推断**普通现金股息通常在 2026-08-17 除息；这不是 KLAC 的事件级 ex-date 证明。应取得发行人历史表或交易所事件记录确认后再入适配器。[FINRA Rule 11140](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140) 也区分普通、小额分配、大额分配与延迟信息，禁止使用无条件 record-date 规则。
5. SEC 与 KLA IR 中的同一新闻稿是同一发行人事实的两种载体，不算两个独立事实源。SEC 保存的 accession 和提交元数据有利于追溯，但枚举所有 8-K 仍不能凭空取得行动总账完整性承诺。10-K 覆盖其披露期间，无法证明之后截至 10-01 没有新行动。

## 可实施的窄范围资格方案（尚未达成）

建议单独开发 **KLAC 当前窗口行动核对**，而不是改写 Yahoo 全局资格。先限定普通股、USD、当前非严格研究、明确自然日区间、最多 90 天；窗口外、其他标的、未知行动类型、源失效或身份歧义均保持现有拒绝行为。

1. 为来源建立独立版本，记录 instrument/CIK/CUSIP、窗口、原始来源 URL、抓取时间、内容摘要哈希、发布/提交时间、字段依据、事件总数、支持类型及覆盖声明。不得只记录已发现的正例而宣称零遗漏。
2. 从发行人完整股息历史取得金额、ex/record/payment/declaration 日期，并取得覆盖整个窗口的拆股/其他生命周期行动记录。与 SEC/OCC 正例及 Yahoo 的观察事件逐项比较；多事件、缺行、未知类型、金额或日期不一致、分页不完整、页面不可用必须失败关闭。完整性若只能人工审查，应有明确范围、到期日及审查记录，且只能称该范围人工审查通过；不得宣称获得来源保证。若仍无完整性依据，就不授予资格。
3. 建立真实独立金例：06-12 10:1（包含日期边界）、08-17 USD 0.23（取得明确 ex-date 后）、拆前/拆后单位、缺失事件、额外事件、不可用空表、范围外请求、重复/修订、未来发布、未知生命周期事件。普通合成 fixture 只能验证逻辑，不能替代来源真实资格。
4. 检查行情的价格含义。`auto_adjust=False` 不足以单独证明供应商全部历史 OHLC 未做拆股重标；跨 06-12 时须用独立拆前交易价格金例核对，避免再除以 10。当前窗口虽全在已知拆股之后，仍须证明窗口内没有未覆盖的行动。
5. 核验后再决定是否引入组合来源的独立报告及缓存版本。原 `yfinance-actions-observed-v1` 保持 `UNVERIFIED`；成功范围与组合来源的资格单独命名并传播，不能仅换 report quality 常量绕过质量门。

备选是单独设计“来源观察价格”展示：保留 Yahoo 原始取得的数值与 `UNVERIFIED`，不输出合格技术结论或完整分析。新价格模式需要明确规范和审查；不能用它悄悄满足现有市场基线或 strict 门槛。

## 当前研究与历史 PIT 的边界

当前研究可将新采集完整核对材料的观察时间作为保守 `available_at`，并在采集后冻结截止。这样的资格只对本次当前研究范围成立。今日抓取的历史表、后续年报以及后续修订不能被设成当年 event date 的历史可见记录。

历史 PIT 需要保存当时可见的版本、SEC acceptance/交易所公告时间、时区与更正关系；只有日期精度时必须选择保守可见边界，不能声称 intraday 资格。即使具体拆股公告发布时间可核实，也不能由一个事件推出整源历史完整性。P9 仍受来源资格限制，P10 的进入条件也不会因本文研究自动满足。

## 本次调研产物与未完成项

本次仅保存上述一手链接和事实，未下载原始来源归档，未执行动态表/API 完整范围查询，未修改代码或质量报告。下一步的最小外部材料是：可读取的 KLA 股息历史行、KLAC 事件级 ex-date、完整窗口行动覆盖依据。获得前应继续显示 `insufficient_evidence`；可以并行完成 SEC 财务流程与模型路径的实现和验证。

## 发行人动态股息表加载追踪（2026-10-01 补充）

直接读取 [KLA 股息入口](https://ir.kla.com/stock-data/dividends) 获 HTTP 200。HTML 使用 `data-qmod-tool="dividends"`，参数为 KLAC / en，公开 webmaster ID 为 93303，环境 app，版本 v1.12.0。来源链由该页面声明，而非猜测第三方接口。

[页面指定的 qmodLoader.js](https://qmod.quotemedia.com/js/qmodLoader.js) 根据上述配置加载 [v1.12.0 dividends.js](https://qmod.quotemedia.com/static/v1.12.0/dividends.js?cs=v1.12.0)。公开代码可核对：

- 工具名为 `Dividends`；先按 webmaster ID 与工具名 SHA-256 调用 `auth/g/authenticate/dataTool/v0/` 的正常工具授权，再携带返回工具 token 调用 `datatool/getDividendsBySymbol.json`。token 不是静态 HTML 数据，不应写入仓库或日志。
- 请求默认 `limit=1500`、`start=1969-01-01`、`end=当前日期+10年`。页面以结果中的 `date` 区分未来/历史；客户端 DataTable 每页 10 行，含 ex-date、amount、frequency、payment、record、announced、type 列。页码只是在同一返回结果上分页，不能仅读取首页就声称取得历史总表。
- 字段映射与请求结构只证明工具支持这些列及最大返回数，尚未证明 KLAC 实际行数、事件日期、币种或历史完整性。

此次按脚本明确流程、未带用户凭据的工具授权返回 `NotAuthorized`（响应 code.value=100）；未取得 token，未请求数据端点。没有伪造站点来源头、绕过授权、注册账号或改变配置。浏览器工具 inventory 同时为空，IAB 报不可用，因此本会话不能补做正常浏览器渲染验证。

公开页面与脚本临时归档在 Windows Temp 的 `klac-dividends-page.html`、`klac-qmod-loader.js`、`klac-qmod-dividends.js`。没有股息 JSON capture 或已渲染行，因此**仍无完整历史行，也没有事件级明确 ex-date 的新证据**。这些归档只是调查过程材料，未作为可复现来源 fixture 提交；工具接口与授权规则可能变更，后续应从页面重新追踪。

KLA 的发行人公告可核实分红决定；其嵌入表实际由 QuoteMedia 加载。即使表读取成功，也应标作“发行人网站展示的 QuoteMedia 观察数据”，不能标作交易所独立确认或发行人自建全行动总账，且不能由显示行或未显示行推出窗口内无未报事件。
