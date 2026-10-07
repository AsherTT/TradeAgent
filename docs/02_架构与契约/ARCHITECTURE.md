# Architecture Baseline

## Current product direction (2026-10-08, Asia/Shanghai)

The confirmed enhanced-A direction keeps the research-platform scope: Simply Wall St portal/company
organization, Fiscal multi-period financial views and Quartr report/source verification,
using TradeAgent contracts and account ownership. Real portfolio/return/dividend tracking
and screening follow later. See the [development plan and backlog](../01_项目总览/DEVELOPMENT_PLAN.md)
and [frontend architecture](../07_前端与部署/FRONTEND_ARCHITECTURE.md) for route/module/API dependencies.

Accounts/watchlists and bounded account-owned research are implemented in the sibling
frontend; the homepage is still a source prototype and the Fiscal/Quartr product work
is incomplete. The earlier pause awaiting user frontend requirements is resolved by
the confirmed scope. Bounded development may continue; complete P5/P10 qualification,
reviewed migration into apps/web, real-provider gates and P11 remain outstanding.
The dated observations below are historical slices; their pause/implementation statements
do not override this current direction or imply that full integration is complete.

## 增强 A 的产品查询与后端补齐（2026-10-08，待实现）

用户已认可保留来源核心页面与内部导航、统一产品身份和操作上下文，并授权依据
公开可观察的功能逻辑补齐研究平台后端。最新[增强 A 设计](../07_前端与部署/FRONTEND_DESIGN_ENHANCED_A_20261008.md)
替代旧 V2-B 的跨来源视觉统一规则；冻结 v1.1.1 的身份、时间、预算与不可变性规则不变。
本节是应用能力扩展方案，不表示已修改数据库、接口或研究图，也不推断第三方私有实现。

### 能力分工与复用边界

| 借鉴行为 | 自有应用能力与拟定职责 | 当前缺口/计划 |
| --- | --- | --- |
| Simply 公司章节、关注与门户 | 账户范围门户查询、公司详情、本人最近研究及历史变化投影；公司公开事实与私有研究分开授权 | 已有目录/关注/研究列表；聚合与详情待补，BE-01 / R1 |
| Fiscal 多期表格、趋势、来源与分部/KPI | 财务事实序列与申报版本存储，单位/期间/口径对齐，确定性指标服务，分部/KPI身份及原始申报定位 | 当前仅年度切片；BE-02～03 / R2 |
| Quartr 材料检索、引用与原文阅读 | 以本人授权研究为入口的材料/片段查询，文档/内容版本/位置映射，有界检索和安全投影 | 复用证据与RAG持久化；账户阅读接口待补，BE-04 / R3 |
| TradeAgent 论点与预测 | 账户论点历史/受控写命令、不可变版本与乐观并发，研究记忆回流、Critic与冻结准入 | 内部基础不是公开账户能力；BE-05～08 / R4 |

### 服务、存储与契约边界

- Next 展示来源界面并维护可恢复状态；同源BFF只代理精确路径/方法和服务器会话。
  FastAPI应用层负责账户授权、有界查询/命令与DTO；领域服务负责财务计算、时间可见性、
  质量、研究完整性和冻结资格；SQLAlchemy/PostgreSQL负责事实/版本/归属持久化。
  外部采集和模型执行沿用来源适配器、预算与Redis/Celery研究图，不进入浏览器。
- 复用既有 `/workspace/companies`、`/workspace/watchlist` 与精确账户研究
  `/workspace/research` 的提交、列表、options、详情、cancel和report能力。新增URI、DTO和
  迁移在各增量规格冻结，不能把拟定职责写成现有接口；不扩开旧内部research/RAG/thesis。
- 财务序列至少区分instrument、概念/分部/KPI身份、单位/币种、期间类型及起止日期、
  申报版本、来源定位和信息可用时间。财年/日历年、年度/季度/TTM、原始/标准化口径
  不静默混合；重述版本保留，按Analysis Timestamp选取当时可知记录。
  分部/KPI不可随显示名称改变身份；业务划分变化、口径不兼容与缺值有显式状态。
  正式schema/迁移和公式在BE-02/03规格中确定，不凭页面需要前端重算。
- 已有证据/RAG文档和chunk优先复用；材料查询返回安全的来源、内容范围、版本与位置。
  必须先验证本人研究归属及证据关联，不能通过全局evidence/document UUID读他人材料。
  页长、文本长度、过滤条件、查询次数与检索范围有界；上传材料不提升来源信任，片段不冒充全文。
- 论点/预测读取和写入重新执行账户与引用授权；冻结仍依赖合格完整综合和不可变执行来源。
  公共事实可按许可共享，账户研究/笔记/论点不可共享。变化投影需真实历史版本与明确比较时间，
  不将首次研究或fixture显示为改善、收益或成熟结果。
- 前端期间/阅读状态不改变持久Analysis Timestamp；把财务选择转成研究输入时，必须由
  提交契约显式支持和后端校验，不能新增查询参数便声称研究实际使用了该期间。
  对未知成本、缺项、质量未验证和部分报告保留明确状态；来源评分不映射为SystemConfidence。

### 增量准入与验证

来源页面/交互清单 → 现有契约映射 → 缺口与数据资格 → 增量spec → 前后端实现 →
代表页面效果确认与行为验收。只借鉴首版对应功能；直播音频、全市场覆盖、估值共识、
组合与筛选等不因参考网站提供便自动纳入首版或授予来源资格。

复用账户HTTP/BFF、财务确定性行为、证据存储/报告和论点版本等已有测试边界。
新增权限/数据行为按TDD覆盖本人/他人/历史未归属、非法ID、分页上限、期间切换、
申报修订/截止时间、原文定位与版本、并发及冻结拒绝；本地真实PG/BFF和产品UI逐增量验收。
后端行为、视觉还原、离线金例、真实来源资格分别记录。具体任务仍以开发计划为唯一清单。

## Frozen baseline and historical checkpoints

The source-of-truth architecture is **Agentic Equity Research Workbench v1.1.1 — Quant Integrity + Operational Reliability Hardened** dated 2026-09-16.

Current checkpoint: [2026-10-03 pre-P10 fixes](../01_项目总览/PRE_P10_CHECKPOINT_20261003.md).
Catalyst failure handling and independent imports are fixed; live nonempty source
interpretations passed citation checks. V1 indicator and strategy statistic calculations
are implemented with explicit configuration and data gates. Research-memory feedback,
richer analysis, full observability and real market/strategy qualification remain open.
Formal P10 is paused for user requirements. The earlier whole-blueprint audit is a
pre-fix snapshot; stage descriptions below retain their historical slice context.

Current audit (2026-10-02): Phases 6–9 have their recorded fixture qualifications;
Phase 5 live completion remains open and Phase 10 has not started. Current model
intent/planning, news and SEC financial acquisition have passed the real local
HTTP/Redis/Celery/PostgreSQL path. Corporate-action completeness, live RAG inputs and
verified financial/catalyst analysis still prevent a complete report. See
`docs/01_项目总览/DEVELOPMENT_PROGRESS_20261002.md` for the current layer-by-layer assessment.
The stage descriptions below retain their original implementation context.

Subsequent current-source qualification added explicit lexical-only RAG without
embeddings. Official SEC filing excerpt intake and PostgreSQL FTS/PIT storage were
verified through the real research graph, removing its RAG gap. The optional hybrid
route remains available but has no live embedding qualification. An offline action
material audit supplies intake diagnostics, never provider qualification. Market/action
completeness and verified analysis still prevent a complete report. See
`docs/06_验证与审查/检索与评估/RAG_LEXICAL_QUALIFICATION.md` and `docs/04_数据源与检索/ACTION_COVERAGE_AUDIT.md`.

This repository has completed Phases 0-4 and implements the first Phase 5 vertical slice. PostgreSQL/pgvector migrations, the API-to-Redis-to-Celery path, point-in-time corporate-action visibility, deterministic price normalization, provider quality gates, and deterministic indicators have passed their local and Docker-backed qualifications. The Phase 5 LangGraph slice adds bounded planning, qualified-evidence collection, durable node transitions, terminal outcomes, failure persistence, durable cancellation, and bounded external-attempt records without changing the frozen provider boundaries.

Phase 5 is in progress rather than complete. Planner, market evidence, deterministic quant,
BudgetGuard enforcement, durable transitions, cancellation, external-attempt observability, and
safe terminal outcomes exist. Intent is a bounded persisted model step. A default-off News
ingestion node now enforces document budgets, point-in-time admission, and untrusted-text guards;
event extraction and a qualified live news adapter remain pending. A deterministic Gap Judge now
checks required plan capabilities against eligible evidence and records coverage. A bounded
model-assisted Replan can retry missing required News without removing original requirements;
evidence-cited Synthesis now runs only after sufficient coverage. Gate C passes with offline
loop-safety tests and a mock-provider Docker API/Redis/Celery/PostgreSQL complete path; live
provider qualification remains separate.

Phase 6 has append-only relational evidence persistence, explicit point-in-time reads, versioned
Thesis memory, a forward-only ForecastRecord repository, and an opt-in, token-guarded application
command. Forecast freezing now requires the Thesis prediction to match one immutable, persisted
Synthesis model execution and its structured output. PostgreSQL blocks direct changes to Thesis
history, model execution history, and Forecast records. The rebuilt Docker
API/Redis/Celery/PostgreSQL mock path has passed qualification. Phase 6 implementation is complete
within that fixture scope;
live provider qualification and real forward accumulation remain separate. Phase 7 Secure RAG
has begun with bounded document intake, prompt-injection quarantine, and append-only
document/chunk storage with pgvector and FTS indexes. PIT-filtered hybrid retrieval and a
bounded untrusted ContextBuilder exist. Default-off guarded APIs and a durable RAG research
node are integrated. Gate D and PostgreSQL/pgvector retrieval are fixture-qualified; real
embedding and live document providers remain separate. Phase 8 replay/evaluation follows.

ADR-0018 separates immutable fixed-cutoff research from current research whose decision cutoff is
persisted only after evidence acquisition. The transport, state, migration, model context, and
workflow tracer are implemented. The initial production current-acquisition route uses one
request-scoped yfinance history snapshot for bars and observed corporate actions, is qualified only
against offline fixtures, remains default-off, and fails closed when yfinance is not configured.

ADR-0017 permits an isolated frontend clone lab during Phase 5 for early visual and interaction
learning. It does not move the formal product UI out of Phase 10: only reviewed design artifacts
and components may enter `apps/web`. Gate C now permits research API integration; later screens
wait for their Phase 6-9 contracts.

ADR-0019 keeps current acquisition yfinance-only until another current-capable adapter is
independently qualified. It also assigns the qualified fixed-cutoff cache to each worker process as
a configurable bounded LRU; cache contents are expendable and never authoritative research state.

## Current boundaries

- FastAPI application skeleton
- strict Pydantic data contracts
- deterministic budget guard
- provider-neutral model gateway
- Codex subscription, Qwen, DeepSeek, OpenAI API, and mock executor boundaries
- bounded retry/fallback and execution metadata
- SQLAlchemy repositories and Alembic migration for the SecurityMaster and research runs
- FastAPI research submission/status boundaries
- explicit fixed-cutoff/current-research timestamp intent with a nullable pending decision cutoff
- JSON-only Celery/Redis queue boundary with bounded pending-run reconciliation
- provider-neutral market-data and corporate-action interfaces
- worker-facing fixed-cutoff and current-acquisition seams; fixed requests use whole-request Alpha
  Vantage-to-yfinance fallback, while current acquisition initially uses yfinance only
- explicitly allowlisted operational fallback, fail-closed integrity failures, and provider
  attempts persisted into successful evidence or terminal gap reasons
- quality-version-aware, worker-process-local bounded LRU caching ahead of external providers
- immutable persisted decision cutoffs and final evidence-time validation against the frozen cutoff
- point-in-time-safe corporate-action lookup and deterministic price normalization
- fail-closed provider and per-bar quality gates for strict backtests
- deterministic pandas/NumPy/SciPy technical indicators
- unit and adapter tests
- documented staged frontend strategy; `apps/web` remains unimplemented

Phase 9 produces restricted deterministic fixture signals and a non-executable
TradeIntent. No component places broker orders or establishes historical alpha;
current reports do not establish complete investment analysis.
