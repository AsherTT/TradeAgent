"use client";

import type { KeyboardEventHandler, RefObject } from "react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import styles from "./SearchInputBar.module.css";

interface SearchInputBarProps {
  query: string;
  onQueryChange: (query: string) => void;
  onKeyDown: KeyboardEventHandler<HTMLInputElement>;
  inputRef: RefObject<HTMLInputElement | null>;
}

export function SearchInputBar({ query, onQueryChange, onKeyDown, inputRef }: SearchInputBarProps) {
  const { t } = useLanguage();
  const showHint = query.length === 0;

  return (
    <form className={styles.form} role="search" onSubmit={(event) => event.preventDefault()}>
      <div className={styles.wrapper}>
        <div className={styles.searchIcon} aria-hidden="true">
          <svg className={styles.icon} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" fill="none" height={18} width={18}>
            <circle cx={11} cy={11} r={8} />
            <line x1={21} y1={21} x2={16.65} y2={16.65} />
          </svg>
        </div>
        <input
          ref={inputRef}
          id="main-search-bar-modal"
          className={`${styles.input} ${showHint ? styles.withHint : ""}`}
          type="search"
          maxLength={512}
          spellCheck={false}
          autoComplete="off"
          autoCapitalize="off"
          autoCorrect="off"
          enterKeyHint="go"
          placeholder={t("Search 50,000+ companies")}
          aria-label={t("Search")}
          aria-controls="fiscal-search-results"
          aria-describedby="fiscal-search-keyboard-help"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onKeyDown={onKeyDown}
        />
        {showHint && (
          <div className={styles.hint} aria-hidden="true">
            <kbd className={styles.hintKey}>/</kbd>
          </div>
        )}
      </div>
    </form>
  );
}
