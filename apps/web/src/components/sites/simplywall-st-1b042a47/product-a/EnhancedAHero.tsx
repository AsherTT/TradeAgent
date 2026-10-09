"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useLanguage } from "../shared/i18n/LanguageProvider";

export function EnhancedAHero({ media }: { media: ReactNode }) {
  const { locale } = useLanguage();
  const chinese = locale === "zh";

  return (
    <section className="home-hero bg-[var(--cream)] pb-[64px] pt-[60px]" data-section="hero">
      <div className="wrap">
        <div className="hero__content flex items-center gap-[40px] pt-[40px]">
          <div className="hero__text flex w-[540px] flex-none flex-col gap-[8px]">
            <h1 className="mb-[10px] font-[family-name:var(--sans)] text-[52px] font-normal leading-[57.2px] max-[640px]:text-[36px] max-[640px]:leading-[40px]">
              {chinese ? "欢迎来到你的" : "Welcome to your"}{" "}
              <span className="serif text-[var(--bronze)]">
                {chinese ? "公司研究中心。" : "Company Research Center."}
              </span>
            </h1>
            <p className="mb-[10px] font-[family-name:var(--sans)] text-[18px] font-normal leading-[21.6px]">
              {chinese
                ? "关注公司、阅读财务、追踪研究与核验证据——把公司、问题和来源连接在同一个空间。"
                : "Follow companies, read financials and trace research back to evidence — companies, questions and sources in one space."}
            </p>
            <div className="btn-row">
              <Link href="/app" className="btn btn--gold">
                {chinese ? "开始研究" : "Start research"}
              </Link>
              <a href="#demo" className="btn btn--black">
                {chinese ? "查看产品演示" : "Explore the demo"}
              </a>
            </div>
            <p className="pb-[10px] font-[family-name:var(--ui)] text-[12px] leading-[20px] text-[#3a3226]">
              {chinese ? "演示使用虚构数据，真实研究需登录。" : "Fictional demo data. Sign in for your own research."}
            </p>
          </div>
          <div className="flex h-[575px] min-w-0 flex-1 items-center justify-end max-[991px]:w-full">
            <div className="w-[837px] max-w-full bg-[var(--slate)] shadow-[rgba(0,0,0,0.2)_0_24px_32px_5px]">
              {media}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
