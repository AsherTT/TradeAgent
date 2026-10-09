"use client";

import Link from "next/link";
import { accountStyles as styles } from "@/components/accounts/styles";
import { researchLabel, researchTime } from "@/components/research/copy";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import type { ResearchChange, ResearchChangeSnapshot } from "./contracts";

function RecordSnapshot({ record, title }: { record: ResearchChangeSnapshot; title: string }) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const values = [
    [zh ? "研究状态" : "Research status", researchLabel(locale, record.research_completion === "budget_exhausted" ? record.research_completion : record.status)],
    [zh ? "数据质量" : "Data quality", researchLabel(locale, record.data_quality_status)],
    [zh ? "质量门槛" : "Quality gate", researchLabel(locale, record.quality_gate_decision)],
    [zh ? "准入证据数" : "Admitted evidence", record.qualified_evidence_count],
    [zh ? "已记录缺口数" : "Recorded gaps", record.evidence_gap_count],
  ];
  return (
    <article className="min-w-0 rounded-xl border border-[#e7e2d5] bg-[#faf8f1] p-4 [overflow-wrap:anywhere]">
      <h3 className="mb-3 font-medium">{title}</h3>
      <p className="mb-3 text-xs text-[#777065]">
        {zh ? "分析截止时间" : "Analysis cutoff"}<br />
        <time dateTime={record.analysis_timestamp}>{researchTime(locale, record.analysis_timestamp)}</time>
      </p>
      <dl className="mb-4 space-y-2 text-sm">
        {values.map(([label, value]) => (
          <div key={label} className="flex flex-wrap justify-between gap-2">
            <dt className="text-[#777065]">{label}</dt><dd>{value}</dd>
          </div>
        ))}
      </dl>
      <Link className="text-xs text-[#855d21] underline" href={`/app/research/${record.research_run_id}`}>
        {zh ? "查看这次任务与报告" : "View this task & report"} →
      </Link>
    </article>
  );
}

export function ResearchChangePanel({ change }: { change: ResearchChange }) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const signed = (value: number | null) => value === null ? researchLabel(locale, null) : value > 0 ? `+${value}` : String(value);
  return (
    <section id="company-change" className={`${styles.card} mt-6 scroll-mt-6 [overflow-wrap:anywhere]`}>
      <h2 className="mb-3 text-xl font-medium">{zh ? "研究记录变化" : "Research record changes"}</h2>
      <p className="mb-4 text-xs leading-6 text-[#777065]">
        {zh
          ? `比较最近 ${change.window_limit} 条已结束记录中相同问题、期限和模式的本人研究。以下仅为记录覆盖与质量，不代表公司表现、评分或投资结论；证据增加不代表质量改善，也不证明历史来源资格。`
          : `Compare your research with the same question, horizon and mode within the latest ${change.window_limit} finished records. These are record coverage and quality changes, not company performance, scores or investment conclusions. More evidence does not establish better quality or historical source qualification.`}
      </p>
      {change.has_more && <p className="mb-4 text-xs leading-6 text-[#855d21]">
        {zh ? "更早记录在本次比较窗口之外，未作全历史比较。" : "Older records exist outside this comparison window; this is not a full-history comparison."}
      </p>}
      {change.latest && <p className="mb-4 whitespace-pre-wrap text-sm leading-6">
        {change.latest.query}<br />
        <span className="text-xs text-[#777065]">{change.latest.horizon} · {zh
          ? change.latest.collection_only ? "资料采集" : "模型研究"
          : change.latest.collection_only ? "Collection only" : "Model research"}</span>
      </p>}
      {change.availability === "available" ? <p className="mb-4 text-sm leading-7">
        {zh ? "与上次相比：准入证据数 " : "Compared with previous: admitted evidence "}
        <strong>{signed(change.qualified_evidence_count_delta)}</strong>
        {zh ? "；已记录缺口数 " : "; recorded gaps "}
        <strong>{signed(change.evidence_gap_count_delta)}</strong>
      </p> : <p className="mb-4 text-sm leading-7 text-[#777065]">
        {change.availability === "no_finished_research"
          ? zh ? "尚无具有有效分析时间的已结束研究，暂不能比较。" : "No finished research with a valid analysis cutoff is available to compare."
          : zh ? "本窗口内没有相同研究条件且分析时间更早的记录，暂不能计算变化。" : "No earlier analysis cutoff with matching research conditions exists in this window; changes are unavailable."}
      </p>}
      <div className="grid gap-4 md:grid-cols-2">
        {change.latest && <RecordSnapshot record={change.latest} title={zh ? "最近一次" : "Latest record"} />}
        {change.previous && <RecordSnapshot record={change.previous} title={zh ? "上一次可比较记录" : "Previous comparable record"} />}
      </div>
    </section>
  );
}
