import { LocalizedText } from "../shared/i18n/LanguageProvider";
import { HeroMedia } from "./HeroMedia";
import { HeroReviews } from "./HeroReviews";

export function HeroSection() {
  return (
      <section className={"home-hero bg-[var(--cream)] pb-[64px] pt-[60px]"} data-section={"hero"}>
        <div className={"wrap"}>
          <div className={"hero__content flex items-center gap-[40px] pt-[40px]"}>
            <div className={"hero__text flex w-[540px] flex-none flex-col gap-[8px]"}>
              <h1 className={"mb-[10px] font-[family-name:var(--sans)] text-[52px] font-normal leading-[57.2px] max-[640px]:text-[36px] max-[640px]:leading-[40px]"}>
                <LocalizedText en={"Welcome to your"} />
                {" "}
                <span className={"serif text-[var(--bronze)]"}>
                  <LocalizedText en={"Portfolio Command Center."} />
                </span>
              </h1>
              <p className={"mb-[10px] font-[family-name:var(--sans)] text-[18px] font-normal leading-[21.6px]"}>
                <LocalizedText en={"Stop wasting hours in spreadsheets and start growing your wealth with portfolio analysis, discovery tools and market alerts — all in one place."} />
              </p>
              <div className={"btn-row"}>
                <a href={"https://simplywall.st/portfolio/demo"} className={"btn btn--gold"}>
                  <LocalizedText en={"View Portfolio demo"} />
                </a>
                <a href={"/register"} className={"btn btn--black"}>
                  <LocalizedText en={"Create a TradeAgent account"} />
                </a>
              </div>
              <p className={"pb-[10px] font-[family-name:var(--ui)] text-[12px] leading-[20px] text-[#3a3226]"}>
                <LocalizedText en={"No credit card required."} />
              </p>
            </div>
            <HeroMedia />
          </div>
          <HeroReviews />
        </div>
      </section>
  );
}
