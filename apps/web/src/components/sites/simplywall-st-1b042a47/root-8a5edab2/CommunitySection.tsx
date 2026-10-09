import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function CommunitySection() {
  return (
      <section className={"flex flex-col gap-[32px] px-[40px] pb-[100px] pt-[60px] text-center max-[640px]:px-[20px]"} data-section={"community"}>
        <div>
          <h2 className={"eyebrow source-inline-180dd8ea"}>
            <LocalizedText en={"Community "} />
            <span className={"serif"}>
              <LocalizedText en={"Narratives"} />
            </span>
          </h2>
          <h3 className={"heading-48 font-[family-name:var(--sans)] text-[40px] font-normal leading-[48px]"}>
            <LocalizedText en={"Gain insights from"} />
            {" "}
            <span className={"serif"}>
              <LocalizedText en={"like-minded investors"} />
            </span>
          </h3>
        </div>
        <div className={"community__grid mx-auto flex w-full max-w-[1417px] justify-center gap-[80px] max-[1350px]:flex-col max-[1350px]:items-center max-[1350px]:gap-[32px]"}>
          <div className={"flex w-full max-w-[366px] flex-col items-center gap-[8px]"}>
            <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Community_3.1-p-500.png")} alt={""} className={"h-[180px] w-[180px] mix-blend-darken"} />
            <span className={"font-[family-name:var(--serif)] text-[20px] font-light leading-[24px]"}>
              <LocalizedText en={"Value any stock for free in seconds"} />
            </span>
          </div>
          <div className={"flex w-full max-w-[366px] flex-col items-center gap-[8px]"}>
            <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Community_3.22-p-500.png")} alt={""} className={"h-[180px] w-[180px] mix-blend-darken"} />
            <span className={"font-[family-name:var(--serif)] text-[20px] font-light leading-[24px]"}>
              <LocalizedText en={"Participate in discussions"} />
            </span>
          </div>
          <div className={"flex w-full max-w-[366px] flex-col items-center gap-[8px]"}>
            <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/Community_3.33-p-500.png")} alt={""} className={"h-[180px] w-[180px] mix-blend-darken"} />
            <span className={"font-[family-name:var(--serif)] text-[20px] font-light leading-[24px]"}>
              <LocalizedText en={"Get alerts & valuation updates"} />
            </span>
          </div>
        </div>
        <div className={"btn-row btn-row--centre mt-[40px]"}>
          <a href={"https://simplywall.st/community/narratives/"} className={"btn btn--gold"}>
            <LocalizedText en={"Explore Community"} />
          </a>
          <a href={"/register"} className={"btn btn--black"}>
            <LocalizedText en={"Create a TradeAgent account"} />
          </a>
        </div>
      </section>
  );
}
