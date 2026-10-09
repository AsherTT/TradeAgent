import type { CompanyDataSourcesContent, CompanyDataStatusContent } from "@/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/types";

export const sourceDataStatus: CompanyDataStatusContent = {
  heading: "Company Analysis and Financial Data Status",
  dataColumn: "Data",
  updatedColumn: "Last Updated (UTC time)",
  rows: [
    { id: "company-analysis", label: "Company Analysis", updatedAtLabel: "2026/10/07 18:18" },
    { id: "end-of-day-share-price", label: "End of Day Share Price", updatedAtLabel: "2026/10/07 08:00" },
    { id: "earnings", label: "Earnings", updatedAtLabel: "2026/06/27" },
    { id: "annual-earnings", label: "Annual Earnings", updatedAtLabel: "2025/09/27" },
  ],
};

// 来源页面的静态开发样本，仅供此验证路由使用。
export const sourceDataSources: CompanyDataSourcesContent = {
  heading: "Data Sources",
  introductionBeforeLink: "The data used in our company analysis is from ",
  provider: {
    label: "S&P Global Market Intelligence LLC",
    href: "https://www.spglobal.com/market-intelligence/en",
  },
  introductionAfterLink:
    ". The following data is used in our analysis model to generate this report. Data is normalised which can introduce a delay from the source being available.",
  columns: ["Package", "Data", "Timeframe", "Example US Source"],
  rows: [
    {
      id: "company-financials",
      packageLabel: "Company Financials",
      timeframeLabel: "10 years",
      data: ["Income statement", "Cash flow statement", "Balance sheet"],
      sources: [
        {
          label: "SEC Form 10-K",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=10-K&owner=include&count=40&action=getcurrent",
        },
        {
          label: "SEC Form 10-Q",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=10-Q&owner=include&count=40&action=getcurrent",
        },
      ],
    },
    {
      id: "analyst-consensus-estimates",
      packageLabel: "Analyst Consensus Estimates",
      timeframeLabel: "+3 years",
      data: ["Forecast financials", "Analyst price targets"],
      sources: [
        { label: "Analyst Research Reports" },
        {
          label: "Blue Matrix",
          href: "https://bluematrix.com/www3/Home.action",
        },
      ],
    },
    {
      id: "market-prices",
      packageLabel: "Market Prices",
      timeframeLabel: "30 years",
      data: ["Stock prices", "Dividends, Splits and Actions"],
      sources: [
        {
          label: "ICE Market Data",
          href: "https://www.ice.com/fixed-income-data-services/data-and-analytics/exchange-data",
        },
        {
          label: "SEC Form S-1",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=S-1&owner=include&count=40&action=getcurrent",
        },
      ],
    },
    {
      id: "ownership",
      packageLabel: "Ownership",
      timeframeLabel: "10 years",
      data: ["Top shareholders", "Insider trading"],
      sources: [
        {
          label: "SEC Form 4",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=4&owner=include&count=40&action=getcurrent",
        },
        {
          label: "SEC Form 13D",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=SC+13D&owner=include&count=40&action=getcurrent",
        },
      ],
    },
    {
      id: "management",
      packageLabel: "Management",
      timeframeLabel: "10 years",
      data: ["Leadership team", "Board of directors"],
      sources: [
        {
          label: "SEC Form 10-K",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=10-K&owner=include&count=40&action=getcurrent",
        },
        {
          label: "SEC Form DEF 14A",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=DEF+14A&owner=include&count=40&action=getcurrent",
        },
      ],
    },
    {
      id: "key-developments",
      packageLabel: "Key Developments",
      timeframeLabel: "10 years",
      data: ["Company announcements"],
      sources: [
        {
          label: "SEC Form 8-K",
          href: "https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=8-K&owner=include&count=40&action=getcurrent",
        },
      ],
    },
  ],
  footnote:
    " Example for US securities, for non-US equivalent regulatory forms and sources are used.",
  financialPeriodDescription:
    "Unless specified all financial data is based on a yearly period but updated quarterly. This is known as Trailing Twelve Month (TTM) or Last Twelve Month (LTM) Data. ",
  learnMore: {
    label: "Learn more",
    href: "https://support.simplywall.st/hc/en-us/articles/115006170908-Your-data-is-different-from-other-reports-and-websites-why-is-that",
  },
};
