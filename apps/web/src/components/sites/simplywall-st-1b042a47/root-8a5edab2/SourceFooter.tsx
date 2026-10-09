import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";
import { TradeAgentLogo } from "../shared/TradeAgentLogo";

export function SourceFooter({ brand = "source" }: { brand?: "source" | "tradeagent" }) {
  return (
      <div className={"footer"}>
        <div className={"_1600-wrapper_alt"}>
          <div className={"footer-content"}>
            <div className={"footer-left-column"}>
              <a href={brand === "tradeagent" ? "/" : "https://simplywall.st/"} className={"w-inline-block"}>
                {brand === "tradeagent" ? <TradeAgentLogo placement="footer" /> : <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/Simply-Wall-St-Logo-FT.svg")} width={"108"} alt={""} className={"logo-image-2"} />}
              </a>
              <p className={"paragraph-light reversed"}>
                <LocalizedText en={"Level 5, 320 Pitt Street, Sydney"} />
              </p>
              <div className={"social-icons"}>
                <a href={"https://www.linkedin.com/company/simply-wall-st/"} className={"social-link w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/LinkedIn.svg")} loading={"lazy"} alt={""} />
                </a>
                <a href={"https://www.youtube.com/c/simplywallst"} className={"social-link w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/YouTube.svg")} loading={"lazy"} alt={""} />
                </a>
                <a href={"https://twitter.com/simplywallst"} className={"social-link w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/Twitter.svg")} loading={"lazy"} alt={""} />
                </a>
              </div>
              <div className={"app-stores"}>
                <a href={"https://apps.apple.com/us/app/simply-wall-st-stock-analysis/id1075614972"} className={"app-store-link w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/itunesbadge.png")} loading={"lazy"} width={"160"} alt={"Download on the App Store"} className={"app-store-image"} />
                </a>
                <a href={"https://play.google.com/store/apps/details?id=com.simplywallst.app&hl=en_AU&gl=US&pli=1"} className={"app-store-link w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/googleplay.png")} loading={"lazy"} width={"160"} alt={"Get it on Google Play"} className={"app-store-image"} />
                </a>
                <a href={"https://chromewebstore.google.com/detail/stock-analysis-overlay-si/fogdlgjnkolhbefbbpghbafdkhcdgdnk"} className={"app-store-link chrome-extension-image w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/chrome-webstore-1.svg")} loading={"lazy"} width={"160"} alt={"Available in the Chrome Web Store"} className={"chrome-extension-image"} />
                </a>
              </div>
              <div className={"sp-global"}>
                <a href={"https://www.spglobal.com/market-intelligence"} target={"_blank"} rel={"noreferrer"} className={"sp-logo w-inline-block"}>
                  <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/sp-global-logo.png")} loading={"lazy"} width={"160"} alt={"Standard and Poor Global Market Intelligence Logo"} />
                </a>
                <p className={"paragraph-light reversed"}>
                  <LocalizedText en={"Financial Data provided by S&P Global Market Intelligence LLC, analysis provided by Simply"} />
                  {" "}
                  <code>
                    <LocalizedText en={"Wall"} />
                  </code>
                  <LocalizedText en={" Street Pty Ltd. Copyright ©"} />
                  {" "}
                  <span className={"copy-year"}>
                    <LocalizedText en={"2026"} />
                  </span>
                  <LocalizedText en={", S&P Global Market Intelligence LLC. All rights reserved."} />
                </p>
                <a href={"https://simplywall.st/analysis-and-financial-data-sources"} className={"footer-link"}>
                  <LocalizedText en={"View Data Sources"} />
                </a>
              </div>
            </div>
            <div className={"footer-right-column"}>
              <div className={"footer-nav"}>
                <div className={"footer-first-two-columns"}>
                  <div className={"footer-link-column"}>
                    <p className={"paragraph-light reversed footer-column-heading"}>
                      <LocalizedText en={"Popular Markets"} />
                    </p>
                    <a href={"https://simplywall.st/markets/us"} className={"footer-link"}>
                      <LocalizedText en={"US: NYSE & NASDAQ"} />
                    </a>
                    <a href={"https://simplywall.st/markets/gb"} className={"footer-link"}>
                      <LocalizedText en={"UK: FTSE"} />
                    </a>
                    <a href={"https://simplywall.st/markets/au"} className={"footer-link"}>
                      <LocalizedText en={"Australia: ASX"} />
                    </a>
                    <a href={"https://simplywall.st/markets/in"} className={"footer-link"}>
                      <LocalizedText en={"India: NIFTY"} />
                    </a>
                    <a href={"https://simplywall.st/markets/ca"} className={"footer-link"}>
                      <LocalizedText en={"Canada: TSX"} />
                    </a>
                    <a href={"https://simplywall.st/markets/za"} className={"footer-link"}>
                      <LocalizedText en={"South Africa: JSE"} />
                    </a>
                    <a href={"https://simplywall.st/markets/jp"} className={"footer-link"}>
                      <LocalizedText en={"Japan: NIKKEI"} />
                    </a>
                    <a href={"https://simplywall.st/markets/kr"} className={"footer-link"}>
                      <LocalizedText en={"South Korea: KOSPI"} />
                    </a>
                    <a href={"https://simplywall.st/markets/de"} className={"footer-link"}>
                      <LocalizedText en={"Germany: DAX"} />
                    </a>
                  </div>
                  <div className={"footer-link-column"}>
                    <p className={"paragraph-light reversed footer-column-heading"}>
                      <LocalizedText en={"Investing Ideas"} />
                    </p>
                    <a href={"https://simplywall.st/discover/investing-ideas/168/undervalued-stocks-based-on-cash-flows"} className={"footer-link"}>
                      <LocalizedText en={"Undervalued Companies"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/146/dividend-powerhouses-3-yield"} className={"footer-link"}>
                      <LocalizedText en={"Dividend Powerhouses"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/171/insider-trading"} className={"footer-link"}>
                      <LocalizedText en={"Recent Insider Buying"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/215173/nuclear-energy-stocks"} className={"footer-link"}>
                      <LocalizedText en={"Nuclear Energy"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/5620/electric-autonomous-vehicle-stocks"} className={"footer-link"}>
                      <LocalizedText en={"Autonomous Vehicles"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/215169/artificial-intelligence-ai-stocks"} className={"footer-link"}>
                      <LocalizedText en={"Artificial Intelligence"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/16734/cryptocurrency-and-blockchain-stocks"} className={"footer-link"}>
                      <LocalizedText en={"Crypto and Blockchain"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas/10184/cybersecurity"} className={"footer-link"}>
                      <LocalizedText en={"Cybersecurity"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas"} className={"footer-link"}>
                      <LocalizedText en={"All Investing Ideas"} />
                    </a>
                  </div>
                </div>
                <div className={"footer-last-two-columns"}>
                  <div className={"footer-link-column"}>
                    <p className={"paragraph-light reversed footer-column-heading"}>
                      <LocalizedText en={"Features & Tools"} />
                    </p>
                    <a href={"https://simplywall.st/features/portfolio"} className={"footer-link"}>
                      <LocalizedText en={"Portfolio Tracker"} />
                    </a>
                    <a href={"https://simplywall.st/features/stock-screener"} className={"footer-link"}>
                      <LocalizedText en={"Screener & Alerts"} />
                    </a>
                    <a href={"https://simplywall.st/discover/investing-ideas"} className={"footer-link"}>
                      <LocalizedText en={"Investing Ideas"} />
                    </a>
                    <a href={"https://simplywall.st/community/narratives"} className={"footer-link"}>
                      <LocalizedText en={"Community Narratives"} />
                    </a>
                    <a href={"https://simplywall.st/markets/insights"} className={"footer-link"}>
                      <LocalizedText en={"Market Insights"} />
                    </a>
                    <a href={"https://support.simplywall.st/hc/en-us/articles/7894830045199-Changelog"} className={"footer-link"}>
                      <LocalizedText en={"What's New"} />
                    </a>
                    <a href={"https://simplywall.st/tools/dividend-calculator"} className={"footer-link"}>
                      <LocalizedText en={"Dividend Calculator"} />
                    </a>
                    <a href={"https://simplywall.st/vs/simply-wall-street-vs-morningstar"} target={"_blank"} rel={"noreferrer"} className={"footer-link"}>
                      <LocalizedText en={"Compare vs Morningstar"} />
                    </a>
                    <a href={"https://simplywall.st/vs/simply-wall-street-vs-seeking-alpha"} target={"_blank"} rel={"noreferrer"} className={"footer-link"}>
                      <LocalizedText en={"Compare vs Seeking Alpha"} />
                    </a>
                    <a href={"https://simplywall.st/vs/simply-wall-street-vs-investing-com-pro"} target={"_blank"} rel={"noreferrer"} className={"footer-link"}>
                      <LocalizedText en={"Compare vs Investing.com"} />
                    </a>
                  </div>
                  <div className={"footer-link-column"}>
                    <p className={"paragraph-light reversed footer-column-heading"}>
                      <LocalizedText en={"Simply Wall St"} />
                    </p>
                    <a href={"https://simplywall.st/plans"} className={"footer-link"}>
                      <LocalizedText en={"Plans & Pricing"} />
                    </a>
                    <a href={"https://simplywall.st/advertising"} className={"footer-link"}>
                      <LocalizedText en={"Advertising"} />
                    </a>
                    <a href={"https://simplywall.st/about"} className={"footer-link"}>
                      <LocalizedText en={"About Us"} />
                    </a>
                    <a href={"https://support.simplywall.st/hc/en-us/requests/new"} className={"footer-link"}>
                      <LocalizedText en={"Contact Us"} />
                    </a>
                    <a href={"https://simplywall.st/careers"} className={"footer-link bottom-space"}>
                      <LocalizedText en={"Careers"} />
                    </a>
                    <a href={"https://support.simplywall.st/hc/en-us"} className={"footer-link"}>
                      <LocalizedText en={"Help Center"} />
                    </a>
                    <a href={"https://learn.simplywall.st/"} className={"footer-link"}>
                      <LocalizedText en={"Learn Stock Investing"} />
                    </a>
                    <a href={"https://simplywall.st/affiliate-program"} className={"footer-link"}>
                      <LocalizedText en={"Affiliate Program"} />
                    </a>
                    <a href={"https://simplywall.st/business-plans"} className={"footer-link"}>
                      <LocalizedText en={"Business & Enterprise"} />
                    </a>
                    <a href={"https://charlieinvest.ai"} className={"footer-link"}>
                      <LocalizedText en={"Charlie AI"} />
                    </a>
                  </div>
                </div>
              </div>
              <div className={"legal"}>
                <p className={"paragraph-light reversed"}>
                  <LocalizedText en={"Simply Wall Street Pty Ltd (ACN 600 056 611), is a Corporate Authorised Representative (Authorised Representative Number: 467183) of Sanlam Private Wealth Pty Ltd (AFSL No. 337927). Any advice contained in this website is general advice only and has been prepared without considering your objectives, financial situation or needs. You should not rely on any advice and/or information contained in this website and before making any investment decision we recommend that you consider whether it is appropriate for your situation and seek appropriate financial, taxation and legal advice. Please read our Financial Services Guide before deciding whether to obtain financial services from us."} />
                </p>
                <p className={"paragraph-light reversed"}>
                  <LocalizedText en={"© "} />
                  <span className={"copy-year2"}>
                    <LocalizedText en={"2026"} />
                  </span>
                  <LocalizedText en={" Simply Wall Street Pty Ltd, US Design Patent #29/544/281, Community and European Design Registration #2845206."} />
                </p>
                <div className={"legal-links"}>
                  <a href={"https://media.simplywall.st/site/financials/Financial_Services_Guide_-_Simply_Wall_St_V2.0_dated_20_Jan_23.pdf"} className={"footer-link"}>
                    <LocalizedText en={"Financial Services Guide"} />
                  </a>
                  <a href={"https://simplywall.st/terms-and-conditions"} className={"footer-link"}>
                    <LocalizedText en={"Terms and Conditions"} />
                  </a>
                  <a href={"https://simplywall.st/privacy-policy"} className={"footer-link"}>
                    <LocalizedText en={"Privacy Policy"} />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
}
