import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function DiscoverySection() {
  return (
      <section className={"pb-[81px] pt-[60px] text-center"} data-section={"discover"}>
        <div className={"wrap"}>
          <h2 className={"heading-40 source-inline-b1f22df6"}>
            <LocalizedText en={"Find your next "} />
            <span className={"serif"}>
              <LocalizedText en={"hidden gem."} />
            </span>
          </h2>
          <p className={"mt-[10px] font-[family-name:var(--sans)] text-[16px] font-normal leading-[21.5px]"}>
            <LocalizedText en={"Stop the countless hours of research."} />
            <br />
            <LocalizedText en={"Discovery tools you can use to customize and surface the data points that matter across 120,000 global stocks."} />
          </p>
          <div className={"split"}>
            <div className={"ideas-visual relative aspect-[678/465] w-[678px] shrink"}>
              <div className={"absolute left-[2.95%] top-0 h-full w-[88.79%] rounded-[16px] bg-[linear-gradient(var(--gold),var(--bronze))]"}>

              </div>
              <a href={"https://simplywall.st/discover/investing-ideas/153/top-growth-stocks"} className={"absolute aspect-square w-[33.78%] shadow-[rgba(80,5,5,0.29)_0_2px_5px] transition-transform duration-200 ease-[ease] hover:translate-y-[-4px] left-[11.8%] top-[-13.12%]"}>
                <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/1.png")} alt={"Forecast High Growth"} className={"size-full"} />
              </a>
              <a href={"https://simplywall.st/discover/investing-ideas/5620/buy-the-dip/"} className={"absolute aspect-square w-[33.78%] shadow-[rgba(80,5,5,0.29)_0_2px_5px] transition-transform duration-200 ease-[ease] hover:translate-y-[-4px] left-[49.12%] top-[7.74%]"}>
                <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/2.png")} alt={"Buy the Dip"} className={"size-full"} />
              </a>
              <a href={"https://simplywall.st/discover/investing-ideas/10184/undervalued-tech-stocks/"} className={"absolute aspect-square w-[33.78%] shadow-[rgba(80,5,5,0.29)_0_2px_5px] transition-transform duration-200 ease-[ease] hover:translate-y-[-4px] left-[11.8%] top-[42.15%]"}>
                <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/3.png")} alt={"Potentially Undervalued"} className={"size-full"} />
              </a>
              <a href={"https://simplywall.st/discover/investing-ideas/171/insider-trading"} className={"absolute aspect-square w-[33.78%] shadow-[rgba(80,5,5,0.29)_0_2px_5px] transition-transform duration-200 ease-[ease] hover:translate-y-[-4px] left-[49.12%] top-[62.8%]"}>
                <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/4.png")} alt={"Insider Trading"} className={"size-full"} />
              </a>
            </div>
            <div className={"w-[675px] max-w-full shrink pl-[24px] max-[991px]:pl-0"}>
              <h2 className={"eyebrow source-inline-c6f27bbc"}>
                <LocalizedText en={"Discovery "} />
                <span className={"serif"}>
                  <LocalizedText en={"Hub"} />
                </span>
              </h2>
              <h3 className={"font-[family-name:var(--sans)] text-[28px] font-normal leading-[30px]"}>
                <LocalizedText en={"Your shortcut to"} />
                {" "}
                <span className={"serif"}>
                  <LocalizedText en={"high-quality stocks."} />
                </span>
              </h3>
              <p className={"mt-[16px] font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
                <LocalizedText en={"You don't have to scan every stock from scratch. We’ve organized the market into curated themes - from dividend powerhouses to high insider buying - so you can spend less time searching and more time growing."} />
              </p>
              <div className={"mt-[26px] font-[family-name:var(--sans)] text-[18px] leading-[20px] text-[var(--bronze)]"}>
                <LocalizedText en={"Trending investing ideas"} />
              </div>
              <ul>
                <li>
                  <a href={"https://simplywall.st/discover/investing-ideas/215169/artificial-intelligence-ai-stocks/global"} target={"_blank"} rel={"noopener noreferrer"} className={"flex items-center gap-[20px] pb-[18px] pt-[24px] font-[family-name:var(--serif)] text-[16px] font-normal leading-[20px] [border-bottom:1px_solid_rgba(25,24,22,0.85)]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Artificial intelligence (AI) stocks"} />
                  </a>
                </li>
                <li>
                  <a href={"https://simplywall.st/discover/investing-ideas/5620/electric-autonomous-vehicle-stocks/global"} target={"_blank"} rel={"noopener noreferrer"} className={"flex items-center gap-[20px] pb-[18px] pt-[24px] font-[family-name:var(--serif)] text-[16px] font-normal leading-[20px] [border-bottom:1px_solid_rgba(25,24,22,0.85)]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Global electric and autonomous vehicle stocks"} />
                  </a>
                </li>
                <li>
                  <a href={"https://simplywall.st/discover/investing-ideas/215173/nuclear-energy-stocks/global"} target={"_blank"} rel={"noopener noreferrer"} className={"flex items-center gap-[20px] pb-[18px] pt-[24px] font-[family-name:var(--serif)] text-[16px] font-normal leading-[20px] [border-bottom:1px_solid_rgba(25,24,22,0.85)]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Nuclear energy stocks"} />
                  </a>
                </li>
              </ul>
              <a href={"https://simplywall.st/discover/investing-ideas"} className={"btn btn--gold mt-[24px]"}>
                <LocalizedText en={"More investing ideas"} />
              </a>
            </div>
          </div>
          <div className={"split split--reverse"}>
            <div className={"screener-visual flex w-[709px] shrink justify-center"}>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/snowflake-animation.webp")} alt={"Snowflake screener"} className={"h-auto w-[633px] rounded-[16px]"} />
            </div>
            <div className={"screener-text w-[709px] shrink px-[24px]"}>
              <h2 className={"eyebrow"}>
                <LocalizedText en={"Snowflake "} />
                <span className={"serif"}>
                  <LocalizedText en={"Screener"} />
                </span>
              </h2>
              <h3 className={"font-[family-name:var(--sans)] text-[28px] font-normal leading-[30px]"}>
                <LocalizedText en={"Let the "} />
                <span className={"serif"}>
                  <LocalizedText en={"winners come to you."} />
                </span>
              </h3>
              <p className={"mt-[14px] font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
                <LocalizedText en={"Use our visual analysis to filter the global market by your exact criteria for growth, value, or dividends. We’ll then scan and notify you the moment a new stock fits your specific profile."} />
              </p>
              <a href={"https://simplywall.st/screener/create"} className={"btn btn--gold mt-[24px]"}>
                <LocalizedText en={"Try Snowflake Screener for free"} />
              </a>
            </div>
          </div>
        </div>
      </section>
  );
}
