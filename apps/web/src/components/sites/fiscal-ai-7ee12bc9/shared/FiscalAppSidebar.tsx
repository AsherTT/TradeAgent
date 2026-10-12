"use client";

import Link from "next/link";
import type { ReactNode, RefObject } from "react";
import { AnalysisIcon, CloseIcon, DashboardIcon, QueryIcon, SettingsIcon } from "./icons";
import styles from "./FiscalAppSidebar.module.css";

export interface AppNavigationItem {
  id: string;
  href: string;
  label: string;
  icon: "dashboard" | "analysis" | "query" | "settings";
  selected: boolean;
}

export interface FiscalAppSidebarProps {
  items: readonly AppNavigationItem[];
  open: boolean;
  navigationLabel: string;
  closeLabel: string;
  searchLabel: string;
  searchHref: string;
  onClose: () => void;
  onNavigate: () => void;
  sidebarRef: RefObject<HTMLElement | null>;
  languageControl: ReactNode;
}

const navigationIcons = {
  dashboard: DashboardIcon,
  analysis: AnalysisIcon,
  query: QueryIcon,
  settings: SettingsIcon,
};

export function FiscalAppSidebar({
  items,
  open,
  navigationLabel,
  closeLabel,
  searchLabel,
  searchHref,
  onClose,
  onNavigate,
  sidebarRef,
  languageControl,
}: FiscalAppSidebarProps) {
  return (
    <aside
      id="workbench-navigation"
      ref={sidebarRef}
      className={`${styles.sidebar}${open ? ` ${styles.open}` : ""}`}
      role={open ? "dialog" : undefined}
      aria-modal={open ? true : undefined}
      aria-label={open ? navigationLabel : undefined}
    >
      <div className={styles.brandRow}>
        <Link href="/" aria-label="TradeAgent" className={styles.brand} onNavigate={onNavigate}>
          <svg aria-hidden="true" focusable="false" viewBox="0 0 64 64" width="32" height="32">
            <rect width="64" height="64" rx="14" fill="#fdcc6a" />
            <path d="M17 18h30v7H36v24h-8V25H17z" fill="#191816" />
          </svg>
        </Link>
        <button type="button" className={styles.close} aria-label={closeLabel} onClick={onClose}>
          <CloseIcon />
        </button>
      </div>
      <div className={styles.searchContainer}>
        <Link href={searchHref} className={styles.search} onNavigate={onNavigate}>
          <svg className={styles.searchIcon} aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          {searchLabel}
        </Link>
      </div>
      <nav className={styles.navigation} aria-label={navigationLabel}>
        <ul className={styles.items}>
          {items.map((item) => {
            const Icon = navigationIcons[item.icon];
            return (
              <li key={item.id}>
                <Link
                  href={item.href}
                  className={`${styles.link}${item.selected ? ` ${styles.selected}` : ""}`}
                  aria-current={item.selected ? "page" : undefined}
                  onNavigate={onNavigate}
                >
                  <span className={styles.icon}><Icon /></span>
                  <span className={styles.label}>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className={styles.language}>{languageControl}</div>
    </aside>
  );
}
