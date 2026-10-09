import type { SourceImage } from "../shared/types";

interface ResearchTab extends SourceImage {
  label: string;
  description: string;
  icon: string;
}

export const researchTabs: readonly ResearchTab[] = [
  {
    "label": "Past Performance",
    "description": "Key benchmarks of the company's profitability or revenue over the years",
    "icon": "https://marketing.simplywall.st/assets/bar-chart-1.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Microsoft-Sankey.gif",
    "alt": "Past performance income statement flow"
  },
  {
    "label": "Risks & Rewards",
    "description": "A snapshot of critical red-flags and opportunities with key insights extracted daily",
    "icon": "https://marketing.simplywall.st/assets/trending-up-2.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-rewards-risks.png",
    "alt": "Warning signs, risks and rewards"
  },
  {
    "label": "Valuation & Comparison",
    "description": "Estimated stock fair value based on future expected cash flows",
    "icon": "https://marketing.simplywall.st/assets/dollar-sign-1.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-valuation.png",
    "alt": "Valuation compared with fair value"
  },
  {
    "label": "Growth Forecast",
    "description": "Forecast growth of a company based on the consensus of professional analysts",
    "icon": "https://marketing.simplywall.st/assets/bar-chartforecast-2.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-growth-forecast.png",
    "alt": "Future earnings and revenue forecasts"
  },
  {
    "label": "Financial Health",
    "description": "Understand the balance sheet. From assets and liabilities to debt, equity and current cash runway",
    "icon": "https://marketing.simplywall.st/assets/activity-1.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-financial-health.png",
    "alt": "Financial health: assets versus liabilities"
  },
  {
    "label": "Dividend Quality",
    "description": "Historical, current and projected shareholder payments and how it compares to the market and industry",
    "icon": "https://marketing.simplywall.st/assets/Group-1171.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-dividend.png",
    "alt": "Dividend history, quality and benchmark"
  },
  {
    "label": "Management Profile",
    "description": "Assess if the right people are steering the ship with management and board profiles and analysis",
    "icon": "https://marketing.simplywall.st/assets/users-2.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-management.png",
    "alt": "Management profile"
  },
  {
    "label": "Insider Transactions",
    "description": "Which individuals or institutions have been backing the company with their financial decisions?",
    "icon": "https://marketing.simplywall.st/assets/user-2.svg",
    "src": "https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/visual-report-insider-transactions.png",
    "alt": "Insider transactions"
  }
];
