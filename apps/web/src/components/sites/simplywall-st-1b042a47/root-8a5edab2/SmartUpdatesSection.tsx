import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function SmartUpdatesSection() {
  return (
      <section className={"bg-[var(--cream)] pt-[80px] text-center"} data-section={"updates"}>
        <div className={"wrap"}>
          <div className={"mx-auto max-w-[1055px]"}>
            <h2 className={"eyebrow source-inline-145688af"}>
              <LocalizedText en={"Smart "} />
              <span className={"serif"}>
                <LocalizedText en={"Updates"} />
              </span>
            </h2>
            <h3 className={"heading-40 source-inline-b1f22df6"}>
              <LocalizedText en={"Never miss "} />
              <span className={"serif"}>
                <LocalizedText en={"your moment again."} />
              </span>
            </h3>
            <p className={"mt-[10px] font-[family-name:var(--sans)] text-[16px] font-normal leading-[21.5px]"}>
              <LocalizedText en={"Stay informed with daily alerts on earnings, dividends, valuation changes, and key events - so you can act decisively when it counts."} />
            </p>
            <div className={"btn-row btn-row--centre mt-[34px]"}>
              <a href={"/app"} className={"btn btn--gold"}>
                <LocalizedText en={"Start your watchlist"} />
              </a>
              <a href={"https://simplywall.st/portfolio/demo"} className={"btn btn--ink"}>
                <LocalizedText en={"Set up a portfolio in minutes"} />
              </a>
            </div>
          </div>
        </div>
        <LocalizedImage className={"mt-[60px] h-auto w-full px-[100px] mix-blend-difference"} src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/recent-updates.png")} alt={"Recent updates timeline"} />
      </section>
  );
}
