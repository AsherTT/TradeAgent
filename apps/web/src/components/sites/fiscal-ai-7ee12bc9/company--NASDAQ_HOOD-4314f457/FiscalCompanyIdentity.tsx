/* eslint-disable @next/next/no-img-element -- Preserve the captured source image DOM and dimensions. */

import styles from "./FiscalCompanyIdentity.module.css";

interface FiscalCompanyIdentityProps {
  name: string;
  exchangeSymbol: string;
  logoSrc?: string;
}

export function FiscalCompanyIdentity({ name, exchangeSymbol, logoSrc }: FiscalCompanyIdentityProps) {
  return (
    <div className={styles.card}>
      <div className={styles.parent}>
        <div className={styles.identity}>
          <div className={styles.logoOuter}>
            <span className={styles.logoInner}>
              {logoSrc && (
                <img
                  className={styles.logoImage}
                  src={logoSrc}
                  alt={`${name} Website`}
                  width={46}
                  height={46}
                />
              )}
            </span>
          </div>
          <div className={styles.nameStack}>
            <h1 className={styles.name}>{name}</h1>
            <div className={styles.market}>
              <p className={styles.marketText}>{exchangeSymbol}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
