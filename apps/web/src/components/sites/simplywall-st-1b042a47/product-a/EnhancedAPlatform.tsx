"use client";

import { LocalizedImage, useLanguage } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function EnhancedAPlatform() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  return (
    <section className={"px-[40px] pb-[80px] pt-[40px] text-center"} data-section={"platform"}>
      <h2 className={"heading-40"}>
        {zh ? "一个研究空间。" : "One research space. "}
        <span className={"serif"}>
          {zh ? "连接公司与证据。" : "Connect companies and evidence."}
        </span>
      </h2>
      <p className={"mt-[24px] font-[family-name:var(--sans)] text-[16px] font-normal leading-[19px]"}>
        {zh ? "从自己的公司目录开始，组织研究、阅读结果、追踪来源。" : "Start with your company directory, organize research and follow its sources."}
      </p>
      <div className={"platform__grid mx-auto mt-[40px] grid max-w-[1272px] grid-cols-[1fr_1fr_1fr] gap-[41px] text-left"}>
        <div id="portal">
          <LocalizedImage className={"h-[42px] w-[42px]"} src={getSourceAsset("https://marketing.simplywall.st/assets/eye-1.svg")} alt={""} />
          <div className={"mb-[11px] mt-[10px] h-px bg-[var(--bronze)] opacity-55"}>

          </div>
          <h3 className={"mb-[20px] font-[family-name:var(--sans)] text-[24px] font-normal leading-[28.8px]"}>
            {zh ? "公司与研究门户" : "Company & research portal"}
          </h3>
          <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
            {zh ? "账户入口已接通：关注公司、活动任务与保存的研究，都归属于自己的账户。" : "Connected: followed companies, active tasks and saved research belong to your own account."}
          </p>
        </div>
        <div id="financials">
          <LocalizedImage className={"h-[42px] w-[42px]"} src={getSourceAsset("https://marketing.simplywall.st/assets/search-3.svg")} alt={""} />
          <div className={"mb-[11px] mt-[10px] h-px bg-[var(--bronze)] opacity-55"}>

          </div>
          <h3 className={"mb-[20px] font-[family-name:var(--sans)] text-[24px] font-normal leading-[28.8px]"}>
            {zh ? "读懂财务，" : "Read financials, "}
            <span className={"serif"}>
              {zh ? "看清期间。" : "understand the period."}
            </span>
          </h3>
          <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
            {zh ? "已有年度事实与部分指标；多期表格、趋势和分部正在开发。先体验明确标注的年度演示。" : "Annual facts and limited metrics exist. Multi-period tables, trends and segments are in development; try the labeled demo."}
          </p>
        </div>
        <div id="reading">
          <LocalizedImage className={"h-[42px] w-[42px]"} src={getSourceAsset("https://marketing.simplywall.st/assets/activity-2.svg")} alt={""} />
          <div className={"mb-[11px] mt-[10px] h-px bg-[var(--bronze)] opacity-55"}>

          </div>
          <h3 className={"mb-[20px] font-[family-name:var(--sans)] text-[24px] font-normal leading-[28.8px]"}>
            {zh ? "让每条结论，" : "Follow each finding "}
            <span className={"serif"}>
              {zh ? "回到来源。" : "back to its source."}
            </span>
          </h3>
          <p className={"font-[family-name:var(--sans)] text-[14px] font-light leading-[20px]"}>
            {zh ? "基础研究报告已有章节与引用；保存片段、原文定位和并排核验将逐步接入。" : "Basic reports contain sections and citations. Saved excerpts, source location and side-by-side verification will follow."}
          </p>
        </div>
      </div>
      <div className={"btn-row btn-row--centre mt-[40px]"}>
        <a href={"#demo"} className={"btn btn--gold"}>
          {zh ? "查看产品演示" : "Explore the demo"}
        </a>
        <a href={"/register"} className={"btn btn--black"}>
          {zh ? "创建研究账户" : "Create a research account"}
        </a>
      </div>
    </section>
  );
}
