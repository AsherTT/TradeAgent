"use client";

import Link from "next/link";
import { useLanguage } from "../shared/i18n/LanguageProvider";

const columns = [
  { zh: "研究空间", en: "Workspace", links: [
    { zh: "公司目录", en: "Company directory", href: "/app#companies" },
    { zh: "关注公司", en: "Following", href: "/app" },
    { zh: "我的研究", en: "My research", href: "/app/research" },
  ] },
  { zh: "产品功能", en: "Features", links: [
    { zh: "公司与研究门户", en: "Company & research portal", href: "/#portal" },
    { zh: "财务演示", en: "Financial demo", href: "/#demo" },
    { zh: "报告与证据", en: "Reports & evidence", href: "/#reading" },
  ] },
  { zh: "使用产品", en: "Get started", links: [
    { zh: "研究流程", en: "Research workflow", href: "/#workflow" },
    { zh: "创建账户", en: "Create account", href: "/register" },
    { zh: "登录", en: "Log in", href: "/login" },
  ] },
  { zh: "当前范围", en: "Current scope", links: [
    { zh: "数据与能力说明", en: "Data & capabilities", href: "/#data" },
    { zh: "可交互演示", en: "Interactive demo", href: "/#demo" },
    { zh: "开始研究", en: "Start research", href: "/app/research" },
  ] },
] as const;

export function EnhancedAFooter() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  function column(index: number) {
    const item = columns[index];
    return <div className="footer-link-column" key={item.en}>
      <p className="paragraph-light reversed footer-column-heading">{zh ? item.zh : item.en}</p>
      {item.links.map((link) => <Link key={link.href} href={link.href} className="footer-link">{zh ? link.zh : link.en}</Link>)}
    </div>;
  }
  return (
    <footer className="footer" id="data">
      <div className="_1600-wrapper_alt">
        <div className="footer-content">
          <div className="footer-left-column">
            <Link href="/" className="w-inline-block text-[20px] text-white">TradeAgent</Link>
            <p className="paragraph-light reversed">{zh ? "公司、问题与来源，在同一个研究空间。" : "Companies, questions and sources in one research space."}</p>
          </div>
          <div className="footer-right-column">
            <div className="footer-nav">
              <div className="footer-first-two-columns">{column(0)}{column(1)}</div>
              <div className="footer-last-two-columns">{column(2)}{column(3)}</div>
            </div>
            <div className="legal">
              <p className="paragraph-light reversed">{zh ? "账户、关注与研究入口已接通。多期财务、原文定位与并排核验仍在开发；首页演示使用虚构数据。" : "Account, following and research entries are connected. Multi-period financials, source location and side-by-side verification remain in development. Homepage demonstrations use fictional data."}</p>
              <p className="paragraph-light reversed">© 2026 TradeAgent</p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
