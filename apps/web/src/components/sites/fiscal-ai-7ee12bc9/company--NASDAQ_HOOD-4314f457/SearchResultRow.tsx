/* eslint-disable @next/next/no-img-element -- Preserve the captured source image DOM and exact dimensions. */
"use client";

import type { MouseEvent } from "react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import type { SearchResult } from "./search-types";
import styles from "./SearchResultRow.module.css";

interface SearchResultRowProps {
  result: SearchResult;
  active: boolean;
  showInvestorType: boolean;
  onSelect: (event: MouseEvent<HTMLAnchorElement>) => void;
  id: string;
}

export function SearchResultRow({ result, active, showInvestorType, onSelect, id }: SearchResultRowProps) {
  const { t } = useLanguage();
  const investor = result.kind === "investor";
  const etfMarket = result.kind === "etf" ? result.market?.match(/^([^:]+:)([^ ]+)(.*)$/) : null;
  const flagCode = result.flag?.match(/flag-([A-Z]+)-/)?.[1];

  return (
    <a
      id={id}
      href={`https://fiscal.ai${result.href}`}
      className={`${styles.link} ${investor ? styles.investor : styles.security}`}
      data-active={active ? "true" : undefined}
      role="option"
      aria-selected={active}
      onClick={onSelect}
    >
      <div className={styles.body}>
        <span className={styles.label}>
          <div className={styles.row}>
            {investor ? (
              <>
                <span className={styles.avatarOuter}>
                  <div className={styles.avatarContainer}>
                    <span className={styles.avatarInner}>
                      <div className={styles.avatarText}>{result.avatar}</div>
                    </span>
                  </div>
                </span>
                <div className={styles.nameStack}>
                  <p className={styles.name}>{result.name}</p>
                  <p className={styles.name}>{showInvestorType ? t(" (Investor)") : ""}</p>
                </div>
              </>
            ) : (
              // The source nests a button inside its link. A noninteractive div keeps the geometry and one focus target.
              <div className={styles.buttonGeometry}>
                <span className={styles.buttonInline}>
                  <span className={styles.buttonInline}>
                    <div className={styles.identity}>
                      <div className={styles.logoOuter}>
                        <span className={styles.logoInner}>
                          {result.logo && <img className={styles.logoImage} src={result.logo} alt={`${result.name} Website`} width={28} height={28} />}
                        </span>
                      </div>
                      <div className={styles.nameStack}>
                        <p className={styles.name}>{result.name}</p>
                        <div className={styles.market}>
                          {result.flag && (result.kind === "company" ? (
                            <div className={styles.companyFlag}>
                              <img className={styles.companyFlagImage} src={result.flag} alt={`${flagCode} Flag`} />
                            </div>
                          ) : (
                            <span className={styles.etfFlag}>
                              <img className={styles.etfFlagImage} src={result.flag} alt={`${flagCode} Flag`} width={14} height={14} />
                            </span>
                          ))}
                          <p className={styles.marketText}>
                            {etfMarket ? <>{etfMarket[1]}<span className={styles.ticker}>{etfMarket[2]}</span>{etfMarket[3]}</> : result.market}
                          </p>
                        </div>
                      </div>
                    </div>
                  </span>
                </span>
              </div>
            )}
          </div>
        </span>
        <span className={styles.description}>
          {active && result.kind === "company" && result.description && (
            <div className={styles.descriptionContent}>
              <p className={styles.descriptionText}>{t(result.description)}</p>
              <kbd className={styles.tabKey}>Tab</kbd>
            </div>
          )}
        </span>
      </div>
      {result.kind === "company" && result.listings && (
        <span className={styles.listingsSection}>
          <div className={styles.listingsContent}>
            <p className={styles.listingsText}>{result.listings.replace(/Listings$/, t("Listings"))}</p>
            <svg className={styles.listingsArrow} stroke="currentColor" fill="none" strokeWidth={2} viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" height={16} width={16} aria-hidden="true">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>
        </span>
      )}
    </a>
  );
}
