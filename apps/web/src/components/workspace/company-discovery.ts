import { validResearchId } from "@/components/research/contracts";

export interface DiscoveredCompany {
  cik: string;
  symbol: string;
  name: string;
  exchange: string | null;
  instrument_id: string | null;
}
export interface DirectoryMetadata {
  source: "sec_company_tickers_exchange";
  source_url: string;
  fetched_at: string;
  stale: boolean;
  directory_total: number;
}
export interface DiscoveryPage extends DirectoryMetadata {
  items: DiscoveredCompany[];
  total: number;
  limit: number;
  offset: number;
}
export interface DiscoveryDetail extends DirectoryMetadata { company: DiscoveredCompany }

export function directoryDetailPath(company: DiscoveredCompany): string {
  const query = new URLSearchParams({ symbol: company.symbol, exchange: company.exchange ?? "" });
  return `/app/companies/discovery/${encodeURIComponent(company.cik)}?${query}`;
}
export function companyDestination(company: DiscoveredCompany): string {
  return company.instrument_id && validResearchId(company.instrument_id)
    ? `/app/companies/${company.instrument_id}` : directoryDetailPath(company);
}

// Captured local artwork is reused only for an exact issuer/listing identity, never by name.
export function directoryLogo(company: DiscoveredCompany): string | undefined {
  const tickers: Record<string, string> = {
    "0000320193:NASDAQ:AAPL": "AAPL",
    "0000789019:NASDAQ:MSFT": "MSFT",
    "0001045810:NASDAQ:NVDA": "NVDA",
    "0001783879:NASDAQ:HOOD": "HOOD",
  };
  const ticker = tickers[`${company.cik}:${company.exchange}:${company.symbol}`];
  return ticker ? `/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/search-images-20261011/logo-${ticker}.png` : undefined;
}
