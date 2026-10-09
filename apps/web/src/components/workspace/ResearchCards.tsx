"use client";

import Link from "next/link";
import type { ResearchSummary } from "@/components/research/contracts";
import { researchLabel, researchTime } from "@/components/research/copy";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";

export function ResearchCards({
  runs,
  empty,
}: {
  runs: ResearchSummary[];
  empty: string;
}) {
  const { locale } = useLanguage();
  if (runs.length === 0)
    return <p className="py-6 text-sm leading-7 text-[#777065]">{empty}</p>;
  return (
    <ul className="space-y-3">
      {runs.map((run) => (
        <li
          key={run.research_run_id}
          className="rounded-xl border border-[#e7e2d5] bg-[#faf8f1] p-4 [overflow-wrap:anywhere]"
        >
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <Link
              className="font-semibold hover:underline"
              href={`/app/companies/${run.instrument_id}`}
            >
              {run.ticker}
            </Link>
            <span className="rounded-full bg-[#edebe1] px-3 py-1 text-[11px]">
              {researchLabel(
                locale,
                run.research_completion === "budget_exhausted"
                  ? run.research_completion
                  : run.status,
              )}
            </span>
          </div>
          <p className="mb-3 whitespace-pre-wrap text-sm leading-6">
            {run.query}
          </p>
          <p className="mb-3 text-xs leading-5 text-[#777065]">
            {researchTime(locale, run.requested_at)} · {run.horizon}
          </p>
          <Link
            href={`/app/research/${run.research_run_id}`}
            className="text-xs font-medium text-[#855d21] underline"
          >
            {locale === "zh" ? "查看任务与报告" : "View task & report"} →
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function PageControls({
  total,
  offset,
  limit,
  onChange,
  disabled = false,
}: {
  total: number;
  offset: number;
  limit: number;
  onChange: (offset: number) => void;
  disabled?: boolean;
}) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  if (total <= limit && offset === 0) return null;
  return (
    <nav
      aria-label={zh ? "列表翻页" : "List pagination"}
      className="mt-5 flex flex-wrap items-center justify-between gap-3 text-xs text-[#777065]"
    >
      <button
        className="cursor-pointer rounded border border-[#d9d5bf] px-3 py-2 disabled:cursor-default disabled:opacity-40"
        disabled={disabled || offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        {zh ? "上一页" : "Previous"}
      </button>
      <span>
        {zh ? `共 ${total} 条` : `${total} total`} ·{" "}
        {offset < total
          ? `${offset + 1}–${Math.min(offset + limit, total)}`
          : zh
            ? "当前页无记录"
            : "No items on this page"}
      </span>
      <button
        className="cursor-pointer rounded border border-[#d9d5bf] px-3 py-2 disabled:cursor-default disabled:opacity-40"
        disabled={disabled || offset + limit >= total || offset + limit > 10000}
        onClick={() => onChange(offset + limit)}
      >
        {zh ? "下一页" : "Next"}
      </button>
    </nav>
  );
}
