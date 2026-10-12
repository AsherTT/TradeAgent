"use client";
import type { ReactNode } from "react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { ProductHeader } from "@/components/product/ProductHeader";
import { useWorkbenchLayout } from "@/components/workspace/WorkbenchLayoutContext";
import { accountCopy } from "./copy";

export function AccountShell({ children }: { children: ReactNode }) {
  const { locale } = useLanguage();
  const copy = accountCopy(locale);
  const sharedLayout = useWorkbenchLayout();
  return <div className={`${sharedLayout ? "min-h-[calc(100dvh-64px)]" : "min-h-screen"} bg-[#edebe1] text-sm leading-5 text-[#191816] [font-family:var(--font-geist-sans),'Microsoft_YaHei',sans-serif] [&_input:focus-visible]:outline-2 [&_button:focus-visible]:outline-2 [&_a:focus-visible]:outline-2 [&_:focus-visible]:outline-[#986e2e] [&_:focus-visible]:outline-offset-3`}>
    {!sharedLayout && <ProductHeader application />}
    <main className="mx-auto max-w-[1120px] px-4 pt-8 pb-12 md:px-6 md:pt-14 md:pb-20">{children}</main>
    <footer className="p-6 text-center text-xs text-[#625f58]">{copy.footer}</footer>
  </div>;
}
