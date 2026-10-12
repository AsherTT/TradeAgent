"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import styles from "./FiscalCompanyProfile.module.css";

interface FiscalCompanyProfileField {
  label: string;
  value: string;
  href?: string;
}

interface FiscalCompanyProfileProps {
  title: string;
  description: string;
  fields: readonly FiscalCompanyProfileField[];
}

export function FiscalCompanyProfile({ title, description, fields }: FiscalCompanyProfileProps) {
  const { t } = useLanguage();
  const contentId = useId();
  const paragraphRef = useRef<HTMLParagraphElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);

  useEffect(() => {
    const paragraph = paragraphRef.current;
    if (!paragraph) return;
    const measure = () => setCanExpand(paragraph.getBoundingClientRect().height > 60);
    measure();
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(measure);
      observer.observe(paragraph);
      return () => observer.disconnect();
    }
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [description]);

  return (
    <div className={styles.card}>
      <div className={styles.outerWrapper}>
        <div className={styles.outerStack}>
          <div className={styles.innerStack}>
            <h2 className={styles.title}>{title}</h2>
            <div className={styles.spoiler}>
              {canExpand && (
                <button
                  className={styles.disclosure}
                  type="button"
                  aria-controls={contentId}
                  aria-expanded={expanded}
                  onClick={() => setExpanded((value) => !value)}
                >
                  {t(expanded ? "Hide" : "Show more")}
                </button>
              )}
              <div id={contentId} className={styles.content} data-expanded={expanded ? "true" : undefined}>
                <div className={styles.paragraphWrapper}>
                  <p ref={paragraphRef} className={styles.description}>{description}</p>
                </div>
              </div>
            </div>
            <ul className={styles.list}>
              {fields.map((field, index) => (
                <li className={styles.item} key={`${field.label}-${index}`}>
                  <div className={styles.itemWrapper}>
                    <span className={styles.itemLabel}>
                      <div className={styles.fieldRow}>
                        <p className={styles.fieldLabel}>{field.label}</p>
                        {field.href ? (
                          <a className={styles.fieldLink} href={field.href} target="_blank" rel="noreferrer">
                            {field.value}
                            <svg
                              className={styles.externalIcon}
                              width={12}
                              height={12}
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth={2}
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              aria-hidden="true"
                            >
                              <path d="M12 6h-6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6" />
                              <path d="M11 13l9-9" />
                              <path d="M15 4h5v5" />
                            </svg>
                          </a>
                        ) : (
                          <p className={styles.fieldValue}>{field.value}</p>
                        )}
                      </div>
                    </span>
                    <div className={styles.divider} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
