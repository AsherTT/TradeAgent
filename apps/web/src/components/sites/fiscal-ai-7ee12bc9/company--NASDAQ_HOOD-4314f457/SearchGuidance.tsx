import styles from "./SearchGuidance.module.css";

export function SearchGuidance() {
  return (
    <div className={styles.guidance}>
      <p className={styles.tip}>
        {"Tip: Navigate directly to pages by typing "}
        <span className={styles.example}>&quot;Tesla income statement&quot;</span>
        {", "}
        <span className={styles.example}>&quot;Apple estimates&quot;</span>
        {", or "}
        <span className={styles.example}>&quot;MSFT pages&quot;</span>
      </p>
    </div>
  );
}
