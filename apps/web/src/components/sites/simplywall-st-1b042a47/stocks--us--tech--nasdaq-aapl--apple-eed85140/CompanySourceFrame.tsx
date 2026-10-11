"use client";

import type { ReactNode } from "react";
import { useLanguage } from "../shared/i18n/LanguageProvider";
import styles from "./CompanySourceFrame.module.css";

const companyUrl = "https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple";
const navigation = [
  { label: "Company Overview", href: companyUrl },
  { label: "Valuation", href: `${companyUrl}/valuation` },
  { label: "Future Growth", href: `${companyUrl}/future` },
  { label: "Past Performance", href: `${companyUrl}/past` },
  { label: "Financial Health", href: `${companyUrl}/health` },
  { label: "Dividend", href: `${companyUrl}/dividend` },
  { label: "Management", href: `${companyUrl}/management` },
  { label: "Ownership", href: `${companyUrl}/ownership` },
  { label: "Other Information", href: `${companyUrl}/information` },
  { label: "Stock Community", href: "https://simplywall.st/stock/nasdaqgs/aapl" },
] as const;

export function CompanySourceFrame({ children }: { children: ReactNode }) {
  const { t } = useLanguage();

  return (
    <section className={styles.frame}>
      <aside className={styles.sidebar}>
        {/* Sticky is a bounded preview adaptation of the source's fixed report sidebar. */}
        <div className={styles.sidebarContent}>
          <div className={styles.identity}>
            <p className={styles.name}>Apple Inc.</p>
            <p className={styles.ticker}>{"NasdaqGS:AAPL "}{t("Stock Report")}</p>
            <div className={styles.market}>
              <p className={styles.marketText}>{t("Market Cap:")}{" US$4.9t"}</p>
            </div>
          </div>
          <nav className={styles.navigation}>
            <ul className={styles.list}>
              {navigation.map((item, index) => (
                <li key={item.href} className={styles.item}>
                  <a
                    className={`${styles.link} ${index === 0 ? styles.overview : ""}`}
                    href={item.href}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {t(item.label)}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </aside>
      <div className={styles.report}>{children}</div>
    </section>
  );
}
