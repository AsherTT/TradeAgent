import type { Locale } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/messages";

const copy = {
  zh: {
    title: "我的研究", intro: "选择公司，记录问题，追踪研究并核验原始证据。", workspace: "返回工作台",
    companySearch: "搜索公司或代码", noCompanyMatches: "没有匹配公司，请调整搜索。", invalid_research_id: "任务地址中的标识无效，请返回研究列表。",
    newResearch: "提交研究", company: "研究公司", question: "研究问题", horizon: "研究期限", mode: "研究方式",
    collection: "资料采集（不调用模型综合）", full: "模型研究", disabled: "模型研究尚未启用，需先核对供应商与预算。",
    noCompanies: "公司目录为空，暂时无法提交研究。", budgets: "本次预算上限", cost: "估算费用上限（美元）",
    seconds: "运行时间（秒）", llm: "模型调用次数", budgetNote: "最多4轮、2次重规划、12次工具调用、100000上下文token、30份新闻、12段检索。费用可能未知，估算上限不代表精确计费。",
    submit: "提交并查看", submitting: "正在提交…", loading: "正在加载…", refresh: "刷新", empty: "还没有研究任务。",
    recent: "最近50项研究", view: "查看任务与报告", task: "任务ID", requested: "提交时间", status: "任务状态",
    details: "研究进度", cancel: "取消任务", cancelling: "正在取消…", cancelNote: "取消会停止后续步骤，已发生的外部调用可能仍产生费用。",
    unknown: "未知", waiting: "等待执行步骤", cutoff: "分析时间截止", notFrozen: "尚未确定", dataQuality: "数据质量",
    gate: "质量门槛", progress: "已保存的执行步骤", usage: "预算用量 / 上限", actualCost: "实际费用", estimate: "记录的估算金额",
    report: "研究报告", partial: "部分报告 · 不是完整分析", complete: "完整分析报告", contentNote: "报告正文及来源说明保留后端原文。任务结束不代表分析完整或来源合格。",
    gaps: "证据缺口", noGaps: "尚未记录缺口", evidence: "证据与来源", noEvidence: "暂无可用引用。", source: "查看原始来源",
    unavailableSource: "暂无安全网页链接", published: "发布时间", observed: "观察时间", available: "可知时间", original: "原始资料",
    metrics: "财务指标", unavailable: "暂无合格数据", versions: "来源资格版本", bars: "采集行情条数", maturity: "评估成熟度",
    integrity: "回放完整性", security: "安全状态", confidence: "系统可信度", coverage: "证据覆盖率", reasons: "质量说明",
    collectingNote: "资料采集仅使用已配置的数据源，不执行模型综合，不能视为完整研究。", back: "返回研究列表", retry: "重试",
    error: "操作未完成，请重试。", backend_unavailable: "暂时无法连接服务。", research_not_found: "研究不存在或当前账户无权访问。",
    not_found: "研究不存在或当前账户无权访问。",
    invalid_research_input: "请检查公司、问题、期限和预算。", submission_conflict: "此提交标识已用于不同内容，请刷新页面后重新提交。",
    model_research_disabled: "模型研究尚未启用。", active_research_limit: "最多同时运行3项研究，请先等待或取消。",
    queue_unavailable: "任务派发失败，可返回列表查看已保存的失败记录。", research_failed: "研究执行失败，已保留可用部分报告。",
    company_not_found: "公司已不可用，请刷新目录。", origin_not_allowed: "当前访问地址未获允许。",
  },
  en: {
    title: "My research", intro: "Choose a company, record your question, track research and verify original evidence.", workspace: "Back to workspace",
    companySearch: "Search a company or ticker", noCompanyMatches: "No matching companies. Refine the search.", invalid_research_id: "The task ID in this address is invalid. Return to your research list.",
    newResearch: "New research", company: "Company", question: "Research question", horizon: "Research horizon", mode: "Research mode",
    collection: "Evidence collection (no model synthesis)", full: "Model research", disabled: "Model research is disabled until providers and budgets are checked.",
    noCompanies: "The company directory is empty. Research cannot be submitted yet.", budgets: "Budget limits", cost: "Estimated cost limit (USD)",
    seconds: "Runtime (seconds)", llm: "Model calls", budgetNote: "At most 4 iterations, 2 replans, 12 tool calls, 100000 context tokens, 30 news documents and 12 retrieval chunks. Charges may be unknown; estimated limits do not establish exact billing.",
    submit: "Submit and view", submitting: "Submitting…", loading: "Loading…", refresh: "Refresh", empty: "No research tasks yet.",
    recent: "Latest 50 research tasks", view: "View task and report", task: "Task ID", requested: "Submitted", status: "Task status",
    details: "Research progress", cancel: "Cancel task", cancelling: "Cancelling…", cancelNote: "Cancellation stops later steps. External calls already made may still incur charges.",
    unknown: "Unknown", waiting: "Waiting for execution steps", cutoff: "Analysis timestamp", notFrozen: "Not established", dataQuality: "Data quality",
    gate: "Quality gate", progress: "Saved execution steps", usage: "Budget usage / limit", actualCost: "Actual charges", estimate: "Recorded estimate",
    report: "Research report", partial: "Partial report · incomplete analysis", complete: "Complete analysis report", contentNote: "Report text and source notes retain the backend's original language. A finished task does not establish complete analysis or qualified sources.",
    gaps: "Evidence gaps", noGaps: "No gaps recorded yet", evidence: "Evidence and sources", noEvidence: "No eligible citations yet.", source: "Open original source",
    unavailableSource: "No safe web link available", published: "Published", observed: "Observed", available: "Available", original: "Original material",
    metrics: "Financial metrics", unavailable: "Qualified data unavailable", versions: "Provider qualification versions", bars: "Collected bars", maturity: "Evaluation maturity",
    integrity: "Replay integrity", security: "Security", confidence: "System confidence", coverage: "Evidence coverage", reasons: "Quality notes",
    collectingNote: "Evidence collection uses configured sources without model synthesis. It is not complete research.", back: "Back to research", retry: "Retry",
    error: "The action could not be completed. Try again.", backend_unavailable: "The service is temporarily unavailable.", research_not_found: "Research was not found or is not owned by this account.",
    not_found: "Research was not found or is not owned by this account.",
    invalid_research_input: "Check the company, question, horizon and budgets.", submission_conflict: "This submission ID was used for different content. Reload to start a new submission.",
    model_research_disabled: "Model research is disabled.", active_research_limit: "At most 3 active tasks are allowed. Wait or cancel one first.",
    queue_unavailable: "Dispatch failed. The saved failed task is available in your list.", research_failed: "Research failed. Available partial results are preserved.",
    company_not_found: "This company is unavailable. Refresh the directory.", origin_not_allowed: "This address is not allowed.",
  },
};

const labels: Record<string, [string, string]> = {
  pending: ["等待执行", "Pending"], running: ["执行中", "Running"], complete: ["流程已结束", "Process complete"],
  insufficient_evidence: ["证据不足", "Insufficient evidence"], failed: ["失败", "Failed"], cancelled: ["已取消", "Cancelled"], budget_exhausted: ["预算耗尽", "Budget exhausted"],
  verified: ["已核验", "Verified"], acceptable: ["可接受", "Acceptable"], degraded: ["降级", "Degraded"], unverified: ["未核验", "Unverified"], rejected: ["已拒绝", "Rejected"],
  publishable: ["可发布", "Publishable"], insufficient: ["不足", "Insufficient"], blocked: ["已阻止", "Blocked"], pass: ["通过", "Pass"],
  cold_start: ["冷启动", "Cold start"], accumulating: ["积累中", "Accumulating"], early_sample: ["早期样本", "Early sample"], mature: ["成熟", "Mature"],
  research_replay: ["研究回放", "Research replay"], evidence_constrained_replay: ["证据约束回放", "Evidence constrained replay"],
  start: ["开始", "Started"], intent: ["研究意图已记录", "Intent saved"], intent_started: ["解析研究意图", "Interpreting intent"], plan: ["计划已记录", "Plan saved"], plan_started: ["规划中", "Planning"],
  collect_evidence: ["资料采集完成", "Evidence collected"], evidence_started: ["采集资料", "Collecting evidence"], news: ["新闻已记录", "News saved"], news_started: ["采集新闻", "Collecting news"],
  rag: ["检索已记录", "Retrieval saved"], rag_started: ["检索证据", "Retrieving evidence"], catalysts: ["来源解释已记录", "Source interpretations saved"], catalysts_started: ["解读来源", "Interpreting sources"],
  gap_judge: ["缺口判断", "Assessing gaps"], replan: ["重规划完成", "Replan saved"], replan_started: ["重规划中", "Replanning"], synthesis: ["综合已记录", "Synthesis saved"], synthesis_started: ["综合中", "Synthesizing"], finish: ["收尾完成", "Finished"],
  iterations: ["研究轮次", "Iterations"], replans: ["重规划", "Replans"], tool_calls: ["工具调用", "Tool calls"], llm_calls: ["模型调用", "Model calls"], wall_time_seconds: ["秒数", "Seconds"], context_tokens: ["上下文token", "Context tokens"], news_documents: ["新闻文档", "News documents"], rag_chunks: ["检索片段", "Retrieval chunks"],
  annual_net_margin: ["年度净利率", "Annual net margin"], cash_to_assets: ["现金 / 资产", "Cash / assets"],
  analysis_cutoff_unavailable: ["分析截止尚未确定", "Analysis cutoff unavailable"], qualified_financial_group_unavailable: ["缺少合格且一致的财务数据", "Qualified consistent financial data unavailable"], nonpositive_denominator: ["分母不为正数", "Nonpositive denominator"], negative_cash: ["现金值为负数", "Negative cash"], arithmetic_unavailable: ["超出计算限制", "Arithmetic unavailable"],
};
export const researchCopy = (locale: Locale) => copy[locale];
export function researchError(locale: Locale, code: string) {
  const messages: Record<string, string> = copy[locale];
  return Object.hasOwn(messages, code) ? messages[code] : messages.error;
}
export function researchLabel(locale: Locale, value: string | null) {
  if (!value) return copy[locale].unknown;
  return Object.hasOwn(labels, value) ? labels[value][locale === "zh" ? 0 : 1] : value;
}
export function researchTime(locale: Locale, value: string | null) {
  return value ? new Date(value).toLocaleString(locale === "zh" ? "zh-CN" : "en-US") : copy[locale].unknown;
}
