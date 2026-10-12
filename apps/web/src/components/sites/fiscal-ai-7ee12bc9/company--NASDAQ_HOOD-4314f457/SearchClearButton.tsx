"use client";

import styles from "./SearchClearButton.module.css";

type SearchClearButtonProps = {
  onClear: () => void;
  label?: string;
};

export function SearchClearButton({
  onClear,
  label = "Clear Search",
}: SearchClearButtonProps) {
  return (
    <button type="button" className={styles.button} onClick={onClear}>
      <span className={styles.inner}>
        <span className={styles.label}>{label}</span>
      </span>
    </button>
  );
}
