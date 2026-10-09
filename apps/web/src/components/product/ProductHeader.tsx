"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import {
  LanguageSwitcher,
  useLanguage,
} from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";

export function ProductHeader({
  application = false,
}: {
  application?: boolean;
}) {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const menu = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    function dismissOnOutsideClick(event: PointerEvent) {
      if (event.target instanceof Node && !menu.current?.contains(event.target)) {
        menu.current?.removeAttribute("open");
      }
    }
    function dismissOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && menu.current?.open) {
        menu.current.removeAttribute("open");
        menu.current.querySelector("summary")?.focus();
      }
    }
    document.addEventListener("pointerdown", dismissOnOutsideClick);
    document.addEventListener("keydown", dismissOnEscape);
    return () => {
      document.removeEventListener("pointerdown", dismissOnOutsideClick);
      document.removeEventListener("keydown", dismissOnEscape);
    };
  }, []);
  const features = application
    ? [
        ["/app", zh ? "研究门户" : "Research portal"],
        ["/app#companies", zh ? "公司目录" : "Companies"],
        ["/app/research", zh ? "研究与报告" : "Research & reports"],
      ]
    : [
        ["/#portal", zh ? "公司与研究门户" : "Company & research portal"],
        ["/#financials", zh ? "财务分析" : "Financial analysis"],
        ["/#reading", zh ? "报告与证据" : "Reports & evidence"],
      ];
  return (
    <header className="relative z-30 border-b border-[#d9d5bf] bg-[#edebe1]">
      <div className="mx-auto flex max-w-[1360px] flex-wrap items-center justify-between gap-x-4 gap-y-4 px-5 py-5 md:px-10 md:py-6">
        <Link
          href="/"
          aria-label={zh ? "TradeAgent 首页" : "TradeAgent home"}
          className="flex items-center gap-2.5 text-[22px] font-semibold tracking-[-.7px] no-underline md:text-[25px]"
        >
          <span
            aria-hidden="true"
            className="grid h-8 w-8 place-items-center rounded-lg bg-[#fdcc6a] text-lg"
          >
            T
          </span>
          TradeAgent
        </Link>
        <nav
          aria-label={zh ? "主导航" : "Main navigation"}
          className="order-3 flex w-full items-center gap-6 text-sm lg:order-0 lg:w-auto"
        >
          <details ref={menu} className="group relative">
            <summary className="cursor-pointer list-none py-2 font-medium">
              {application
                ? zh
                  ? "工作空间"
                  : "Workspace"
                : zh
                  ? "产品功能"
                  : "Features"}
              <span
                aria-hidden="true"
                className="ml-2 inline-block transition-transform group-open:rotate-180"
              >
                ⌄
              </span>
            </summary>
            <div className="absolute left-0 top-full z-40 w-60 rounded-xl border border-[#d9d5bf] bg-[#fffdf8] p-2 shadow-xl">
              {features.map(([href, label]) => (
                <Link
                  key={href}
                  href={href}
                  className="block rounded-lg px-4 py-3 hover:bg-[#edebe1]"
                  onClick={(event) =>
                    event.currentTarget
                      .closest("details")
                      ?.removeAttribute("open")
                  }
                >
                  {label}
                </Link>
              ))}
            </div>
          </details>
          <Link href={application ? "/app/research" : "/#workflow"}>
            {zh
              ? application
                ? "研究任务"
                : "研究流程"
              : application
                ? "Research tasks"
                : "Workflow"}
          </Link>
          <Link href={application ? "/app#data-scope" : "/#data"}>{zh ? "数据说明" : "Data & sources"}</Link>
        </nav>
        <div className="flex items-center gap-3 text-sm md:gap-5">
          <LanguageSwitcher appearance="account" />
          {!application && (
            <Link href="/login" className="hidden sm:inline">
              {zh ? "登录" : "Sign in"}
            </Link>
          )}
          <Link
            href="/app"
            className="rounded-md bg-[#191816] px-3 py-2.5 font-medium text-[#fffdf8] hover:bg-[#353128] md:px-5"
          >
            {zh
              ? application
                ? "我的门户"
                : "开始研究"
              : application
                ? "My portal"
                : "Start researching"}
          </Link>
        </div>
      </div>
    </header>
  );
}
