/* eslint-disable @next/next/no-img-element -- Keep original media dimensions and DOM in both locales. */
"use client";

import { accountPageTitle } from "@/lib/account-page-titles";
import { usePathname } from "next/navigation";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ComponentProps,
  type ReactNode,
} from "react";
import { languageTag, localeCookie, previewTitle, translate, type Locale } from "./messages";

interface LanguageContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (english: string) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ initialLocale, children }: {
  initialLocale: Locale;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const [locale, updateLocale] = useState(initialLocale);
  const setLocale = useCallback((nextLocale: Locale) => {
    updateLocale(nextLocale);
    document.cookie = `${localeCookie}=${nextLocale}; Path=/; Max-Age=31536000; SameSite=Lax`;
  }, []);
  const t = useCallback((english: string) => translate(locale, english), [locale]);
  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  useEffect(() => {
    document.documentElement.lang = languageTag(locale);
    document.title = translate(locale, accountPageTitle(pathname) ?? previewTitle);
  }, [locale, pathname]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("Page localization requires LanguageProvider.");
  return context;
}

export function LocalizedText({ en }: { en: string }) {
  const { t } = useLanguage();
  return t(en);
}

export function LocalizedImage({ alt = "", ...props }: ComponentProps<"img">) {
  const { t } = useLanguage();
  return <img {...props} alt={t(alt)} />;
}

export function LanguageSwitcher({ appearance = "source" }: { appearance?: "source" | "account" }) {
  const { locale, setLocale, t } = useLanguage();
  return (
    <div className={appearance === "account" ? "flex flex-none items-center gap-[2px] rounded-md border border-[#986e2e] p-[2px] [&_button]:min-w-[30px] [&_button]:cursor-pointer [&_button]:rounded-[3px] [&_button]:px-1 [&_button]:py-[5px] [&_button]:text-xs [&_button]:leading-5 [&_button[aria-pressed=true]]:bg-[#fdcc6a]" : "language-switcher"} role="group" aria-label={t("Language")}>
      <button type="button" lang="zh-CN" aria-label="中文" aria-pressed={locale === "zh"} onClick={() => setLocale("zh")}>
        中文
      </button>
      <button type="button" lang="en" aria-label="English" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>
        EN
      </button>
    </div>
  );
}
