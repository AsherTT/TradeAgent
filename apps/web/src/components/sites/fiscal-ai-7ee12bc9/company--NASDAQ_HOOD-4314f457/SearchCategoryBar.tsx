"use client";

import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import type { SearchCategory } from "./search-types";
import styles from "./SearchCategoryBar.module.css";

interface SearchCategoryBarProps {
  category: SearchCategory;
  onCategoryChange: (category: SearchCategory) => void;
  options?: readonly { value: SearchCategory; label: string }[];
}

const categories = [
  { value: "all", label: "All" },
  { value: "company", label: "Companies" },
  { value: "etf", label: "ETFs & Funds" },
  { value: "investor", label: "Investors" },
] as const;

export function SearchCategoryBar({ category, onCategoryChange, options = categories }: SearchCategoryBarProps) {
  const { t } = useLanguage();

  return (
    <div className={styles.wrapper}>
      <div className={styles.inner}>
        <div className={styles.tabList} role="tablist" aria-orientation="horizontal">
          {options.map((item) => (
            <button
              key={item.value}
              type="button"
              role="tab"
              aria-selected={category === item.value}
              className={styles.tab}
              onClick={() => onCategoryChange(item.value)}
            >
              <span className={styles.tabText}>
                <div className={styles.badge}>
                  <span className={styles.badgeLabel}>{t(item.label)}</span>
                </div>
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
