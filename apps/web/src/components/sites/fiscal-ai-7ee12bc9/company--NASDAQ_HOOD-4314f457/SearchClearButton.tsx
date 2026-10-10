"use client";

import styles from "./SearchClearButton.module.css";

type SearchClearButtonProps = {
  onClear: () => void;
};

export function SearchClearButton({ onClear }: SearchClearButtonProps) {
  return (
    <button type="button" className={styles.button} onClick={onClear}>
      <span className={styles.inner}>
        <span className={styles.label}>Clear Search</span>
      </span>
    </button>
  );
}
