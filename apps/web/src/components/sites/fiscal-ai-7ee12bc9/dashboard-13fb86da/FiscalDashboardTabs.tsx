"use client";

import { useRef, type KeyboardEvent } from "react";
import styles from "./FiscalDashboardTabs.module.css";

interface FiscalDashboardTabsProps {
  items: readonly { id: string; label: string }[];
  activeId: string;
  onChange: (id: string) => void;
  idPrefix: string;
  label: string;
}

export function FiscalDashboardTabs({
  items,
  activeId,
  onChange,
  idPrefix,
  label,
}: FiscalDashboardTabsProps) {
  const tabs = useRef(new Map<string, HTMLButtonElement>());

  function moveFocus(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let nextIndex: number;
    switch (event.key) {
      case "ArrowLeft":
        nextIndex = (index - 1 + items.length) % items.length;
        break;
      case "ArrowRight":
        nextIndex = (index + 1) % items.length;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = items.length - 1;
        break;
      default:
        return;
    }

    event.preventDefault();
    const nextTab = tabs.current.get(items[nextIndex].id);
    nextTab?.focus();
    nextTab?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
  }

  return (
    <div className={styles.viewport}>
      <div className={styles.list} role="tablist" aria-label={label}>
        {items.map((item, index) => (
          <button
            key={item.id}
            ref={(element) => {
              if (element) tabs.current.set(item.id, element);
              else tabs.current.delete(item.id);
            }}
            className={styles.tab}
            type="button"
            role="tab"
            id={`${idPrefix}-tab-${item.id}`}
            aria-controls={`${idPrefix}-panel-${item.id}`}
            aria-selected={activeId === item.id}
            tabIndex={activeId === item.id ? 0 : -1}
            onClick={() => onChange(item.id)}
            onKeyDown={(event) => moveFocus(event, index)}
          >
            <span className={styles.label}>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
