import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function PortfolioAnalysisSection() {
  return (
      <section className={"bg-[linear-gradient(var(--cream),var(--gold)_14%,var(--ink))] pb-[40px] pt-[84px]"} data-section={"analysis"}>
        <div className={"wrap"}>
          <div className={"mx-auto flex max-w-screen-xl flex-col gap-[24px]"}>
            <div className={"panel grid grid-cols-[1fr_1fr] items-center bg-[var(--ink)] text-[var(--cream)]"}>
              <div className={"p-[32px]"}>
                <h3 className={"font-[family-name:var(--sans)] text-[40px] font-normal leading-[44px] max-[640px]:text-[28px] max-[640px]:leading-[32px]"}>
                  <LocalizedText en={"Finally see your portfolio's"} />
                  {" "}
                  <span className={"serif"}>
                    <LocalizedText en={"true performance"} />
                  </span>
                </h3>
                <ul className={"my-[20px] flex flex-col"}>
                  <li className={"flex items-center gap-[8px] font-[family-name:var(--sans)] text-[14px] font-normal leading-[20px]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check-1-.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Realized & Unrealized Gains & Losses"} />
                  </li>
                  <li className={"flex items-center gap-[8px] font-[family-name:var(--sans)] text-[14px] font-normal leading-[20px]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check-1-.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Dividend Payments"} />
                  </li>
                  <li className={"flex items-center gap-[8px] font-[family-name:var(--sans)] text-[14px] font-normal leading-[20px]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check-1-.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Currency Gains & Losses"} />
                  </li>
                  <li className={"flex items-center gap-[8px] font-[family-name:var(--sans)] text-[14px] font-normal leading-[20px]"}>
                    <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/check-1-.svg")} alt={""} className={"h-[16px] w-[16px]"} />
                    <LocalizedText en={"Annualized Return (IRR)"} />
                  </li>
                </ul>
                <p className={"mt-[20px] font-[family-name:var(--sans)] text-[16px] font-light leading-[20px]"}>
                  <LocalizedText en={"Stop wondering how you're actually doing. We calculate your real returns so you know exactly where you stand."} />
                </p>
              </div>
              <div className={"flex justify-center p-[24px]"}>
                <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Graphic-1.png")} alt={"Portfolio return breakdown waterfall chart"} className={"h-auto w-full"} />
              </div>
            </div>
            <div className={"analysis__row grid grid-cols-[1fr_1fr] gap-[24px]"}>
              <div className={"flex flex-col bg-[var(--ink)] text-[var(--cream)]"}>
                <div className={"px-[32px] pb-[52px] pt-[32px]"}>
                  <h3 className={"font-[family-name:var(--sans)] text-[40px] font-normal leading-[44px] max-[640px]:text-[28px] max-[640px]:leading-[32px]"}>
                    <LocalizedText en={"Portfolio Snowflake"} />
                  </h3>
                  <p className={"mt-[20px] font-[family-name:var(--sans)] text-[16px] font-light leading-[20px]"}>
                    <LocalizedText en={"Your portfolio’s profile and health at a glance."} />
                  </p>
                  <p className={"mt-[20px] font-[family-name:var(--sans)] text-[16px] font-light leading-[20px]"}>
                    <LocalizedText en={"Our visual analysis instantly flags where you’re winning and where you’re exposed. It’s the ultimate pulse check for the disciplined investor."} />
                  </p>
                </div>
                <div className={"mt-auto pb-[20px]"}>
                  <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Graphic-2.png")} alt={"Portfolio Snowflake visual analysis"} className={"h-auto w-full"} />
                </div>
              </div>
              <div className={"flex flex-col bg-[var(--ink)] text-[var(--cream)]"}>
                <div className={"px-[32px] pb-[52px] pt-[32px]"}>
                  <h3 className={"font-[family-name:var(--sans)] text-[40px] font-normal leading-[44px] max-[640px]:text-[28px] max-[640px]:leading-[32px]"}>
                    <LocalizedText en={"Dividend quality"} />
                    <br />
                    <LocalizedText en={"& forecasting"} />
                  </h3>
                  <p className={"mt-[20px] font-[family-name:var(--sans)] text-[16px] font-light leading-[20px]"}>
                    <LocalizedText en={"We stress-test dividend quality and project your future income, flagging fragile payouts before they’re cut so you can pivot with conviction."} />
                  </p>
                </div>
                <div className={"mt-auto"}>
                  <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Dividend-2.png")} alt={"Dividend quality and forecast chart"} className={"h-auto w-full"} />
                </div>
              </div>
            </div>
            <div className={"panel grid grid-cols-[1fr_1fr] items-center bg-[var(--ink)] text-[var(--cream)]"}>
              <div className={"flex justify-center py-[16px] pl-0 pr-[24px]"}>
                <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Graphic-4.png")} alt={"Portfolio value versus US Market chart"} className={"h-auto w-full"} />
              </div>
              <div className={"p-[32px]"}>
                <h3 className={"font-[family-name:var(--sans)] text-[40px] font-normal leading-[44px] max-[640px]:text-[28px] max-[640px]:leading-[32px]"}>
                  <LocalizedText en={"Portfolio valuation"} />
                </h3>
                <p className={"mt-[20px] font-[family-name:var(--sans)] text-[16px] font-light leading-[20px]"}>
                  <LocalizedText en={"Know what your portfolio is actually worth."} />
                </p>
                <p className={"mt-[20px] font-[family-name:var(--sans)] text-[16px] font-light leading-[20px]"}>
                  <LocalizedText en={"We aggregate the intrinsic value of every stock you own. See the difference between the market's price and your portfolio's true value."} />
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
  );
}
