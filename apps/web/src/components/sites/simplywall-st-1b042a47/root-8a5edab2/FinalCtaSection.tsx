import { LocalizedText } from "../shared/i18n/LanguageProvider";


export function FinalCtaSection() {
  return (
      <section className={"p-[40px] text-center"} data-section={"narratives"}>
        <div className={"mx-auto max-w-[1062px] px-[40px] pt-[20px]"}>
          <h2 className={"heading-40 source-inline-b1f22df6"}>
            <LocalizedText en={"Build your case. "} />
            <span className={"serif"}>
              <LocalizedText en={"Own the story."} />
            </span>
          </h2>
          <p className={"mt-[10px] h-[38px] font-[family-name:var(--ui)] text-[15px] leading-[19px]"}>
            <LocalizedText en={"Stop reacting to market mood swings. Use our Narratives framework to build, track, and evolve a thesis for every stock you own."} />
            <br />
          </p>
          <h3 className={"mt-[21px] pb-[40px] font-[family-name:var(--serif)] text-[24px] font-light leading-[28.8px]"}>
            <LocalizedText en={"Successful investors follow these 3 key principles"} />
          </h3>
          <div className={"relative mt-[32px] flex gap-[16px]"}>
            <div className={"absolute inset-x-[162px] top-[4px] h-[24px] bg-[rgba(152,110,46,0.25)] max-[991px]:hidden"}>

            </div>
            <ul className={"relative z-[1] flex flex-1 max-[640px]:flex-col max-[640px]:gap-[24px]"}>
              <li className={"flex flex-1 flex-col items-center gap-[18px] px-[16px]"}>
                <div className={"flex h-[32px] w-[32px] items-center justify-center rounded-full bg-[var(--bronze)] font-[family-name:var(--ui)] text-[16px] text-white"}>
                  <LocalizedText en={"1"} />
                </div>
                <div className={"font-[family-name:var(--serif)] text-[18px] font-light leading-[32px]"}>
                  <LocalizedText en={"Identify a stock"} />
                </div>
              </li>
              <li className={"flex flex-1 flex-col items-center gap-[18px] px-[16px]"}>
                <div className={"flex h-[32px] w-[32px] items-center justify-center rounded-full bg-[var(--bronze)] font-[family-name:var(--ui)] text-[16px] text-white"}>
                  <LocalizedText en={"2"} />
                </div>
                <div className={"font-[family-name:var(--serif)] text-[18px] font-light leading-[32px]"}>
                  <LocalizedText en={"Form your thesis"} />
                </div>
              </li>
              <li className={"flex flex-1 flex-col items-center gap-[18px] px-[16px]"}>
                <div className={"flex h-[32px] w-[32px] items-center justify-center rounded-full bg-[var(--bronze)] font-[family-name:var(--ui)] text-[16px] text-white"}>
                  <LocalizedText en={"3"} />
                </div>
                <div className={"font-[family-name:var(--serif)] text-[18px] font-light leading-[32px]"}>
                  <LocalizedText en={"Set your fair value"} />
                </div>
              </li>
            </ul>
          </div>
          <div className={"mt-[55px] flex flex-col items-center gap-[12px]"}>
            <a href={"/register"} className={"btn btn--lg"}>
              <LocalizedText en={"Create a TradeAgent account"} />
            </a>
            <p className={"font-[family-name:var(--ui)] text-[14px] leading-[26px] text-[rgba(25,24,22,0.7)]"}>
              <LocalizedText en={"Manage your watchlist in your own account."} />
            </p>
          </div>
        </div>
      </section>
  );
}
