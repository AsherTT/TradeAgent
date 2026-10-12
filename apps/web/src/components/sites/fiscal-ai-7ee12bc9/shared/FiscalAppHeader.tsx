import Link from "next/link";
import type { ReactNode, RefObject } from "react";

import styles from "./FiscalAppHeader.module.css";

type FiscalAppHeaderProps = {
  searchHref: string;
  searchLabel: string;
  languageControl: ReactNode;
  navigationLabel: string;
  expanded: boolean;
  onOpenNavigation: () => void;
  buttonRef: RefObject<HTMLButtonElement | null>;
  searchRef: RefObject<HTMLAnchorElement | null>;
};

export function FiscalAppHeader({
  searchHref,
  searchLabel,
  languageControl,
  navigationLabel,
  expanded,
  onOpenNavigation,
  buttonRef,
  searchRef,
}: FiscalAppHeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.row}>
          <Link href={searchHref} ref={searchRef} className={styles.search}>
            <span className={styles.searchIcon} aria-hidden="true">
              <svg
                className={styles.icon}
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </span>
            {searchLabel}
            <span className={styles.hint} aria-hidden="true">
              <kbd className={styles.hintKey}>/</kbd>
            </span>
          </Link>
          {languageControl}
          <button
            ref={buttonRef}
            type="button"
            className={styles.burger}
            aria-label={navigationLabel}
            aria-expanded={expanded}
            aria-controls="workbench-navigation"
            onClick={onOpenNavigation}
          >
            <div className={styles.lines} aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>
  );
}
