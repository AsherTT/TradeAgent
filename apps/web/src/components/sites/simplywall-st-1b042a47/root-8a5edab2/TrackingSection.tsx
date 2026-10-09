import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function TrackingSection() {
  return (
      <section className={"py-[40px] text-center"} data-section={"tracking"}>
        <div className={"mx-auto max-w-screen-xl"}>
          <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Header_7.png")} alt={""} />
        </div>
        <h2 className={"eyebrow mt-[20px]"}>
          <LocalizedText en={"Portfolio "} />
          <span className={"serif"}>
            <LocalizedText en={"Tracking & Analysis"} />
          </span>
        </h2>
        <h2 className={"heading-40-bold"}>
          <LocalizedText en={"Build a life-changing portfolio"} />
          {" "}
          <span className={"serif"}>
            <LocalizedText en={"driven by logic, not luck."} />
          </span>
        </h2>
        <p className={"mx-auto mb-0 mt-[10px] max-w-[1200px] font-[family-name:var(--sans)] text-[16px] font-normal leading-[20px]"}>
          <LocalizedText en={"Gain confidence with portfolio insights that give you a competitive edge."} />
        </p>
        <div className={"tracking__cards mx-auto flex max-w-[1272px] justify-center gap-[48px] pt-[50px] text-left"}>
          <div className={"card flex !w-[376px] flex-col !gap-[32px]"}>
            <div className={"flex h-[48px] items-end"}>
              <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Exclude.png")} alt={""} className={"h-[48px] w-auto rounded-[16px]"} />
            </div>
            <div>
              <h3 className={"mb-[14px] font-[family-name:var(--sans)] text-[18px] font-normal leading-[24px]"}>
                <LocalizedText en={"All of your portfolios in one place."} />
              </h3>
              <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
                <LocalizedText en={"Track multiple accounts and brokers with ease."} />
              </p>
            </div>
          </div>
          <div className={"card flex !w-[376px] flex-col !gap-[32px]"}>
            <div className={"flex h-[48px] items-end"}>
              <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Group-1872.png")} alt={""} className={"h-[48px] w-auto rounded-[16px]"} />
            </div>
            <div>
              <h3 className={"mb-[14px] font-[family-name:var(--sans)] text-[18px] font-normal leading-[24px]"}>
                <LocalizedText en={"Import your portfolio data in minutes."} />
              </h3>
              <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
                <LocalizedText en={"Sync with 2000+ brokers or import your trade history quickly."} />
              </p>
            </div>
          </div>
          <div className={"card flex !w-[376px] flex-col !gap-[32px]"}>
            <div className={"flex h-[48px] items-end"}>
              <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/shield.png")} alt={""} className={"h-[48px] w-auto rounded-[16px]"} />
            </div>
            <div>
              <h3 className={"mb-[14px] font-[family-name:var(--sans)] text-[18px] font-normal leading-[24px]"}>
                <LocalizedText en={"Your portfolio, stored securely."} />
              </h3>
              <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
                <LocalizedText en={"Rest easy knowing your portfolio data is encrypted end to end."} />
              </p>
            </div>
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
