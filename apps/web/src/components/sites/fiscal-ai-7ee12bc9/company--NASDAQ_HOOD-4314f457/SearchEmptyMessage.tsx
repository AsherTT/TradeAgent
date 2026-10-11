import styles from "./SearchEmptyMessage.module.css";

export function SearchEmptyMessage({ message = "No results found..." }: { message?: string }) {
  return <p className={styles.message}>{message}</p>;
}
