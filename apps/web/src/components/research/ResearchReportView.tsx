import type { Locale } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/messages";
import { accountStyles as styles } from "@/components/accounts/styles";
import { safeEvidenceUrl, type ResearchReport } from "./contracts";
import { researchCopy, researchLabel, researchTime } from "./copy";

function references(ids: string[]) {
  return ids.length > 0 && <ul className="mt-3 flex flex-wrap gap-2 text-xs">{ids.map((id) => <li key={id}><a className="underline [overflow-wrap:anywhere]" href={`#evidence-${id}`}>{id}</a></li>)}</ul>;
}

export function ResearchReportView({ report, locale }: { report: ResearchReport; locale: Locale }) {
  const copy = researchCopy(locale);
  return <section className={`${styles.card} mt-6 [overflow-wrap:anywhere]`}>
    <h2 className={styles.subheading}>{copy.report}</h2>
    <p className="mb-3 rounded-lg border border-[#d9d5bf] bg-[#f8edcf] p-3 font-medium">{report.complete_analysis ? copy.complete : copy.partial}</p>
    <p className={`${styles.muted} mb-6 text-xs`}>{copy.contentNote}</p>
    <div className="grid items-start gap-7 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <div className="min-w-0 space-y-6">
        {report.sections.map((section, index) => <article key={index}><h3 className="mb-2 text-lg font-semibold">{section.title}</h3><p className="whitespace-pre-wrap leading-7">{section.text}</p>{references(section.evidence_ids)}</article>)}
        <section><h3 className="mb-3 text-lg font-semibold">{copy.metrics}</h3><ul className="space-y-4">{report.financial_metric_assessments.map((item) => <li key={item.name} className="rounded-lg bg-[#edebe1] p-4">
          <strong>{researchLabel(locale, item.name)}</strong>
          {item.metric ? <><p className="mt-2 text-xl">{item.metric.value} <span className="text-xs">{item.metric.unit}</span></p><p className={`${styles.muted} text-xs`}>{item.metric.period_start ?? "—"} → {item.metric.period_end}</p>{references(item.metric.evidence_ids)}</> : <p className="mt-2">— · {researchLabel(locale, item.unavailable_reason)}</p>}
          {item.interpretation && <p className="mt-2 leading-6">{item.interpretation}</p>}
          <ul className="mt-2 space-y-1 text-xs text-[#625f58]">{item.limitations.map((text, index) => <li key={index}>{text}</li>)}</ul>
        </li>)}</ul></section>
        <section><h3 className="mb-2 text-lg font-semibold">{copy.gaps}</h3>{report.gaps.length ? <ul className="list-disc space-y-2 pl-5 leading-6">{report.gaps.map((text, index) => <li key={index}>{text}</li>)}</ul> : <p className={styles.muted}>{copy.noGaps}</p>}</section>
        {report.market_acquisition && <section className="rounded-lg border border-[#d9d5bf] p-4"><h3 className="mb-2 font-semibold">{copy.original}</h3><p>{report.market_acquisition.source_names.join(", ")} · {researchLabel(locale, report.market_acquisition.data_quality_status)}</p><p className={`${styles.muted} mt-2 text-xs`}>{copy.versions}: {report.market_acquisition.provider_quality_versions.join(", ")}</p><p className={`${styles.muted} text-xs`}>{copy.bars}: {report.market_acquisition.bar_count}</p></section>}
        {report.catalyst_limitations.length > 0 && <ul className="space-y-2 text-xs text-[#625f58]">{report.catalyst_limitations.map((text, index) => <li key={index}>{text}</li>)}</ul>}
      </div>
      <aside className="min-w-0 rounded-lg bg-[#edebe1] p-4 md:p-5"><h3 className="mb-3 text-lg font-semibold">{copy.evidence} <span className="text-sm">{report.citations.length}</span></h3><p className={`${styles.muted} mb-5 text-xs`}>{report.citation_note}</p>
        {report.citations.length === 0 ? <p className={styles.empty}>{copy.noEvidence}</p> : <ul className="space-y-5">{report.citations.map((citation) => {
          const link = safeEvidenceUrl(citation.source_uri);
          return <li key={citation.evidence_id} id={`evidence-${citation.evidence_id}`} className="scroll-mt-6 rounded-lg border border-[#c9c4b7] bg-[#fffdf8] p-4 target:ring-2 target:ring-[#986e2e]">
            <strong>{citation.source_name}</strong><p className="mt-2 text-xs">{citation.evidence_id}</p>
            <dl className="my-3 space-y-2 text-xs text-[#625f58]">{([[copy.published, citation.published_at], [copy.observed, citation.observed_at], [copy.available, citation.available_at]] as const).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{researchTime(locale, value)}</dd></div>)}</dl>
            {link ? <a href={link} target="_blank" rel="noopener noreferrer" className="text-[#855d21] underline">{copy.source} ↗</a> : <p className="text-xs text-[#625f58]">{copy.unavailableSource}</p>}
          </li>;
        })}</ul>}
      </aside>
    </div>
  </section>;
}
