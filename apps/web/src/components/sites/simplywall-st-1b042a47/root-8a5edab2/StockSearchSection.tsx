import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function StockSearchSection() {
  return (
      <section className={"bg-[var(--tan)]"} data-section={"which"}>
        <div className={"which__inner mx-auto flex max-w-[940px] items-center gap-0 p-[40px] max-[640px]:px-[20px]"}>
          <div className={"which__art flex w-[508px] flex-none justify-center"}>
            <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/image_273-1.png")} alt={""} className={"h-auto w-[381px] shadow-[rgba(150,163,181,0.08)_0_4px_24px]"} />
          </div>
          <div className={"which__copy w-[432px] flex-none"}>
            <h2 className={"font-[family-name:var(--sans)] text-[40px] font-normal leading-[48px] max-[640px]:text-[30px]"}>
              <LocalizedText en={"Which stocks are you"} />
              {" "}
              <span className={"serif"}>
                <LocalizedText en={"currently weighing up?"} />
              </span>
            </h2>
            <p className={"mt-[16px] font-[family-name:var(--ui)] text-[15px] leading-[22px]"}>
              <LocalizedText en={"Search from 120,000 global stocks to see thousands of data points condensed into one visual report."} />
            </p>
            <a href={"https://simplywall.st/stocks"} className={"mt-[24px] flex h-[56px] items-center gap-[14px] rounded-[12px] bg-white px-[20px] font-[family-name:var(--ui)] text-[17px] text-[var(--slate)] shadow-[rgba(0,0,0,0.2)_0_4px_12px]"}>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/search-3.svg")} alt={""} className={"h-[22px] w-[22px]"} />
              <LocalizedText en={"Search any stock to research for free"} />
            </a>
            <div className={"mt-[20px] font-[family-name:var(--ui)] text-[14px]"}>
              <span className={"mb-[6px] block"}>
                <LocalizedText en={"Popular stocks"} />
              </span>
              <ul className={"flex gap-[24px] font-[family-name:var(--serif)] text-[16px] font-light"}>
                <li>
                  <a href={"https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple"} className={"hover:underline"}>
                    <LocalizedText en={"Apple"} />
                  </a>
                </li>
                <li>
                  <a href={"https://simplywall.st/stocks/us/retail/nasdaq-amzn/amazoncom"} className={"hover:underline"}>
                    <LocalizedText en={"Amazon"} />
                  </a>
                </li>
                <li>
                  <a href={"https://simplywall.st/stocks/us/media/nasdaq-googl/alphabet"} className={"hover:underline"}>
                    <LocalizedText en={"Alphabet"} />
                  </a>
                </li>
                <li>
                  <a href={"https://simplywall.st/stocks/us/semiconductors/nasdaq-nvda/nvidia"} className={"hover:underline"}>
                    <LocalizedText en={"NVIDIA"} />
                  </a>
                </li>
                <li className={"max-[640px]:hidden"}>
                  <a href={"https://simplywall.st/stocks/us/automobiles/nasdaq-tsla/tesla"} className={"hover:underline"}>
                    <LocalizedText en={"Tesla"} />
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
  );
}
