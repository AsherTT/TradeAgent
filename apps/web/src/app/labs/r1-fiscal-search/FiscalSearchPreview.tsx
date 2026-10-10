"use client";

import Link from "next/link";
import { useState } from "react";
import { SearchClearButton } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchClearButton";
import { SearchEmptyMessage } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchEmptyMessage";
import { SearchGuidance } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchGuidance";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";

const initialQuery = "HOOD pages";
const sampleClassName = "mx-auto w-[317.375px] max-w-full bg-[#292931] min-[768px]:w-[657.2px] min-[1024px]:w-[966px]";
const steps = [
  "Edit the demo input. Clear Search appears only while the input contains text.",
  "Hover over Clear Search, then click it. The input becomes empty and the clear count increases by one.",
  "Reset the example. Use Tab to focus Clear Search and inspect its focus outline, then press Enter once.",
  "Reset again. Focus Clear Search with Tab and press and release Space once. Each activation increases the count only once.",
  "Switch between Chinese and English after editing the input. The input and clear count stay unchanged; refreshing keeps the language preference.",
  "Check viewport widths of 1440, 768 and 390 pixels. Samples stay centered without horizontal overflow.",
] as const;

export function FiscalSearchPreview() {
  const { t } = useLanguage();
  const [query, setQuery] = useState(initialQuery);
  const [clearCount, setClearCount] = useState(0);

  function clearQuery() {
    setQuery("");
    setClearCount((count) => count + 1);
  }

  function resetExample() {
    setQuery(initialQuery);
    setClearCount(0);
  }

  return (
    <div className="mx-auto max-w-[1100px] px-4">
      <header className="mb-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-xl font-semibold">{t("Fiscal search component preview")}</h1>
          <div className="[&_button[aria-pressed=true]]:text-[#191816]">
            <LanguageSwitcher appearance="account" />
          </div>
        </div>
        <p className="mt-3 text-sm leading-6 text-white/70">
          {t("This page demonstrates three captured Fiscal search components in a development container. It is not the complete search dialog, results list or company page.")}
        </p>
        <p className="mt-2 text-sm leading-6 text-white/70">
          {t("Source samples retain their English text for comparison. Language switching translates only this preview's instructions and controls.")}
        </p>
        <nav aria-label={t("Preview navigation")} className="mt-4 flex flex-wrap gap-x-6 gap-y-3 text-sm">
          <Link className="underline underline-offset-4 hover:text-[#fdcc6a]" href="/app">{t("Research workspace")}</Link>
          <Link className="underline underline-offset-4 hover:text-[#fdcc6a]" href="/labs/r1-company-data-status">{t("Company source component preview")}</Link>
          <Link className="underline underline-offset-4 hover:text-[#fdcc6a]" href="/">{t("Home")}</Link>
        </nav>
      </header>

      <div className="space-y-8">
        <section aria-labelledby="clear-demo-heading">
          <h2 id="clear-demo-heading" className="text-lg font-semibold">{t("Clear action demo")}</h2>
          <p id="query-demo-description" className="mt-2 text-sm leading-6 text-white/70">
            {t("The input is only a clear-button demo. It does not search securities or request data.")}
          </p>
          <div className="my-4 max-w-lg">
            <label htmlFor="fiscal-demo-query" className="mb-2 block text-sm font-medium">{t("Demo search text")}</label>
            <input
              id="fiscal-demo-query"
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-describedby="query-demo-description"
              className="w-full rounded-md border border-white/30 bg-[#202026] px-3 py-2 text-base text-white outline-offset-2 focus-visible:outline-2 focus-visible:outline-[#fdcc6a]"
            />
          </div>
          <div lang="en" className={`${sampleClassName} flex min-h-[62px] items-center justify-center`}>
            {query.length > 0 && <SearchClearButton onClear={clearQuery} />}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={resetExample}
              className="cursor-pointer rounded-md border border-white/30 px-3 py-2 text-sm hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#fdcc6a]"
            >
              {t("Reset example")}
            </button>
            <p aria-live="polite" aria-atomic="true" className="text-sm text-white/80">
              {t("Clear count:")} {clearCount}
            </p>
          </div>
        </section>

        <section aria-labelledby="empty-sample-heading">
          <h2 id="empty-sample-heading" className="text-lg font-semibold">{t("Static no-results sample")}</h2>
          <p className="mb-4 mt-2 text-sm leading-6 text-white/70">
            {t("This captured message is always shown as a static sample. It is not a result of the demo input.")}
          </p>
          <div lang="en" className={sampleClassName}>
            <SearchEmptyMessage />
          </div>
        </section>

        <section aria-labelledby="guidance-sample-heading">
          <h2 id="guidance-sample-heading" className="text-lg font-semibold">{t("Static search guidance sample")}</h2>
          <p className="mb-4 mt-2 text-sm leading-6 text-white/70">
            {t("The source guidance keeps its original text. Its navigation tip does not mean result selection or keyboard navigation is implemented on this page.")}
          </p>
          <div lang="en" className={sampleClassName}>
            <SearchGuidance />
          </div>
        </section>

        <section aria-labelledby="manual-check-heading">
          <h2 id="manual-check-heading" className="text-lg font-semibold">{t("Manual verification steps")}</h2>
          <ol className="mt-3 list-decimal space-y-2 pl-6 text-sm leading-6 text-white/80">
            {steps.map((step) => <li key={step}>{t(step)}</li>)}
          </ol>
        </section>
      </div>
    </div>
  );
}
