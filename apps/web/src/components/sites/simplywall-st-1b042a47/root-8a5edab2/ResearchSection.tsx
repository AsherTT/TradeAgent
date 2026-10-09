"use client";

import { LocalizedImage, LocalizedText } from "../shared/i18n/LanguageProvider";

import { useState } from "react";
import { getSourceAsset } from "../shared/assets";
import { researchTabs } from "./research-tabs";

export function ResearchSection() {
  const [activeIndex, setActiveIndex] = useState(0);
  return (
      <section className={"bg-[var(--ink)] pb-[60px] pt-[40px] text-center text-white"} data-section={"research"}>
        <div className={"wrap"}>
          <div>
            <h2 className={"eyebrow eyebrow--gold"}>
              <LocalizedText en={"Discovery "} />
              <span className={"serif"}>
                <LocalizedText en={"& Research"} />
              </span>
            </h2>
            <h3 className={"heading-40-light"}>
              <LocalizedText en={"The full story, "} />
              <span className={"serif"}>
                <LocalizedText en={"backed by data."} />
              </span>
            </h3>
            <p className={"mt-[10px] font-[family-name:var(--ui)] text-[15px] leading-[20px] text-[rgba(255,255,255,0.85)]"}>
              <LocalizedText en={"We condense thousands of data points into one visual report. From debt to growth, get the institutional-grade clarity you need in minutes, not hours."} />
            </p>
          </div>
          <div className={"mx-auto mt-[64px] flex h-[91px] max-w-screen-xl items-center gap-[24px] text-left max-[1350px]:h-auto max-[1350px]:flex-col max-[1350px]:items-start"}>
            <div className={"flex w-[329px] flex-none flex-col gap-[8px]"}>
              <span className={"font-[family-name:var(--ui)] text-[14px] leading-[20px] text-white"}>
                <LocalizedText en={"Institutional Quality Data from"} />
              </span>
              <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/sp-global-logo.png")} alt={"S&P Global Market Intelligence"} className={"w-[160px]"} />
            </div>
            <div className={"flex flex-1 max-[1350px]:flex-wrap max-[1350px]:gap-[24px]"}>
              <div className={"flex w-[293px] flex-col gap-[18px]"}>
                <div className={"font-[family-name:var(--sans)] text-[36px] font-normal leading-[20px] text-[var(--gold)]"}>
                  <LocalizedText en={"120k"} />
                </div>
                <div className={"font-[family-name:var(--serif)] text-[16px] font-light leading-[20px] text-[var(--gold)]"}>
                  <LocalizedText en={"Stocks worldwide"} />
                </div>
              </div>
              <div className={"flex w-[293px] flex-col gap-[18px]"}>
                <div className={"font-[family-name:var(--sans)] text-[36px] font-normal leading-[20px] text-[var(--gold)]"}>
                  <LocalizedText en={"90"} />
                </div>
                <div className={"font-[family-name:var(--serif)] text-[16px] font-light leading-[20px] text-[var(--gold)]"}>
                  <LocalizedText en={"Global markets"} />
                </div>
              </div>
              <div className={"flex w-[293px] flex-col gap-[18px]"}>
                <div className={"font-[family-name:var(--sans)] text-[36px] font-normal leading-[20px] text-[var(--gold)]"}>
                  <LocalizedText en={"10 yrs +"} />
                </div>
                <div className={"font-[family-name:var(--serif)] text-[16px] font-light leading-[20px] text-[var(--gold)]"}>
                  <LocalizedText en={"Historical Data"} />
                </div>
              </div>
            </div>
          </div>
          <div className={"mx-auto mt-[72px] flex max-w-screen-xl gap-0 px-[24px] text-left max-[991px]:flex-col"}>
            <div className="w-[350px] flex-none pr-[24px] max-[991px]:w-full">
          {researchTabs.map((tab, index) => (
            <div key={tab.label} className={activeIndex === index ? "tab is-active" : "tab"} role="button" tabIndex={0} aria-pressed={activeIndex === index} onClick={() => setActiveIndex(index)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setActiveIndex(index); } }}>
              <LocalizedImage src={getSourceAsset(tab.icon)} alt="" />
              <div>
                <h4 className="tab__name"><LocalizedText en={tab.label} /></h4>
                <p className="tab__desc"><LocalizedText en={tab.description} /></p>
              </div>
            </div>
          ))}
        </div>
            <div className={"carousel__stage relative h-[571px] min-w-0 flex-1 overflow-hidden rounded-[6px] bg-[#0d131d]"}>
              <div className={"flex h-[29px] items-center gap-[6px] bg-[#37455a] px-[12px]"}>
                <i className={"h-[10px] w-[10px] rounded-full bg-[rgba(255,255,255,0.35)]"}>

                </i>
                <i className={"h-[10px] w-[10px] rounded-full bg-[rgba(255,255,255,0.35)]"}>

                </i>
                <i className={"h-[10px] w-[10px] rounded-full bg-[rgba(255,255,255,0.35)]"}>

                </i>
              </div>
              {researchTabs.map((tab, index) => (
          <figure key={tab.label} className={activeIndex === index ? "is-active" : ""}>
            <LocalizedImage src={getSourceAsset(tab.src)} alt={tab.alt} className="h-auto w-full" />
          </figure>
        ))}
            </div>
          </div>
        </div>
      </section>
  );
}
