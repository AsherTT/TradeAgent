/** Reference identity only; product navigation must resolve an instrumentId. */
export interface FiscalReferenceCompany {
  name: string;
  exchangeSymbol: string;
  pathname: string;
}

/** Public source labels/URLs do not declare equivalent product capabilities. */
export interface FiscalReferenceNavigationItem {
  label: string;
  pathname: string;
}
