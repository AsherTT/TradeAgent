import chineseMessages from "./zh.json";

export type Locale = "zh" | "en";
export const localeCookie = "tradeagent-preview-locale";
export const previewTitle = "Simply Wall St — Local reference preview";
export const previewDescription = "Local source reproduction for the TradeAgent V2-B frontend design review.";
const translations: Readonly<Record<string, string>> = chineseMessages;

export function resolveLocale(value: string | undefined): Locale {
  return value === "en" ? "en" : "zh";
}

export function languageTag(locale: Locale): "zh-CN" | "en" {
  return locale === "zh" ? "zh-CN" : "en";
}

export function translate(locale: Locale, english: string): string {
  return locale === "zh" && Object.hasOwn(translations, english)
    ? translations[english]
    : english;
}
