"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { SearchDialogFrame } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchDialogFrame";
import { SearchInputBar } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchInputBar";
import { SearchCategoryBar } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchCategoryBar";
import { SearchEmptyMessage } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchEmptyMessage";
import { SearchGuidance } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchGuidance";
import { SearchResultRow } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchResultRow";
import { defaultSearchResults } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/search-reference-data";
import type { SearchCategory, SearchResult } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/search-types";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import styles from "./FiscalSearchPreview.module.css";

export function FiscalSearchPreview() {
  const { t } = useLanguage();
  const [open, setOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<SearchCategory>("all");
  const [activeIndex, setActiveIndex] = useState(0);
  const [selected, setSelected] = useState<SearchResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const launchRef = useRef<HTMLButtonElement>(null);
  const dialogRegionRef = useRef<HTMLDivElement>(null);
  const results = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    return defaultSearchResults.filter((result) =>
      (category === "all" || result.kind === category) &&
      (!term || `${result.name} ${result.market ?? ""}`.toLocaleLowerCase().includes(term)));
  }, [query, category]);
  const activeResultId = results[activeIndex] ? `fiscal-result-${activeIndex}` : undefined;

  useEffect(() => {
    if (open) inputRef.current?.focus();
    else launchRef.current?.focus();
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previousOverflow; };
  }, [open]);

  function choose(result: SearchResult) {
    setSelected(result);
    setOpen(false);
  }
  function onInputKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Tab" && !event.shiftKey && query.length === 0) {
      event.preventDefault();
      setActiveIndex(-1);
    } else if ((event.key === "ArrowDown" || event.key === "ArrowUp") && results.length > 0) {
      event.preventDefault();
      const next = activeIndex < 0 ? (event.key === "ArrowDown" ? 0 : results.length - 1)
        : (activeIndex + (event.key === "ArrowDown" ? 1 : -1) + results.length) % results.length;
      setActiveIndex(next);
      document.getElementById(`fiscal-result-${next}`)?.scrollIntoView({ block: "nearest" });
    } else if (event.key === "Enter" && results[activeIndex]) {
      event.preventDefault();
      choose(results[activeIndex]);
    }
  }
  function onDialogKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
    } else if (event.key === "Tab") {
      const controls = dialogRegionRef.current?.querySelectorAll<HTMLElement>("button, input, a[href]");
      if (!controls?.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }

  return (
    <>
      <div className="mx-auto max-w-[1000px] px-5 py-8" inert={open}>
        <header className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-xl font-semibold">{t("Fiscal search component preview")}</h1>
          <div className="[&_button[aria-pressed=true]]:text-[#191816]"><LanguageSwitcher appearance="account" /></div>
        </header>
        <p className="mt-5 max-w-3xl text-sm leading-6 text-white/70">
          {t("This preview restores the captured search dialog and 30 reference results. Filtering uses these samples only; global search, company pages and listing expansion are still pending.")}
        </p>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-white/70">
          {t("Close the dialog to change language. Your query and category are preserved when you reopen it. The source page-navigation tip is retained for comparison; page search is not connected yet.")}
        </p>
        <button ref={launchRef} type="button" onClick={() => setOpen(true)} className="mt-5 cursor-pointer rounded-full border border-white/40 px-5 py-2 hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2">
          {t("Open search")}
        </button>
        {selected && <p className="mt-6 text-sm" role="status">{t("Selected reference result:")} {selected.name} · <a className="underline" href={`https://fiscal.ai${selected.href}`} target="_blank" rel="noreferrer">{t("View source page")}</a></p>}
        <nav aria-label={t("Preview navigation")} className="mt-8 flex flex-wrap gap-6 text-sm">
          <Link className="underline" href="/app">{t("Research workspace")}</Link>
          <Link className="underline" href="/labs/r1-company-data-status">{t("Company source component preview")}</Link>
          <Link className="underline" href="/">{t("Home")}</Link>
        </nav>
      </div>
      {open && <div ref={dialogRegionRef} onKeyDown={onDialogKeyDown}>
        <SearchDialogFrame onClose={() => setOpen(false)}
          header={<SearchInputBar query={query} onQueryChange={(value) => { setQuery(value); setActiveIndex(0); }} onKeyDown={onInputKeyDown} inputRef={inputRef} activeResultId={activeResultId} />}
          footer={<SearchGuidance translate={t} />}>
          <div className={styles.card}>
            <SearchCategoryBar category={category} onCategoryChange={(value) => { setCategory(value); setActiveIndex(0); inputRef.current?.focus(); }} />
            <div className={styles.divider} />
            <div className={styles.scroll} id="fiscal-search-results" role="listbox" aria-label={t("Search results")}>
              {results.length ? results.map((result, index) =>
                <SearchResultRow key={result.href} result={result} active={index === activeIndex} showInvestorType={category !== "investor" || query.length > 0} id={`fiscal-result-${index}`} onSelect={(event) => { event.preventDefault(); choose(result); }} />)
                : <SearchEmptyMessage message={t("No results found...")} />}
            </div>
          </div>
        </SearchDialogFrame>
      </div>}
    </>
  );
}
