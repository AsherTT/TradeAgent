export type SearchResultKind = "company" | "etf" | "investor";
export type SearchCategory = "all" | SearchResultKind;

/** Public source snapshots for the bounded interface preview; not a securities API. */
export interface SearchResult {
  href: string;
  kind: SearchResultKind;
  name: string;
  market: string | null;
  avatar: string | null;
  logo: string | null;
  flag: string | null;
  listings: string | null;
  description: string | null;
}
