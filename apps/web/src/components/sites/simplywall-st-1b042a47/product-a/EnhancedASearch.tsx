"use client";

import { LocalizedImage, useLanguage } from "../shared/i18n/LanguageProvider";
import { getSourceAsset } from "../shared/assets";

export function EnhancedASearch() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  return (
    <section className={"bg-[var(--tan)]"} data-section={"which"} id="companies">
      <div className={"which__inner mx-auto flex max-w-[940px] items-center gap-0 p-[40px] max-[640px]:px-[20px]"}>
        <div className={"which__art flex w-[508px] flex-none justify-center"}>
          <LocalizedImage src={getSourceAsset("https://simplywall.st/cdn-cgi/image/format=auto,width=1920,quality=80/https://marketing.simplywall.st/assets/image_273-1.png")} alt={""} className={"h-auto w-[381px] shadow-[rgba(150,163,181,0.08)_0_4px_24px]"} />
        </div>
        <div className={"which__copy w-[432px] flex-none"}>
          <h2 className={"font-[family-name:var(--sans)] text-[40px] font-normal leading-[48px] max-[640px]:text-[30px]"}>
            {zh ? "下一家公司，" : "Which company will you"}
            {" "}
            <span className={"serif"}>
              {zh ? "你想研究什么？" : "research next?"}
            </span>
          </h2>
          <p className={"mt-[16px] font-[family-name:var(--ui)] text-[15px] leading-[22px]"}>
            {zh ? "登录后搜索本地公司目录，打开公司对象与自己的研究记录。目录范围始终明确。" : "Sign in to search the local company directory and open your own research. Directory coverage is explicit."}
          </p>
          <a href={"/app#companies"} className={"mt-[24px] flex h-[56px] items-center gap-[14px] rounded-[12px] bg-white px-[20px] font-[family-name:var(--ui)] text-[17px] text-[var(--slate)] shadow-[rgba(0,0,0,0.2)_0_4px_12px]"}>
            <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/search-3.svg")} alt={""} className={"h-[22px] w-[22px]"} />
            {zh ? "登录并搜索公司" : "Sign in and search companies"}
          </a>
          <div className={"mt-[20px] font-[family-name:var(--ui)] text-[14px]"}>
            <span className={"mb-[6px] block"}>
              {zh ? "研究入口" : "Research entries"}
            </span>
            <ul className={"flex gap-[24px] font-[family-name:var(--serif)] text-[16px] font-light"}>
              <li>
                <a href={"/app#companies"} className={"hover:underline"}>
                  {zh ? "公司目录" : "Directory"}
                </a>
              </li>
              <li>
                <a href={"/app/research"} className={"hover:underline"}>
                  {zh ? "我的研究" : "My research"}
                </a>
              </li>
              <li>
                <a href={"#demo"} className={"hover:underline"}>
                  {zh ? "年度演示" : "Annual demo"}
                </a>
              </li>
              <li>
                <a href={"#workflow"} className={"hover:underline"}>
                  {zh ? "研究流程" : "Workflow"}
                </a>
              </li>
              <li className={"max-[640px]:hidden"}>
                <a href={"/register"} className={"hover:underline"}>
                  {zh ? "创建账户" : "Create account"}
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
