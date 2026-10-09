import type { Company, ResearchSummary } from "@/components/research/contracts";

export interface WorkspacePage<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
export interface PortalSummary {
  directory_scope: "local_directory";
  watchlist: WorkspacePage<Company>;
  recent_research: WorkspacePage<ResearchSummary>;
  active_research: ResearchSummary[];
  active_research_total: number;
  research_changes: { instrument_id: string; research_change: ResearchChange }[];
}
export interface CompanyDetail {
  company: Company;
  is_followed: boolean;
  directory_scope: "local_directory";
  research: WorkspacePage<ResearchSummary>;
  research_change: ResearchChange;
}

export interface ResearchChangeSnapshot extends ResearchSummary {
  analysis_timestamp: string;
  data_quality_status: string;
  quality_gate_decision: string | null;
  qualified_evidence_count: number;
  evidence_gap_count: number;
}
export interface ResearchChange {
  availability: "available" | "no_finished_research" | "no_comparable_previous";
  window_limit: number;
  has_more: boolean;
  latest: ResearchChangeSnapshot | null;
  previous: ResearchChangeSnapshot | null;
  qualified_evidence_count_delta: number | null;
  evidence_gap_count_delta: number | null;
}
