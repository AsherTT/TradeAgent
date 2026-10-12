"use client";

import Link from "next/link";
import { FiscalCompanyIdentity } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/FiscalCompanyIdentity";
import { FiscalCompanyProfile } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/FiscalCompanyProfile";
import { identityReference, profileReference } from "@/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/company-identity-reference";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import styles from "./IdentityReferencePreview.module.css";

export function IdentityReferencePreview() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  return <div className={styles.frame}>
    <header className="mx-auto flex max-w-[1000px] flex-wrap items-center justify-between gap-4">
      <h1 className="text-base font-semibold">{zh ? "Fiscal 公司身份与概览来源对照" : "Fiscal company identity and overview comparison"}</h1>
      <div className="[&_button[aria-pressed=true]]:text-[#191816]"><LanguageSwitcher appearance="account" /></div>
    </header>
    <p className="mx-auto mt-4 max-w-[1000px] text-sm leading-6 text-white/65">{zh ? "以下英文内容是来源快照，只用于组件对照，不是实时自有公司数据，也不是整页复刻完成。正式公司搜索与目录详情使用 SEC 真实身份。" : "The English content below is a captured source specimen for component comparison. It is not live product data or a completed full-page clone. Product search and directory details use actual SEC identities."}</p>
    <div className={styles.identity} data-comparison="identity"><FiscalCompanyIdentity {...identityReference} /></div>
    <div className={styles.profile} data-comparison="profile"><FiscalCompanyProfile {...profileReference} /></div>
    <nav className="mx-auto mt-8 flex max-w-[1000px] gap-6 text-sm">
      <Link className="underline" href="/app/company-search">{zh ? "真实公司搜索" : "Real company search"}</Link>
      <Link className="underline" href="/labs/r1-fiscal-search">{zh ? "搜索区块对照" : "Search comparison"}</Link>
    </nav>
  </div>;
}
