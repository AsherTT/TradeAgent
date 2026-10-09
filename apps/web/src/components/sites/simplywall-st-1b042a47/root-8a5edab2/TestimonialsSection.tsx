import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function TestimonialsSection() {
  return (
      <section className={"bg-[linear-gradient(var(--cream),var(--gold))] px-[40px] pb-[40px] text-center"} data-section={"trusted"}>
        <div className={"mx-auto max-w-[833px] pt-[40px]"}>
          <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/reviews.svg")} alt={"4.6 App Store, 4.3 Trustpilot, 4.6 Google Play"} className={"mx-auto mb-[40px] w-[523px]"} />
          <h2 className={"font-[family-name:var(--sans)] text-[50px] font-normal leading-[60px] max-[640px]:text-[34px] max-[640px]:leading-[42px]"}>
            <LocalizedText en={"Trusted by 7M+ "} />
            <span className={"serif"}>
              <LocalizedText en={"investors worldwide"} />
            </span>
          </h2>
        </div>
        <div className={"testimonials mx-auto mt-[28px] flex max-w-[1337px] items-start gap-[32px] text-left"}>
          <div className={"flex min-w-0 flex-1 flex-col gap-[32px]"}>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Stuart Aberdein"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"Portugal"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <strong className={"text-[15px] font-semibold"}>
                  <LocalizedText en={"Brilliant site. Highly recommended"} />
                </strong>
                <p>
                  <LocalizedText en={"It's an excellent site. Very well laid out and easy to use. It's great for quickly screening shares that fit a set of requirements. It saves huge amounts of research time. They are also very ethical and reasonable."} />
                </p>
                <p>
                  <LocalizedText en={"I hadn't used the site for a while because I had built my portfolio and didn't want to make changes. I had forgotten to cancel my auto-renewing membership and only realised when the invoice was processed. Although it was entirely my fault, they processed a refund for me. Nice people."} />
                </p>
              </div>
            </article>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Nuno"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"Spain"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <strong className={"text-[15px] font-semibold"}>
                  <LocalizedText en={"Super useful"} />
                </strong>
                <p>
                  <LocalizedText en={"Overall great experience. Excited for adding more features to the new portfolio and rolling out the stock validator tool."} />
                </p>
              </div>
            </article>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Ryan"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"Canada"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <p>
                  <LocalizedText en={"The app is fantastically well designed, able to get a lot of information visually on whatever aspect of investing is needed, whether it's stock analysis, portfolio analysis, etc. This allows for ease in navigating between various aspects of a stock and a much shorter time spent analyzing it. Love it."} />
                </p>
              </div>
            </article>
          </div>
          <div className={"flex min-w-0 flex-1 flex-col gap-[32px]"}>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Pamela"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"United States"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <p>
                  <LocalizedText en={"I took several years off from investing and now I renewed my membership, I was very happy before and looking for to even tools to work with research, and keeping up with my portfolio. Thank you Simply Wall ST. Pam from SC"} />
                </p>
              </div>
            </article>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Anonymous Customer"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"United Kingdom"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <strong className={"text-[15px] font-semibold"}>
                  <LocalizedText en={"Best informative site for Value based investing"} />
                </strong>
                <p>
                  <LocalizedText en={"Fantastic coverage of global stocks. Their layout is super user friendly, simple yet effective enough to give you all the right info needed for value investing. Portfolio and watchlist features are excellent. Best feature is the snowflake analysis with screener."} />
                </p>
                <p>
                  <LocalizedText en={"They also send the articles and timely updates that cut through any jargon and provide very insightful information that layman like me can understand. Very happy to have found Simply Wall St."} />
                </p>
              </div>
            </article>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Ricci Johannessen"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"South Africa"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <p>
                  <LocalizedText en={"Simply Wall St is packed with loads of tools and info. As a beginner I am extremely excited to get stuck in. I know Simply Wall St will help me manage and improve the quality of my portfolio and watchlist."} />
                </p>
              </div>
            </article>
          </div>
          <div className={"flex min-w-0 flex-1 flex-col gap-[32px]"}>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Rajan"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"Australia"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <p>
                  <LocalizedText en={"Glad to be able to subscribe to your premium plan. It’s a useful product particularly for the novice trader to get a good heads up on building up an investment portfolio. Pleasure dealing with the staff as well. Excellent value"} />
                </p>
              </div>
            </article>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Gary"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"United Kingdom"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <p>
                  <LocalizedText en={"Seems to have a multitude of info, but broken down and explained simply enough for the amateur investor, yet intuitive enough for the more seasoned investor."} />
                </p>
                <p>
                  <LocalizedText en={"Very easy to keep track of your portfolio, and keeps providing important updates when there's a significant alert on stocks... Only downside, no info on funds, that I can find."} />
                </p>
              </div>
            </article>
            <article className={"testimonial flex flex-col !gap-[16px] border border-solid border-[var(--bronze)] !p-[16px]"}>
              <div className={"flex items-baseline gap-[8px] font-[family-name:var(--ui)] text-[15px]"}>
                <b className={"font-semibold"}>
                  <LocalizedText en={"Georgy"} />
                </b>
                <span className={"text-[rgba(25,24,22,0.62)]"}>
                  <LocalizedText en={"India"} />
                </span>
              </div>
              <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/stars.svg")} alt={"5 stars"} className={"h-[16px] w-[96px] mix-blend-multiply"} />
              <div className={"flex flex-col gap-[8px] font-[family-name:var(--ui)] text-[14px] leading-[22px]"}>
                <strong className={"text-[15px] font-semibold"}>
                  <LocalizedText en={"The top one in the stock tools i have ever used"} />
                </strong>
                <p>
                  <LocalizedText en={"I loved your teame for the regular email updates you used to send me on my watchlisted indian stockmarket companies. That made me go ahead and take a plan to get the portfolio experience also. Seamless plan purchase process too. Way to go!!!"} />
                </p>
              </div>
            </article>
          </div>
        </div>
      </section>
  );
}
