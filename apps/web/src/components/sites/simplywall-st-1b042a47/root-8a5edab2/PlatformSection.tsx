import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function PlatformSection() {
  return (
      <section className={"px-[40px] pb-[80px] pt-[40px] text-center"} data-section={"platform"}>
        <h2 className={"heading-40"}>
          <LocalizedText en={"One platform. "} />
          <span className={"serif"}>
            <LocalizedText en={"Better decision making."} />
          </span>
        </h2>
        <p className={"mt-[24px] font-[family-name:var(--sans)] text-[16px] font-normal leading-[19px]"}>
          <LocalizedText en={"Stop reacting and start growing with data and insights the pros use."} />
        </p>
        <div className={"platform__grid mx-auto mt-[40px] grid max-w-[1272px] grid-cols-[1fr_1fr_1fr] gap-[41px] text-left"}>
          <div>
            <LocalizedImage className={"h-[42px] w-[42px]"} src={getSourceAsset("https://marketing.simplywall.st/assets/eye-1.svg")} alt={""} />
            <div className={"mb-[11px] mt-[10px] h-px bg-[var(--bronze)] opacity-55"}>

            </div>
            <h3 className={"mb-[20px] font-[family-name:var(--sans)] text-[24px] font-normal leading-[28.8px]"}>
              <LocalizedText en={"Master your portfolio."} />
            </h3>
            <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
              <LocalizedText en={"A high-fidelity view and analysis of your portfolio, bringing together performance, risk, and opportunities into one centralized location."} />
            </p>
          </div>
          <div>
            <LocalizedImage className={"h-[42px] w-[42px]"} src={getSourceAsset("https://marketing.simplywall.st/assets/search-3.svg")} alt={""} />
            <div className={"mb-[11px] mt-[10px] h-px bg-[var(--bronze)] opacity-55"}>

            </div>
            <h3 className={"mb-[20px] font-[family-name:var(--sans)] text-[24px] font-normal leading-[28.8px]"}>
              <LocalizedText en={"Find your next "} />
              <span className={"serif"}>
                <LocalizedText en={"hidden gem."} />
              </span>
            </h3>
            <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
              <LocalizedText en={"Filter and research 120,000 global stocks using deep-dive fundamentals and unbiased valuations to find your next winning move."} />
            </p>
          </div>
          <div>
            <LocalizedImage className={"h-[42px] w-[42px]"} src={getSourceAsset("https://marketing.simplywall.st/assets/activity-2.svg")} alt={""} />
            <div className={"mb-[11px] mt-[10px] h-px bg-[var(--bronze)] opacity-55"}>

            </div>
            <h3 className={"mb-[20px] font-[family-name:var(--sans)] text-[24px] font-normal leading-[28.8px]"}>
              <LocalizedText en={"Keep your "} />
              <span className={"serif"}>
                <LocalizedText en={"finger on the pulse."} />
              </span>
            </h3>
            <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
              <LocalizedText en={"Stay informed with daily alerts on earnings, dividends, valuation changes and insider trading - so you can act decisively when it counts."} />
            </p>
          </div>
        </div>
        <div className={"btn-row btn-row--centre mt-[40px]"}>
          <a href={"https://simplywall.st/portfolio/demo"} className={"btn btn--gold"}>
            <LocalizedText en={"View Portfolio demo"} />
          </a>
          <a href={"/register"} className={"btn btn--black"}>
            <LocalizedText en={"Create a TradeAgent account"} />
          </a>
        </div>
      </section>
  );
}
