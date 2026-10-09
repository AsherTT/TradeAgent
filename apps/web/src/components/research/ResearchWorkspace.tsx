"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AccountShell } from "@/components/accounts/AccountShell";
import { accountStyles as styles } from "@/components/accounts/styles";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { ResearchApiError, researchRequest } from "./api";
import { researchActive, type Company, type ResearchSummary } from "./contracts";
import { researchCopy, researchError, researchLabel, researchTime } from "./copy";
import type { CompanyDetail } from "@/components/workspace/contracts";

export function ResearchWorkspace({ unavailable, initialCompany = "" }: { unavailable: boolean; initialCompany?: string }) {
  const { locale } = useLanguage();
  const copy = researchCopy(locale);
  const router = useRouter();
  const [companyQuery, setCompanyQuery] = useState("");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [runs, setRuns] = useState<ResearchSummary[]>([]);
  const [modelsEnabled, setModelsEnabled] = useState(false);
  const [error, setError] = useState<string | null>(unavailable ? "backend_unavailable" : null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [revision, setRevision] = useState(0);
  const [instrument, setInstrument] = useState(initialCompany);
  const [companyUnavailable, setCompanyUnavailable] = useState(false);
  const [question, setQuestion] = useState("");
  const [horizon, setHorizon] = useState(locale === "zh" ? "3–5天" : "3–5 days");
  const [collection, setCollection] = useState(true);
  const [cost, setCost] = useState("0.10");
  const [seconds, setSeconds] = useState("120");
  const [llm, setLlm] = useState("4");
  const [saving, setSaving] = useState(false);
  const submitting = useRef(false);
  const requestIdentity = useRef<{ body: string; id: string } | null>(null);
  const sessionValid = useRef(true);
  const stopLoading = useRef<(() => void) | null>(null);
  const expireSession = useCallback(() => {
    sessionValid.current = false;
    stopLoading.current?.();
    setCompanies([]); setRuns([]); setInstrument(""); setQuestion("");
    setModelsEnabled(false); setCompanyUnavailable(false); setLoaded(true);
    setActionError(null); setError("authentication_required");
    requestIdentity.current = null;
    router.replace("/login"); router.refresh();
  }, [router]);

  useEffect(() => {
    if (!sessionValid.current) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let active = true;
    function stop() { active = false; controller.abort(); clearTimeout(timer); }
    stopLoading.current = stop;
    async function read<T>(path: string): Promise<T> {
      try {
        return await researchRequest<T>(path, { signal: controller.signal });
      } catch (failure) {
        if (active && sessionValid.current && failure instanceof ResearchApiError && failure.status === 401)
          expireSession();
        throw failure;
      }
    }
    async function load() {
      try {
        const [found, list, options, selected] = await Promise.all([
          read<Company[]>(`companies?query=${encodeURIComponent(companyQuery)}`),
          read<ResearchSummary[]>("research"),
          read<{ models_enabled: boolean }>("research/options"),
          initialCompany && !companyQuery ? read<CompanyDetail>(`companies/${initialCompany}`).catch((failure: unknown) => {
            if (failure instanceof ResearchApiError && failure.status === 404) return null;
            throw failure;
          }) : Promise.resolve(null),
        ]);
        if (!active || !sessionValid.current) return;
        const directory = selected && !found.some((company) => company.instrument_id === selected.company.instrument_id) ? [selected.company, ...found] : found;
        setCompanyUnavailable(!!initialCompany && !companyQuery && selected === null);
        setCompanies(directory); setInstrument((value) => directory.some((company) => company.instrument_id === value) ? value : ""); setRuns(list); setModelsEnabled(options.models_enabled);
        if (!options.models_enabled) setCollection(true);
        setError(null); setLoaded(true);
        if (list.some(researchActive)) timer = setTimeout(() => void load(), 5000);
      } catch (failure) {
        if (!active || !sessionValid.current) return;
        if (failure instanceof ResearchApiError && failure.status === 401) { expireSession(); return; }
        setError(failure instanceof ResearchApiError ? failure.code : "backend_unavailable");
        setLoaded(true);
      }
    }
    timer = setTimeout(() => void load(), 200);
    return stop;
  }, [revision, expireSession, companyQuery, initialCompany]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current || !sessionValid.current) return;
    let accepted = false;
    submitting.current = true; setSaving(true); setActionError(null);
    const payload = { instrument_id: instrument, query: question.trim(), horizon: horizon.trim(),
      collection_only: collection, budget: { max_iterations: 4, max_replans: 2, max_tool_calls: 12,
        max_llm_calls: collection ? 0 : Number(llm), max_wall_time_seconds: Number(seconds),
        max_context_tokens: 100000, max_estimated_cost_usd: Number(cost), max_news_documents: 30, max_rag_chunks: 12 } };
    const body = JSON.stringify(payload);
    if (!requestIdentity.current || requestIdentity.current.body !== body) requestIdentity.current = { body, id: crypto.randomUUID() };
    try {
      const receipt = await researchRequest<{ research_run_id: string }>("research", { method: "POST",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, request_id: requestIdentity.current.id }) });
      if (!sessionValid.current) return;
      accepted = true;
      requestIdentity.current = null;
      router.push(`/app/research/${receipt.research_run_id}`);
    } catch (failure) {
      if (!sessionValid.current) return;
      if (failure instanceof ResearchApiError && failure.status === 401) { expireSession(); return; }
      setActionError(failure instanceof ResearchApiError ? failure.code : "backend_unavailable");
      setRevision((value) => value + 1);
    } finally { if (!accepted) { submitting.current = false; setSaving(false); } }
  }

  return <AccountShell>
    <Link className="underline" href="/app">← {copy.workspace}</Link>
    <h1 className={styles.heading}>{copy.title}</h1><p className={`${styles.muted} mb-7`}>{copy.intro}</p>
    {error && <div role="alert" className={styles.error}>{researchError(locale, error)} <button className="cursor-pointer underline" onClick={() => setRevision((value) => value + 1)}>{copy.retry}</button></div>}
    {actionError && <div role="alert" className={styles.error}>{researchError(locale, actionError)}</div>}
    {companyUnavailable && <p role="status" className={styles.error}>{locale === "zh" ? "入口选择的公司已不可用，请从当前目录重新选择。" : "The company selected at entry is unavailable. Choose another company from the directory."}</p>}
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <section className={styles.card}><h2 className={styles.subheading}>{copy.newResearch}</h2>
        <label className="mb-5 block" htmlFor="research-company-search">{copy.companySearch}<input id="research-company-search" className={`${styles.input} mt-2`} type="search" maxLength={64} value={companyQuery} disabled={saving} onChange={(event) => setCompanyQuery(event.target.value)} /></label>
        {!loaded ? <p role="status">{copy.loading}</p> : error && companies.length === 0 ? null : companies.length === 0 ? <p className={styles.empty}>{companyQuery ? copy.noCompanyMatches : copy.noCompanies}</p> : <form className="space-y-5" onSubmit={(event) => void submit(event)}>
          <label className="block">{copy.company}<select id="research-company" className={`${styles.input} mt-2`} required value={instrument} onChange={(event) => setInstrument(event.target.value)}><option value="">—</option>{companies.map((company) => <option key={company.instrument_id} value={company.instrument_id}>{company.current_symbol} · {company.company_name}</option>)}</select></label>
          <label className="block">{copy.question}<textarea id="research-question" className={`${styles.input} mt-2 min-h-28 resize-y`} required maxLength={2000} value={question} onChange={(event) => setQuestion(event.target.value)} /></label>
          <label className="block">{copy.horizon}<input id="research-horizon" className={`${styles.input} mt-2`} required maxLength={64} value={horizon} onChange={(event) => setHorizon(event.target.value)} /></label>
          <label className="block">{copy.mode}<select className={`${styles.input} mt-2`} value={collection ? "collection" : "model"} onChange={(event) => setCollection(event.target.value === "collection")}><option value="collection">{copy.collection}</option><option value="model" disabled={!modelsEnabled}>{copy.full}</option></select></label>
          {!modelsEnabled && <p className={`${styles.muted} text-xs`}>{copy.disabled}</p>}
          <fieldset className="space-y-3 rounded-lg border border-[#d9d5bf] p-4"><legend className="px-2 font-semibold">{copy.budgets}</legend>
            <label className="block">{copy.cost}<input className={`${styles.input} mt-2`} type="number" min={collection ? 0 : 0.01} max={1} step="0.01" required value={cost} onChange={(event) => setCost(event.target.value)} /></label>
            <label className="block">{copy.seconds}<input className={`${styles.input} mt-2`} type="number" min={1} max={120} step={1} required value={seconds} onChange={(event) => setSeconds(event.target.value)} /></label>
            {!collection && <label className="block">{copy.llm}<input className={`${styles.input} mt-2`} type="number" min={1} max={10} step={1} required value={llm} onChange={(event) => setLlm(event.target.value)} /></label>}
            <p className={`${styles.muted} text-xs`}>{copy.budgetNote}</p>
          </fieldset>
          {collection && <p className={`${styles.muted} text-xs`}>{copy.collectingNote}</p>}
          <button className={`${styles.button} w-full`} disabled={saving || !!error}>{saving ? copy.submitting : copy.submit}</button>
        </form>}
      </section>
      <section className={styles.card}><div className="mb-5 flex items-start justify-between gap-4"><h2 className="text-xl font-semibold">{copy.recent}</h2><button className="cursor-pointer underline" onClick={() => setRevision((value) => value + 1)}>{copy.refresh}</button></div>
        {!loaded ? <p role="status">{copy.loading}</p> : runs.length === 0 ? <p className={styles.empty}>{copy.empty}</p> : <ul className="space-y-5">{runs.map((run) => <li key={run.research_run_id} className="rounded-lg border border-[#d9d5bf] p-4 [overflow-wrap:anywhere]">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2"><strong className="text-lg">{run.ticker}</strong><span className="rounded-full bg-[#edebe1] px-3 py-1 text-xs">{researchLabel(locale, run.research_completion === "budget_exhausted" ? run.research_completion : run.status)}</span></div>
          <p className="mb-2 whitespace-pre-wrap">{run.query}</p><p className={`${styles.muted} text-xs`}>{researchTime(locale, run.requested_at)} · {run.horizon}</p><p className={`${styles.muted} my-2 text-xs`}>{copy.task}: {run.research_run_id}</p>
          <Link className="font-medium text-[#855d21] underline" href={`/app/research/${run.research_run_id}`}>{copy.view} →</Link>
        </li>)}</ul>}
      </section>
    </div>
  </AccountShell>;
}
