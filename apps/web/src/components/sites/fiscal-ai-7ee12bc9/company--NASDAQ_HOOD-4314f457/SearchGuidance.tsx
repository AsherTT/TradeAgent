import styles from "./SearchGuidance.module.css";

export function SearchGuidance({ translate = (text) => text, message }: { translate?: (text: string) => string; message?: string }) {
  return (
    <div className={styles.guidance}>
      <p className={styles.tip}>
        {message ?? <>{translate("Tip: Navigate directly to pages by typing ")}
        <span className={styles.example}>&quot;Tesla income statement&quot;</span>
        {", "}
        <span className={styles.example}>&quot;Apple estimates&quot;</span>
        {translate(", or ")}
        <span className={styles.example}>&quot;MSFT pages&quot;</span>
        </>}
      </p>
    </div>
  );
}
