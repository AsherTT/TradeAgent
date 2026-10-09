export type ResearchStatus = "pending" | "running" | "complete" | "insufficient_evidence" | "failed" | "cancelled";
export interface Company { instrument_id: string; current_symbol: string; company_name: string; exchange: string; currency: string }
export interface ResearchSummary {
  research_run_id: string; instrument_id: string; ticker: string; query: string; horizon: string;
  requested_at: string; status: ResearchStatus; research_completion: string | null; collection_only: boolean;
}
export interface ResearchDetail extends ResearchSummary {
  analysis_timestamp: string | null; research_budget: Record<string, number>; budget_usage: Record<string, number>;
  data_quality_status: string; quality_gate_decision: string | null; progress_steps: string[];
  failure_code: string | null; actual_cost_usd: number | null;
  quality_assessment: null | {
    evaluation_maturity: string; replay_integrity: string; security_status: string; evidence_coverage: number;
    reasons: string[]; system_confidence: { score: number; limitations: string[] };
  };
}
export interface Citation {
  evidence_id: string; evidence_type: string; source_name: string; source_uri: string | null;
  published_at: string | null; observed_at: string; available_at: string;
}
export interface ResearchReport {
  research_id: string; ticker: string; complete_analysis: boolean; citation_note: string;
  data_quality_status: string; quality_gate_decision: string | null;
  sections: { title: string; text: string; evidence_ids: string[] }[]; citations: Citation[]; gaps: string[];
  market_acquisition: null | { source_names: string[]; provider_quality_versions: string[]; data_quality_status: string; bar_count: number };
  financial_metric_assessments: {
    name: string; interpretation: string | null; unavailable_reason: string | null; limitations: string[];
    metric: null | { value: string; unit: string; period_start: string | null; period_end: string; evidence_ids: string[] };
  }[];
  catalyst_limitations: string[];
}
export const validResearchId = (id: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
export const researchActive = (run: ResearchSummary) => run.status === "pending" || run.status === "running";
export function safeEvidenceUrl(value: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || !url.hostname || url.username || url.password || url.port || /\s/.test(value)) return null;
    return url.href;
  } catch { return null; }
}
