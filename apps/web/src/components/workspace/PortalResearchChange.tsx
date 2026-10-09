"use client";

import Link from "next/link";
import { researchLabel, researchTime } from "@/components/research/copy";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import type { ResearchChange } from "./contracts";

export function PortalResearchChange({ instrumentId, change }: {
  instrumentId: string;
  change: ResearchChange | undefined;
}) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const signed = (value: number | null) => value === null ? researchLabel(locale, null) : value > 0 ? `+${value}` : String(value);
  return (
    <div aria-label={zh ? "研究记录变化" : "Research record changes"} className="w-full border-l-2 border-[#d9d5bf] pl-3 text-xs leading-6 [overflow-wrap:anywhere]">
      <p className="font-medium">{zh ? "本人研究记录变化" : "Your research record changes"}</p>
      {!change ? <p className="text-[#777065]">{zh ? "研究变化暂不可用，请稍后刷新。" : "Research changes are unavailable. Refresh later."}</p> : <>
        <p className="text-[#777065]">{zh
          ? `最近 ${change.window_limit} 条结束记录；仅比较相同研究条件，不代表公司表现或质量改善。`
          : `Latest ${change.window_limit} finished records; matching research conditions only, not company performance or better quality.`}</p>
        {change.has_more && <p className="text-[#855d21]">{zh ? "更早记录在窗口外，未作全历史比较。" : "Older records are outside the window; this is not full history."}</p>}
        {change.availability === "available" ? <p>
          {zh ? "准入证据数变化 " : "Admitted evidence change "}<strong>{signed(change.qualified_evidence_count_delta)}</strong>
          {zh ? " · 已记录缺口数变化 " : " · Recorded gap change "}<strong>{signed(change.evidence_gap_count_delta)}</strong>
        </p> : <p>{change.availability === "no_finished_research"
          ? zh ? "尚无有效分析时间的结束研究。" : "No finished research with a valid analysis cutoff."
          : zh ? "暂无相同条件且分析时间更早的可比较记录。" : "No comparable record with an earlier analysis cutoff."}</p>}
        {([change.latest, change.previous] as const).map((record, index) => record && <p key={record.research_run_id}>
          <Link className="text-[#855d21] underline" href={`/app/research/${record.research_run_id}`}>
            {index === 0 ? zh ? "最近任务与报告" : "Latest task & report" : zh ? "上次可比较任务与报告" : "Previous comparable task & report"}
          </Link><br />
          <span className="text-[#777065]">{zh ? "分析截止时间 " : "Analysis cutoff "}
            <time dateTime={record.analysis_timestamp}>{researchTime(locale, record.analysis_timestamp)}</time>
          </span>
        </p>)}
      </>}
      <Link className="text-[#855d21] underline" href={`/app/companies/${instrumentId}#company-change`}>
        {zh ? "查看公司研究变化详情" : "View company research change details"} →
      </Link>
    </div>
  );
}
