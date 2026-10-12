"use client";

import { SearchClearButton } from "./SearchClearButton";
import styles from "./SearchClearBar.module.css";

type SearchClearBarProps = {
  onClear: () => void;
  label?: string;
};

export function SearchClearBar({
  onClear,
  label = "Clear Search",
}: SearchClearBarProps) {
  return (
    <div className={styles.bar}>
      <SearchClearButton onClear={onClear} label={label} />
    </div>
  );
}
