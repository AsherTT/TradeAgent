"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AccountShell } from "@/components/accounts/AccountShell";
import { accountStyles as styles } from "@/components/accounts/styles";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { ResearchApiError, researchRequest } from "./api";
import { researchActive, validResearchId, type ResearchDetail, type ResearchReport } from "./contracts";
import { researchCopy, researchError, researchLabel, researchTime } from "./copy";
import { ResearchReportView } from "./ResearchReportView";

const budgetDimensions = ["iterations", "replans", "tool_calls", "llm_calls", "wall_time_seconds", "context_tokens", "news_documents", "rag_chunks"] as const;

export function ResearchRun({ runId, unavailable }: { runId: string; unavailable: boolean }) {
  const { locale } = useLanguage();
  const copy = researchCopy(locale);
  const router = useRouter();
  const [run, setRun] = useState<ResearchDetail | null>(null);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState<string | null>(!validResearchId(runId) ? "invalid_research_id" : unavailable ? "backend_unavailable" : null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [cancelling, setCancelling] = useState(false);
  const cancellation = useRef(false);
  const sessionValid = useRef(true);
  const stopLoading = useRef<(() => void) | null>(null);

  const expireSession = useCallback(() => {
    sessionValid.current = false;
    stopLoading.current?.();
    setRun(null); setReport(null); setReportError(null);
    setError("authentication_required");
    router.replace("/login"); router.refresh();
  }, [router]);

  useEffect(() => {
    if (!sessionValid.current || !validResearchId(runId)) return;
    const controller = new AbortController();
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    function stop() { active = false; controller.abort(); clearTimeout(timer); }
    stopLoading.current = stop;
    async function load() {
      try {
        const state = await researchRequest<ResearchDetail>(`research/${runId}`, { signal: controller.signal });
        if (!active || !sessionValid.current) return;
        setRun(state); setError(null);
        try {
          const projected = await researchRequest<ResearchReport>(`research/${runId}/report`, { signal: controller.signal });
          if (!active || !sessionValid.current) return;
          setReport(projected); setReportError(null);
        } catch (failure) {
          if (!active || !sessionValid.current) return;
          if (failure instanceof ResearchApiError && failure.status === 401) { expireSession(); return; }
          setReport(null); setReportError(failure instanceof ResearchApiError ? failure.code : "backend_unavailable");
        }
        if (researchActive(state)) timer = setTimeout(() => void load(), 5000);
      } catch (failure) {
        if (!active || !sessionValid.current) return;
        if (failure instanceof ResearchApiError && failure.status === 401) { expireSession(); return; }
        if (failure instanceof ResearchApiError && (failure.status === 404 || failure.status === 422)) { setRun(null); setReport(null); }
        setError(failure instanceof ResearchApiError ? failure.code : "backend_unavailable");
      }
    }
    void load();
    return stop;
  }, [revision, expireSession, runId]);

  async function cancel() {
    if (cancellation.current || !sessionValid.current) return;
    cancellation.current = true; setCancelling(true);
    try {
      await researchRequest<ResearchDetail>(`research/${runId}/cancel`, { method: "POST" });
      if (!sessionValid.current) return;
      setRevision((value) => value + 1);
    } catch (failure) {
      if (!sessionValid.current) return;
      if (failure instanceof ResearchApiError && failure.status === 401) { expireSession(); return; }
      setError(failure instanceof ResearchApiError ? failure.code : "backend_unavailable");
    } finally { cancellation.current = false; setCancelling(false); }
  }

  const assessment = run?.quality_assessment;
  return <AccountShell>
    <Link className="underline" href="/app/research">← {copy.back}</Link><h1 className={styles.heading}>{run ? `${run.ticker} · ${copy.details}` : copy.details}</h1>
    <div className="mb-5 flex flex-wrap items-center gap-4"><button className={styles.button} onClick={() => setRevision((value) => value + 1)}>{copy.refresh}</button>{run && researchActive(run) && <button className={styles.button} disabled={cancelling || !!error} onClick={() => void cancel()}>{cancelling ? copy.cancelling : copy.cancel}</button>}</div>
    {error && <div role="alert" className={styles.error}>{researchError(locale, error)} <button className="cursor-pointer underline" onClick={() => setRevision((value) => value + 1)}>{copy.retry}</button></div>}
    {!run && !error && <p role="status">{copy.loading}</p>}
    {run && <>
      <section className={`${styles.card} [overflow-wrap:anywhere]`}>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">{copy.status}</h2><span role="status" className="rounded-full bg-[#f8edcf] px-4 py-2 font-medium">{researchLabel(locale, run.research_completion === "budget_exhausted" ? run.research_completion : run.status)}</span></div>
        <p className="mb-5 whitespace-pre-wrap text-lg leading-7">{run.query}</p>
        <dl className="grid gap-4 text-xs sm:grid-cols-2 lg:grid-cols-3">{([
          [copy.task, run.research_run_id], [copy.requested, researchTime(locale, run.requested_at)],
          [copy.horizon, run.horizon], [copy.cutoff, run.analysis_timestamp ? researchTime(locale, run.analysis_timestamp) : copy.notFrozen],
          [copy.dataQuality, researchLabel(locale, run.data_quality_status)], [copy.gate, researchLabel(locale, run.quality_gate_decision)],
          [copy.actualCost, run.actual_cost_usd === null ? copy.unknown : `$${run.actual_cost_usd}`],
        ] as const).map(([label, value]) => <div key={label}><dt className={styles.muted}>{label}</dt><dd className="mt-1 font-medium">{value}</dd></div>)}</dl>
        {run.failure_code && <p className={styles.error}>{researchError(locale, run.failure_code)}</p>}
        <p className={`${styles.muted} mt-5 text-xs`}>{run.collection_only ? copy.collectingNote : copy.cancelNote}</p>
        {researchActive(run) && run.collection_only && <p className={`${styles.muted} mt-2 text-xs`}>{copy.cancelNote}</p>}
        <h3 className="mt-6 mb-3 font-semibold">{copy.progress}</h3>{run.progress_steps.length ? <ol className="flex flex-wrap gap-2 text-xs">{run.progress_steps.map((step, index) => <li key={index} className="rounded-md bg-[#edebe1] px-3 py-2">{index + 1}. {researchLabel(locale, step)}</li>)}</ol> : <p className={styles.muted}>{copy.waiting}</p>}
        <h3 className="mt-6 mb-3 font-semibold">{copy.usage}</h3><dl className="grid grid-cols-2 gap-4 text-xs md:grid-cols-4">{budgetDimensions.map((key) => <div key={key}><dt className={styles.muted}>{researchLabel(locale, key)}</dt><dd className="mt-1 font-medium">{run.budget_usage[key]} / {run.research_budget[`max_${key}`]}</dd></div>)}</dl>
        <p className={`${styles.muted} mt-4 text-xs`}>{copy.estimate}: ${run.budget_usage.estimated_cost_usd} / ${run.research_budget.max_estimated_cost_usd} · {copy.actualCost}: {copy.unknown}</p>
        <p className={`${styles.muted} mt-2 text-xs`}>{copy.budgetNote}</p>
        {assessment && <div className="mt-6 border-t border-[#d9d5bf] pt-5"><dl className="grid gap-4 text-xs sm:grid-cols-2 lg:grid-cols-4">{([
          [copy.maturity, researchLabel(locale, assessment.evaluation_maturity)], [copy.integrity, researchLabel(locale, assessment.replay_integrity)],
          [copy.security, researchLabel(locale, assessment.security_status)], [copy.confidence, String(assessment.system_confidence.score)],
          [copy.coverage, String(assessment.evidence_coverage)],
        ] as const).map(([label, value]) => <div key={label}><dt className={styles.muted}>{label}</dt><dd className="mt-1">{value}</dd></div>)}</dl><h3 className="mt-4 font-semibold">{copy.reasons}</h3><ul className="mt-2 list-disc space-y-2 pl-5 text-xs leading-6">{Array.from(new Set([...assessment.reasons, ...assessment.system_confidence.limitations])).map((text, index) => <li key={index}>{text}</li>)}</ul></div>}
      </section>
      {reportError && <div role="alert" className={styles.error}>{copy.report}: {researchError(locale, reportError)}</div>}
      {report && <ResearchReportView report={report} locale={locale} />}
    </>}
  </AccountShell>;
}
