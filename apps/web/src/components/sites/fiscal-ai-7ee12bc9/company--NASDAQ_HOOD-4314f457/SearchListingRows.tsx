/* eslint-disable @next/next/no-img-element -- Preserve the source flag image DOM and exact dimensions. */
"use client";

import type { MouseEvent } from "react";
import type { SearchListing } from "./search-types";
import styles from "./SearchListingRows.module.css";

interface SearchListingRowsProps {
  listings: readonly SearchListing[];
  onSelect: (listing: SearchListing, event: MouseEvent<HTMLAnchorElement>) => void;
  idPrefix: string;
}

export function SearchListingRows({ listings, onSelect, idPrefix }: SearchListingRowsProps) {
  if (listings.length === 0) return null;

  return (
    <div className={styles.root}>
      <div className={styles.stack}>
        {listings.map((listing, index) => (
          <a
            key={`${index}-${listing.market}`}
            id={`${idPrefix}-${index}`}
            className={styles.link}
            href={`https://fiscal.ai${listing.href}`}
            onClick={(event) => onSelect(listing, event)}
          >
            <span className={styles.leftSection}>
              <div className={styles.flagFrame}>
                <img className={styles.flag} src={listing.flag} alt={listing.flagAlt} />
              </div>
            </span>
            <div className={styles.body}>
              <span className={styles.label}>
                <p className={styles.market}>{listing.market}</p>
              </span>
              <span className={styles.description} />
            </div>
          </a>
        ))}
      </div>
      <div className={styles.separator} role="separator" aria-orientation="horizontal" />
    </div>
  );
}
