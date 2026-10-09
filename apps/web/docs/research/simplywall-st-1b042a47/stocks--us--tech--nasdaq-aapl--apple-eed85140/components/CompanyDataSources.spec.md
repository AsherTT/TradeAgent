# CompanyDataSources Specification

2026-10-09. Source: https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple
Target: src/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyDataSources.tsx
Verification: existing /labs/r1-company-data-status, authorized continuation of the same component preview.
Screenshot: docs/design-references/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/data-sources-source-desktop.jpg
Evidence: CompanyDataSources.source-{desktop,tablet,mobile}.json.gz (92 nodes each from overview bounded DOM); source-extra.json (fresh 670px viewport, vertical alignment, native sup and borders).

## Scope and structure
Static props-only server component. No network, account, financial calculation, parsing, tracking, or client state.
Render a fragment within the existing CompanyDataStatusTable section, after its table. The parent now has an optional children slot because both source regions occupy the same surface. No extra card/padding/rounding.
Order: h3; p with inline provider link; div overflow-x-auto pt-4 with native table; p right-aligned footnote with sup *; p period description + Learn more link + period.
Native table: thead/tr/four th scope=col, tbody/six tr/four td. Column order is exactly Package | Data | Timeframe | Example US Source + sup *, despite the source's unusual second/third labels.
Cells: package text, timeframe text, ul data strings, ul mixed plain/link source items. Preserve list bullets and all content. Last row has no row border; other rows have 1px borders #eeece2/10% and vertical-align top. Header cells have native middle alignment.
Add tabIndex=0 and role=region with aria-label from heading to the horizontal scrolling wrapper as an explicit keyboard usability adaptation; no fake scroll buttons.
Use CompanyDataSourcesContent from existing types.ts, data supplied by a separate source fixture used only in the lab.

## Exact styles
Reuse Bureau Sans, current scoped .sws-company-source tokens; link gold #fdcb68. No global edits.
h3: margin 32px 0 16px, font 18px/27px weight500 white; >=1024 20px/30px.
p introduction/period: margin 0 0 16px, 14px/23.8px weight400 white70%; >=1024 16px/27.2px.
Links: inherit surrounding font, gold, text-decoration none -> underline on hover and focus, transition none (observed class + downloaded source CSS). Standard href navigation only; keep same-tab behavior.
Table: width100%, table-auto, border-collapse:collapse, outer 1px #eeece2/10%; no column fixed widths or added min-width. Native content gives mobile intrinsic overflow.
thead background #1a1a1a; th font700, text-left, padding8px16px. Header/body table font13px/19.5px; >=1024 14px/21px. Body400 white.
td padding8px16px, vertical-align top; rows borders as above. ul margin0 padding-left16px list-style disc. li margin0 padding0.
sup uses source's native font-size:smaller (5/6 parent), vertical-align:super and unitless 1.5 line-height; override Tailwind reset's position/top/line-height to static/auto/1.5 so text raises and affects line boxes like source.
Footnote margin8px0px16px, text-right, white70%; 11px/16.5px; >=1024 12px/18px.
Use Tailwind classes, strict TS, named export, mobile first, no inline style.

## Verbatim content
Heading: Data Sources
Introduction before link: The data used in our company analysis is from [space]
Provider: S&P Global Market Intelligence LLC — https://www.spglobal.com/market-intelligence/en
After link: . The following data is used in our analysis model to generate this report. Data is normalised which can introduce a delay from the source being available.
Rows:
- Company Financials | 10 years | Income statement; Cash flow statement; Balance sheet | SEC Form 10-K; SEC Form 10-Q
- Analyst Consensus Estimates | +3 years | Forecast financials; Analyst price targets | Analyst Research Reports (plain); Blue Matrix
- Market Prices | 30 years | Stock prices; Dividends, Splits and Actions (ONE list item) | ICE Market Data; SEC Form S-1
- Ownership | 10 years | Top shareholders; Insider trading | SEC Form 4; SEC Form 13D
- Management | 10 years | Leadership team; Board of directors | SEC Form 10-K; SEC Form DEF 14A
- Key Developments | 10 years | Company announcements | SEC Form 8-K
SEC href pattern: https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=TYPE&owner=include&count=40&action=getcurrent
Exact TYPEs in source order: 10-K;10-Q;S-1;4;SC+13D;10-K;DEF+14A;8-K. Do not replace + with a literal space.
Blue Matrix: https://bluematrix.com/www3/Home.action
ICE Market Data: https://www.ice.com/fixed-income-data-services/data-and-analytics/exchange-data
Footnote after sup: [space]Example for US securities, for non-US equivalent regulatory forms and sources are used.
Period description: Unless specified all financial data is based on a yearly period but updated quarterly. This is known as Trailing Twelve Month (TTM) or Last Twelve Month (LTM) Data. [space]
Learn more: https://support.simplywall.st/hc/en-us/articles/115006170908-Your-data-is-different-from-other-reports-and-websites-why-is-that
Final period after Learn more.

## Responsive and validation
Source region width desktop799.254/table799.254 height394.169; tablet696.217/table696.217 height413.344; mobile358.377/table429.359 height705.785. Current lab outer864 gives800/704/358 inner widths; preserve existing section sizing and document tablet whole-page framing gap.
Native auto table should overflow only its wrapper at390; no page overflow. No column stacking.
Verify1440/768/390 CSS and content, all link hrefs, keyboard region horizontal scrolling and focus underline using browser UI. No external link activation needed.
The standalone lab hides the browser's root scrollbar via a route-presence selector so the390px sampled viewport retains358px component content. This is a documented preview-only framing adaptation, not a claim about the complete source page's scroll implementation. Preserve native vertical scrolling and other routes' scrollbars.
Update preview notice to say data update + data sources static samples, never real TradeAgent data. No new complete source pathname or /app integration.
Builder checks lint and typecheck; parent production build and integration tests. Source hover dynamically untested; behavior read from exact source CSS; whole-page state sweep remains pending.
