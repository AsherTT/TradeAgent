"use client";

import Link from "next/link";
import { useState } from "react";
import { FiscalCompanyIdentity } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/FiscalCompanyIdentity";
import { FiscalCompanyProfile } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/FiscalCompanyProfile";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { companyDestination, directoryLogo, type DiscoveryDetail } from "./company-discovery";
import { useCompanyDiscovery } from "./useCompanyDiscovery";

export function CompanyDirectoryDetail({ cik, symbol, exchange }: { cik: string; symbol: string; exchange: string }) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const [revision, setRevision] = useState(0);
  const query = new URLSearchParams({ symbol, exchange });
  const { data, error, pending } = useCompanyDiscovery<DiscoveryDetail>(`company-discovery/${encodeURIComponent(cik)}?${query}`, true, revision);
  const company = data?.company;
  return <div className="mx-auto max-w-[1400px] px-4 py-3 [font-family:var(--font-fiscal-jakarta),sans-serif]">
    <header className="mb-7 flex flex-wrap items-center justify-between gap-4">
      <Link href="/app/company-search" className="text-sm underline">← {zh ? "公司目录搜索" : "Company directory search"}</Link>
      <div className="[&_button[aria-pressed=true]]:text-[#191816]"><LanguageSwitcher appearance="account" /></div>
    </header>
    {pending && <p role="status">{zh ? "正在获取公司身份…" : "Loading company identity…"}</p>}
    {error && <div role="alert" className="rounded-lg border border-white/20 p-6">
      <p>{error === "session_required" ? zh ? "会话已失效，请重新登录。" : "Your session has expired. Sign in again."
        : error === "directory_company_not_found" ? zh ? "目录中未找到这组发行人、代码与交易所身份。" : "This issuer, ticker and exchange identity was not found in the directory."
          : error === "directory_not_configured" ? zh ? "公司目录来源尚未配置。" : "The company directory source is not configured."
            : zh ? "公司目录暂时不可用。" : "The company directory is temporarily unavailable."}</p>
      {error === "session_required" ? <Link className="mt-4 inline-block underline" href="/login">{zh ? "登录" : "Sign in"}</Link>
        : <button className="mt-4 cursor-pointer underline" type="button" onClick={() => setRevision((value) => value + 1)}>{zh ? "重试" : "Retry"}</button>}
    </div>}
    {data && company && <>
      <FiscalCompanyIdentity name={company.name} exchangeSymbol={`${company.exchange ?? (zh ? "交易所未注明" : "Exchange unspecified")}-${company.symbol}`} logoSrc={directoryLogo(company)} />
      <div className="mt-2 grid items-start gap-2 lg:grid-cols-2">
        <FiscalCompanyProfile title={zh ? "公司身份" : "Company identity"}
          description={zh ? "这里提供 SEC 目录中的公司名称、交易代码与交易所。SEC 不保证目录完整性或准确性；CIK 标识申报发行人，同一发行人可能有多个股票代码。" : "This page provides the issuer name, ticker and exchange reported in the SEC directory. SEC does not guarantee completeness or accuracy. CIK identifies the filing issuer, which may have multiple ticker symbols."}
          fields={[
            { label: zh ? "名称" : "Name", value: company.name },
            { label: "CIK", value: company.cik },
            { label: zh ? "交易代码" : "Ticker", value: company.symbol },
            { label: zh ? "交易所" : "Exchange", value: company.exchange ?? (zh ? "未注明" : "Unspecified") },
            { label: zh ? "研究库收录" : "Research directory record", value: company.instrument_id ? zh ? "已匹配本地记录；研究前还需核验数据" : "Matched local record; verification is still required" : zh ? "尚未收录，仅身份目录" : "Not onboarded; identity directory only" },
          ]} />
        <FiscalCompanyProfile title={zh ? "数据来源与可用范围" : "Data source and availability"}
          description={zh ? "尚未接入本公司的报价、价格走势图、年度财务或分析师预测，暂不能通过这条目录记录发起研究。" : "Quotes, price history, annual financials and analyst estimates are not connected here. This directory record cannot yet be used to start research."}
          fields={[
            { label: zh ? "数据来源" : "Data source", value: "SEC EDGAR", href: "https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data" },
            { label: zh ? "抓取时间" : "Fetched at", value: `${new Date(data.fetched_at).toLocaleString(zh ? "zh-CN" : "en-US", { timeZone: "UTC" })} UTC` },
            { label: zh ? "快照状态" : "Snapshot status", value: data.stale ? zh ? "陈旧快照" : "Stale snapshot" : zh ? "当前快照" : "Current snapshot" },
            { label: zh ? "目录记录数" : "Directory records", value: data.directory_total.toLocaleString() },
            { label: zh ? "行情与财务" : "Market data / financials", value: zh ? "尚未接入" : "Not connected" },
          ]} />
      </div>
      {company.instrument_id && <Link className="mt-5 inline-block text-sm underline" href={companyDestination(company)}>{zh ? "打开已匹配的本地公司页" : "Open matched local company page"} →</Link>}
    </>}
  </div>;
}
