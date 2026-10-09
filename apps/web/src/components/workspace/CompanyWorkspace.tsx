"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AccountShell } from "@/components/accounts/AccountShell";
import { accountError, readApiError } from "@/components/accounts/copy";
import { accountStyles as styles } from "@/components/accounts/styles";
import { ResearchApiError, researchRequest } from "@/components/research/api";
import { researchActive } from "@/components/research/contracts";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import type { CompanyDetail } from "./contracts";
import { PageControls, ResearchCards } from "./ResearchCards";
import { ResearchChangePanel } from "./ResearchChangePanel";

export function CompanyWorkspace({ instrumentId }: { instrumentId: string }) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const router = useRouter();
  const [detail, setDetail] = useState<CompanyDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [pending, setPending] = useState(true);
  const [saving, setSaving] = useState(false);
  const changingFollow = useRef(false);
  const sessionValid = useRef(true);
  const stopLoading = useRef<(() => void) | null>(null);
  const expireSession = useCallback(() => {
    sessionValid.current = false;
    stopLoading.current?.();
    setDetail(null);
    setPending(false);
    setError("authentication_required");
    router.replace("/login");
    router.refresh();
  }, [router]);
  useEffect(() => {
    if (!sessionValid.current) return;
    const controller = new AbortController();
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    function stop() {
      active = false;
      controller.abort();
      clearTimeout(timer);
    }
    stopLoading.current = stop;
    async function load() {
      try {
        const value = await researchRequest<CompanyDetail>(
          `companies/${instrumentId}?limit=6&research_offset=${offset}`,
          { signal: controller.signal },
        );
        if (!active || !sessionValid.current) return;
        setDetail(value);
        setPending(false);
        setError(null);
        if (value.research.items.some(researchActive))
          timer = setTimeout(() => void load(), 5000);
      } catch (failure) {
        if (!active || !sessionValid.current) return;
        if (failure instanceof ResearchApiError && failure.status === 401) {
          expireSession();
          return;
        }
        setError(
          failure instanceof ResearchApiError
            ? failure.code
            : "backend_unavailable",
        );
        setPending(false);
      }
    }
    void load();
    return stop;
  }, [instrumentId, offset, revision, expireSession]);

  async function changeFollow() {
    if (!detail || changingFollow.current || !sessionValid.current) return;
    changingFollow.current = true;
    setSaving(true);
    try {
      const response = await fetch(
        `/api/backend/workspace/watchlist/${instrumentId}`,
        {
          method: detail.is_followed ? "DELETE" : "POST",
          signal: AbortSignal.timeout(12000),
        },
      );
      if (!sessionValid.current) return;
      if (response.status === 401) {
        expireSession();
        return;
      }
      if (!response.ok) {
        setError(await readApiError(response));
        return;
      }
      setRevision((value) => value + 1);
    } catch {
      if (!sessionValid.current) return;
      setError("backend_unavailable");
    } finally {
      changingFollow.current = false;
      setSaving(false);
    }
  }
  return (
    <AccountShell>
      <Link href="/app" className="text-sm text-[#855d21] underline">
        ← {zh ? "返回研究门户" : "Back to research portal"}
      </Link>
      {error && (
        <div role="alert" className={styles.error}>
          {accountError(locale, error)}{" "}
          <button
            className="cursor-pointer underline"
            onClick={() => setRevision((value) => value + 1)}
          >
            {zh ? "重试" : "Retry"}
          </button>
        </div>
      )}
      {pending && (
        <p role="status" className="py-12 text-sm text-[#777065]">
          {zh ? "正在加载公司…" : "Loading company…"}
        </p>
      )}
      {detail && !error && (
        <>
          <header className="my-7 flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className={styles.eyebrow}>
                {detail.company.exchange} · {detail.company.current_symbol}
              </p>
              <h1 className={styles.heading}>{detail.company.company_name}</h1>
              <p className="text-sm text-[#777065]">
                {zh ? "记账币种" : "Currency"} {detail.company.currency} ·{" "}
                {zh ? "已接入的公司记录" : "Connected company record"}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                className={styles.button}
                disabled={saving}
                onClick={() => void changeFollow()}
              >
                {saving
                  ? zh
                    ? "处理中…"
                    : "Working…"
                  : detail.is_followed
                    ? zh
                      ? "取消关注"
                      : "Unfollow"
                    : zh
                      ? "关注公司"
                      : "Follow company"}
              </button>
              <Link
                className="rounded-md bg-[#191816] px-5 py-3 text-sm font-medium text-[#fffdf8]"
                href={`/app/research?company=${instrumentId}`}
              >
                {zh ? "发起研究" : "Start research"} →
              </Link>
            </div>
          </header>
          <nav
            aria-label={zh ? "公司章节" : "Company sections"}
            className="mb-8 flex flex-wrap gap-6 border-b border-[#d9d5bf] pb-4 text-sm"
          >
            <a href="#company-research">{zh ? "我的研究" : "My research"}</a>
            {detail.research_change && <a href="#company-change">{zh ? "研究记录变化" : "Research record changes"}</a>}
            <a href="#company-capabilities">
              {zh ? "分析能力与范围" : "Analysis scope"}
            </a>
          </nav>
          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
            <section
              id="company-research"
              className={`${styles.card} scroll-mt-6`}
            >
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-medium">
                  {zh ? "这家公司的本人研究" : "Your research on this company"}
                </h2>
                <span className="text-xs text-[#777065]">
                  {zh
                    ? `共 ${detail.research.total} 条`
                    : `${detail.research.total} total`}
                </span>
              </div>
              <ResearchCards
                runs={detail.research.items}
                empty={
                  zh
                    ? "还没有研究记录。设定问题与预算后，可以发起第一项研究。"
                    : "No research yet. Set a question and budget to begin."
                }
              />
              <PageControls
                {...detail.research}
                disabled={saving}
                onChange={(value) => {
                  setPending(true);
                  setOffset(value);
                }}
              />
            </section>
            <section
              id="company-capabilities"
              className={`${styles.card} scroll-mt-6`}
            >
              <h2 className="mb-5 text-xl font-medium">
                {zh ? "分析能力与范围" : "Analysis scope"}
              </h2>
              <ul className="space-y-5 text-sm leading-7">
                <li>
                  <strong>
                    {zh
                      ? "研究任务与部分报告"
                      : "Research tasks & partial reports"}
                  </strong>
                  <p className="text-[#777065]">
                    {zh
                      ? "可提交、查看状态与取消。已保存报告会说明来源、时间、质量和缺口。"
                      : "Submit, inspect and cancel tasks. Saved reports describe sources, timing, quality and gaps."}
                  </p>
                </li>
                <li>
                  <strong>
                    {zh
                      ? "多期财务 · 待接入"
                      : "Multi-period financials · upcoming"}
                  </strong>
                  <p className="text-[#777065]">
                    {zh
                      ? "当前年度事实不代表多期终端；表格、趋势和分部数据将在后续阶段接入。"
                      : "Current annual facts are not a multi-period terminal. Tables, trends and segments will follow."}
                  </p>
                </li>
                <li>
                  <strong>
                    {zh
                      ? "原文核验与论点跟踪 · 待接入"
                      : "Source reading & thesis tracking · upcoming"}
                  </strong>
                  <p className="text-[#777065]">
                    {zh
                      ? "后续提供授权片段定位和论点版本；当前不展示虚构评分或预测成熟结果。"
                      : "Authorized excerpt location and thesis versions will follow. No invented scores or mature forecasts are shown."}
                  </p>
                </li>
              </ul>
            </section>
          </div>
          {detail.research_change && <ResearchChangePanel change={detail.research_change} />}
          <p className="mt-7 text-xs leading-6 text-[#777065]">
            {zh
              ? "公司身份来自已接入目录；这里的研究只属于当前账户。目录不代表全市场覆盖或实时行情。"
              : "Company identity comes from the connected directory; research belongs to this account. The directory is not full-market coverage or a live feed."}
          </p>
        </>
      )}
    </AccountShell>
  );
}
