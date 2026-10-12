"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { SearchDialogFrame } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchDialogFrame";
import { SearchInputBar } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchInputBar";
import { SearchClearBar } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchClearBar";
import { SearchCategoryBar } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchCategoryBar";
import { SearchEmptyMessage } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchEmptyMessage";
import { SearchGuidance } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchGuidance";
import { SearchResultRow } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchResultRow";
import panel from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchResultsPanel.module.css";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { companyDestination, directoryLogo, type DiscoveryPage } from "./company-discovery";
import { useCompanyDiscovery } from "./useCompanyDiscovery";
import styles from "./CompanyDiscoverySearch.module.css";

export function CompanyDiscoverySearch({ referenceControl }: { referenceControl?: ReactNode }) {
  const { locale, t } = useLanguage();
  const zh = locale === "zh";
  const router = useRouter();
  const [open, setOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [revision, setRevision] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const launchRef = useRef<HTMLButtonElement>(null);
  const regionRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const params = new URLSearchParams({ query, limit: "20", offset: String(offset) });
  const { data, error, pending } = useCompanyDiscovery<DiscoveryPage>(`company-discovery?${params}`, open, revision);
  const results = data?.items ?? [];
  const target = results[activeIndex];

  useEffect(() => {
    if (open) inputRef.current?.focus();
    else launchRef.current?.focus();
  }, [open]);

  function clearSearch() {
    setQuery("");
    setOffset(0);
    setActiveIndex(0);
    if (resultsRef.current) resultsRef.current.scrollTop = 0;
    inputRef.current?.focus({ preventScroll: true });
  }
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previous; };
  }, [open]);

  function onInputKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Tab" && !event.shiftKey && query.length === 0) {
      setActiveIndex(-1);
    } else if ((event.key === "ArrowDown" || event.key === "ArrowUp") && results.length) {
      event.preventDefault();
      const next = activeIndex < 0 ? (event.key === "ArrowDown" ? 0 : results.length - 1)
        : (activeIndex + (event.key === "ArrowDown" ? 1 : -1) + results.length) % results.length;
      setActiveIndex(next);
      document.getElementById(`directory-result-${next}`)?.scrollIntoView?.({ block: "nearest" });
    } else if (event.key === "Enter" && target) {
      event.preventDefault();
      router.push(companyDestination(target));
    }
  }
  function onDialogKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") { event.preventDefault(); setOpen(false); }
    if (event.key !== "Tab") return;
    const controls = regionRef.current?.querySelectorAll<HTMLElement>("button:not(:disabled), input, a[href]");
    if (!controls?.length) return;
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  const failure = error === "session_required"
    ? zh ? "请登录后查询真实公司目录。" : "Sign in to search the real company directory."
    : error === "directory_not_configured"
      ? zh ? "公司目录来源尚未配置。" : "The company directory source is not configured."
            : zh ? "公司目录暂时无法获取，请重试。" : "The company directory is temporarily unavailable. Please retry.";
  const directoryNote = zh ? "SEC 身份目录 · 不覆盖全球公司。目录记录尚不代表可发起研究。" : "SEC identity directory · Global coverage is not available. Discovery does not establish research eligibility.";
  const snapshotNote = data ? `${data.directory_total.toLocaleString()} ${zh ? "条记录" : "records"} · ${data.total.toLocaleString()} ${zh ? "条匹配" : "matches"} · ${zh ? "抓取时间" : "Fetched"} ${new Date(data.fetched_at).toLocaleString(zh ? "zh-CN" : "en-US", { timeZone: "UTC" })} UTC${data.stale ? zh ? " · 陈旧快照" : " · Stale snapshot" : ""} · ` : "";

  return <>
    <div className="mx-auto max-w-[1000px] px-5 py-8" inert={open}>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">{zh ? "公司目录搜索" : "Company directory search"}</h1>
        <div className="[&_button[aria-pressed=true]]:text-[#191816]"><LanguageSwitcher appearance="account" /></div>
      </header>
      <p className="mt-5 max-w-3xl text-sm leading-6 text-white/70">{zh ? "查询 SEC 官方发行人代码目录。已收录公司进入研究空间公司页，其他记录进入自有目录详情。SEC 不保证目录完整性或准确性，搜索结果不代表已有行情、财务或研究资格。" : "Search the SEC issuer ticker directory. Local records open the workspace company page; other records open our directory details. SEC does not guarantee completeness or accuracy. A search result does not establish market data, financials or research eligibility."}</p>
      <p className="mt-2 text-sm leading-6 text-white/70">{zh ? "关闭弹窗后可切换语言；重新打开时保留搜索内容。" : "Close the dialog to change language. Reopening preserves your query."}</p>
      <button ref={launchRef} type="button" className="mt-6 cursor-pointer rounded border border-white/30 px-4 py-2 text-sm" onClick={() => { setRevision((value) => value + 1); setOpen(true); }}>{t("Open search")}</button>
      <div>{referenceControl}</div>
      <nav className="mt-8 flex flex-wrap gap-6 text-sm" aria-label={t("Preview navigation")}>
        <Link className="underline" href="/app">{t("Research workspace")}</Link>
        <Link className="underline" href="/labs/r1-company-data-status">{t("Company source component preview")}</Link>
      </nav>
    </div>
    {open && <div ref={regionRef} onKeyDown={onDialogKeyDown}>
      <SearchDialogFrame onClose={() => setOpen(false)}
        header={<SearchInputBar query={query} placeholder={zh ? "搜索公司名称或股票代码 · SEC 目录" : "Search company name or ticker · SEC directory"} maxLength={64} inputRef={inputRef} onQueryChange={(value) => { setQuery(value); setOffset(0); setActiveIndex(0); }} onKeyDown={onInputKeyDown} />}
        footer={<SearchGuidance message={`${snapshotNote}${directoryNote}`} />}>
        <p id="fiscal-search-keyboard-help" className="sr-only">{zh ? "上下方向键选择结果，回车进入公司页，Tab 切换链接和按钮。" : "Use arrow keys to select a result, Enter to open its company page, and Tab for links and controls."}</p>
        <p className="sr-only" role="status" aria-atomic="true">{target ? `${t("Keyboard target:")} ${target.name} ${target.symbol}` : ""}</p>
        <div className={panel.card}>
          <SearchCategoryBar category="company" options={[{ value: "company", label: zh ? "SEC 公司目录" : "SEC directory" }]} onCategoryChange={() => { setActiveIndex(0); inputRef.current?.focus(); }} />
          <div className={panel.divider} />
          <div ref={resultsRef} className={panel.scroll} id="fiscal-search-results" role="region" aria-label={t("Search results")} aria-busy={pending}>
            {query.length > 0 && <SearchClearBar onClear={clearSearch} label={zh ? "清空搜索" : "Clear Search"} />}
            {pending ? <SearchEmptyMessage message={zh ? "正在查询公司目录…" : "Searching the company directory…"} />
              : error ? <><div role="alert"><SearchEmptyMessage message={failure} /></div><div className={styles.actions}>{error === "session_required" ? <Link className={styles.action} href="/login">{zh ? "登录" : "Sign in"}</Link> : <button type="button" className={styles.action} onClick={() => setRevision((value) => value + 1)}>{zh ? "重试" : "Retry"}</button>}</div></>
                : results.length ? results.map((company, index) => {
                  const href = companyDestination(company);
                  return <SearchResultRow key={`${company.cik}:${company.symbol}:${company.exchange}`} id={`directory-result-${index}`} active={index === activeIndex} showInvestorType={false} navigationHref={href} logoText={company.symbol.slice(0, 2)} result={{
                    href, kind: "company", name: company.name,
                    market: `${company.exchange ?? (zh ? "交易所未注明" : "Exchange unspecified")}:${company.symbol} · ${company.instrument_id ? zh ? "本地记录" : "Local record" : zh ? "仅目录身份" : "Directory identity only"}`,
                    avatar: null, logo: directoryLogo(company) ?? null, flag: null, listings: null, description: null,
                  }} onSelect={(event) => {
                    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
                    event.preventDefault(); router.push(href);
                  }} />;
                }) : <SearchEmptyMessage message={zh ? "该 SEC 目录中没有匹配记录；不代表这家公司不存在。" : "No match in this SEC directory; this does not mean the company does not exist."} />}
          </div>
          {data && data.total > data.limit && <div className={styles.actions}>
            <button type="button" className={styles.action} disabled={offset === 0} onClick={() => { setOffset(Math.max(0, offset - 20)); setActiveIndex(0); }}>{zh ? "上一页" : "Previous"}</button>
            <span>{offset + 1}–{Math.min(offset + data.limit, data.total)} / {data.total}</span>
            <button type="button" className={styles.action} disabled={offset + data.limit >= data.total} onClick={() => { setOffset(offset + 20); setActiveIndex(0); }}>{zh ? "下一页" : "Next"}</button>
          </div>}
        </div>
      </SearchDialogFrame>
    </div>}
  </>;
}
