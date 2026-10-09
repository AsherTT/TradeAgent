"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { Account } from "@/lib/account-api";
import type { Company } from "@/components/research/contracts";
import { ResearchApiError, researchRequest } from "@/components/research/api";
import type { PortalSummary } from "@/components/workspace/contracts";
import { startWorkspacePolling } from "@/components/workspace/polling";
import { PortalResearchChange } from "@/components/workspace/PortalResearchChange";
import {
  PageControls,
  ResearchCards,
} from "@/components/workspace/ResearchCards";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { accountStyles as styles } from "./styles";
import { AccountShell } from "./AccountShell";
import { accountCopy, accountError, readApiError } from "./copy";

export function Workspace({
  account,
  unavailable,
}: {
  account: Account | null;
  unavailable: boolean;
}) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const copy = accountCopy(locale);
  const router = useRouter();
  const [portal, setPortal] = useState<PortalSummary | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [query, setQuery] = useState("");
  const [watchOffset, setWatchOffset] = useState(0);
  const [researchOffset, setResearchOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [pending, setPending] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(
    unavailable ? "backend_unavailable" : null,
  );
  const changing = useRef(false);
  const sessionValid = useRef(true);
  const stopLoading = useRef<(() => void) | null>(null);
  const invalidateSession = useCallback(() => {
    sessionValid.current = false;
    stopLoading.current?.();
    setPortal(null);
    setCompanies([]);
    router.replace("/login");
    router.refresh();
  }, [router]);

  useEffect(() => {
    if (!sessionValid.current) return;
    const stop = startWorkspacePolling({
      load: (signal) =>
        Promise.all([
          researchRequest<PortalSummary>(
            `portal?limit=6&watchlist_offset=${watchOffset}&research_offset=${researchOffset}`,
            { signal },
          ),
          researchRequest<Company[]>(
            `companies?query=${encodeURIComponent(query)}`,
            { signal },
          ),
        ]),
      onUpdate: ([snapshot, directory]) => {
        if (!sessionValid.current) return false;
        setPortal(snapshot);
        setCompanies(directory);
        setPending(false);
        setError(null);
        return snapshot.active_research_total > 0;
      },
      onFailure: (failure) => {
        if (!sessionValid.current) return;
        if (failure instanceof ResearchApiError && failure.status === 401) {
          invalidateSession();
          return;
        }
        setError(
          failure instanceof ResearchApiError
            ? failure.code
            : "backend_unavailable",
        );
        setPending(false);
      },
    });
    stopLoading.current = stop;
    return stop;
  }, [query, watchOffset, researchOffset, revision, invalidateSession]);

  async function changeFollow(company: Company, remove: boolean) {
    if (changing.current) return;
    changing.current = true;
    setSaving(company.instrument_id);
    try {
      const response = await fetch(
        `/api/backend/workspace/watchlist/${company.instrument_id}`,
        {
          method: remove ? "DELETE" : "POST",
          signal: AbortSignal.timeout(12000),
        },
      );
      if (!sessionValid.current) return;
      if (response.status === 401) {
        invalidateSession();
        return;
      }
      if (!response.ok) {
        setError(await readApiError(response));
        return;
      }
      setWatchOffset(0);
      setPending(true);
      setRevision((value) => value + 1);
    } catch {
      setError("backend_unavailable");
    } finally {
      changing.current = false;
      setSaving(null);
    }
  }
  async function logout() {
    if (changing.current) return;
    changing.current = true;
    setSaving("logout");
    try {
      const response = await fetch("/api/backend/auth/logout", {
        method: "POST",
        signal: AbortSignal.timeout(12000),
      });
      if (!sessionValid.current) return;
      if (response.status === 401) {
        invalidateSession();
        return;
      }
      if (!response.ok) {
        setError(await readApiError(response));
        return;
      }
      invalidateSession();
    } catch {
      setError("backend_unavailable");
    } finally {
      changing.current = false;
      setSaving(null);
    }
  }
  const followedIds = new Set(
    portal?.watchlist.items.map((company) => company.instrument_id),
  );
  function companyRow(company: Company, followed: boolean, allowFollow = true) {
    return (
      <li
        key={company.instrument_id}
        className="flex flex-wrap items-center justify-between gap-3 border-b border-[#ece8dd] py-4 last:border-b-0"
      >
        <Link
          href={`/app/companies/${company.instrument_id}`}
          className="min-w-0 flex-1 [overflow-wrap:anywhere] hover:text-[#855d21]"
        >
          <strong className="text-sm">{company.current_symbol}</strong>
          <p className="my-1 text-sm leading-6">{company.company_name}</p>
          <span className="text-xs text-[#777065]">
            {company.exchange} · {company.currency}
          </span>
        </Link>
        {allowFollow ? (
          <button
            className={`${styles.button} min-w-[76px] px-3 py-2 text-xs`}
            disabled={saving !== null || pending}
            onClick={() => void changeFollow(company, followed)}
          >
            {saving === company.instrument_id
              ? copy.pending
              : followed
                ? copy.unfollow
                : copy.follow}
          </button>
        ) : (
          <Link
            className="text-xs text-[#855d21] underline"
            href={`/app/companies/${company.instrument_id}`}
          >
            {zh ? "查看公司" : "Open company"} →
          </Link>
        )}
        {followed && allowFollow && !pending && <PortalResearchChange
          instrumentId={company.instrument_id}
          change={portal?.research_changes?.find((item) => item.instrument_id === company.instrument_id)?.research_change}
        />}
      </li>
    );
  }
  return (
    <AccountShell>
      <section className="mb-7 flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className={styles.eyebrow}>
            {zh ? "你的研究空间" : "YOUR RESEARCH SPACE"}
          </p>
          <h1 className={styles.heading}>
            {zh ? "公司、研究与下一步。" : "Companies, research, next steps."}
          </h1>
          {account && (
            <p className={`${styles.muted} text-xs [overflow-wrap:anywhere]`}>
              {account.email}
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <button
            className="cursor-pointer rounded-md border border-[#c9c4b7] px-4 py-2 text-xs"
            disabled={saving !== null}
            onClick={() => setRevision((value) => value + 1)}
          >
            {zh ? "刷新" : "Refresh"}
          </button>
          <button
            className="cursor-pointer rounded-md border border-[#c9c4b7] px-4 py-2 text-xs"
            disabled={saving !== null}
            onClick={() => void logout()}
          >
            {copy.logout}
          </button>
        </div>
      </section>
      {error && (
        <div className={styles.error} role="alert">
          {accountError(locale, error)}{" "}
          <button
            className="cursor-pointer underline"
            onClick={() => {
              if (unavailable) router.refresh();
              setRevision((value) => value + 1);
            }}
          >
            {copy.retry}
          </button>
        </div>
      )}
      {pending && (
        <p role="status" className="py-6 text-sm text-[#777065]">
          {copy.loading}
        </p>
      )}
      {portal && !error && (
        <>
          <div className="mb-7 grid grid-cols-3 gap-3 md:gap-5">
            {[
              [
                zh ? "可用关注公司" : "Available follows",
                portal.watchlist.total,
              ],
              [
                zh ? "研究记录" : "Research records",
                portal.recent_research.total,
              ],
              [zh ? "活动任务" : "Active tasks", portal.active_research_total],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-xl border border-[#d9d5bf] bg-[#fffdf8] p-4 md:p-6"
              >
                <p className="mb-3 text-xs leading-5 text-[#777065]">{label}</p>
                <p className="text-3xl font-normal">{value}</p>
              </div>
            ))}
          </div>
          <div className="mb-7 flex flex-wrap items-center justify-between gap-4 rounded-xl bg-[#262e3a] px-5 py-5 text-[#fffdf8]">
            <div>
              <h2 className="mb-1 text-base">
                {zh
                  ? "从一个明确的问题开始研究"
                  : "Begin with a clear research question"}
              </h2>
              <p className="text-xs leading-6 text-[#bbc0c6]">
                {zh
                  ? "选择公司、设定预算，查看真实任务状态与报告缺口。"
                  : "Choose a company and budget, then follow actual task status and report gaps."}
              </p>
            </div>
            <Link
              href="/app/research"
              className="rounded-md bg-[#fdcc6a] px-5 py-2.5 text-sm font-medium text-[#191816]"
            >
              {zh ? "发起研究" : "Start research"} →
            </Link>
          </div>
          <div className="grid items-start gap-6 lg:grid-cols-2">
            <section className={styles.card}>
              <h2 className="mb-4 text-xl font-medium">{copy.watchlist}</h2>
              {portal.watchlist.items.length === 0 ? (
                <p className={styles.empty}>{copy.empty}</p>
              ) : (
                <ul>
                  {portal.watchlist.items.map((company) =>
                    companyRow(company, true),
                  )}
                </ul>
              )}
              <PageControls
                {...portal.watchlist}
                disabled={saving !== null}
                onChange={(value) => {
                  setPending(true);
                  setWatchOffset(value);
                }}
              />
            </section>
            <section className={styles.card}>
              <h2 className="mb-4 text-xl font-medium">
                {zh ? "活动研究" : "Active research"}
              </h2>
              <ResearchCards
                runs={portal.active_research}
                empty={
                  zh
                    ? "暂无活动任务。你可以查看已有报告，或发起新研究。"
                    : "No active tasks. Read an existing report or start new research."
                }
              />
              {portal.active_research_total > portal.active_research.length && (
                <Link
                  className="mt-4 block text-xs underline"
                  href="/app/research"
                >
                  {zh ? "查看最近50条研究任务" : "View the latest 50 research tasks"}
                </Link>
              )}
            </section>
            <section className={styles.card}>
              <h2 className="mb-4 text-xl font-medium">
                {zh ? "最近研究" : "Recent research"}
              </h2>
              <ResearchCards
                runs={portal.recent_research.items}
                empty={
                  zh
                    ? "还没有保存的研究记录。"
                    : "No saved research records yet."
                }
              />
              <PageControls
                {...portal.recent_research}
                disabled={saving !== null}
                onChange={setResearchOffset}
              />
            </section>
            <section id="companies" className={`${styles.card} scroll-mt-6`}>
              <h2 className="mb-4 text-xl font-medium">{copy.companies}</h2>
              <label
                htmlFor="company-search"
                className="mb-2 block text-xs text-[#777065]"
              >
                {copy.search}
              </label>
              <input
                id="company-search"
                className={styles.input}
                type="search"
                maxLength={64}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <p className="mt-3 text-xs leading-5 text-[#777065]">
                {zh
                  ? "当前查询最多显示50条已接入记录；进入公司页可管理关注。"
                  : "Search shows up to 50 connected records. Manage follows from the company page."}
              </p>
              {companies.length === 0 ? (
                <p className={styles.empty}>{copy.noCompanies}</p>
              ) : (
                <ul>
                  {companies.map((company) =>
                    companyRow(
                      company,
                      followedIds.has(company.instrument_id),
                      false,
                    ),
                  )}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
      <p id="data-scope" className="mt-7 scroll-mt-6 text-xs leading-6 text-[#777065]">
        {zh
          ? "目录不是全市场行情；研究记录仅属于当前账户。多期财务、原文核验与论点界面仍在逐项接入。"
          : "This directory is not a market-wide feed; research belongs to this account. Multi-period financials, source verification and thesis views are being added incrementally."}
      </p>
    </AccountShell>
  );
}
