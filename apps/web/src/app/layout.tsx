import type { Metadata } from "next";
import localFont from "next/font/local";
import { cookies } from "next/headers";
import { LanguageProvider } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { languageTag, localeCookie, resolveLocale } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/messages";
import {
  sourceBureauSans,
  sourceBureauSerif,
  sourceInter,
} from "@/components/sites/simplywall-st-1b042a47/shared/fonts";
import "./globals.css";
import "@/components/sites/simplywall-st-1b042a47/shared/foundation.css";
import "@/components/sites/simplywall-st-1b042a47/shared/source-styles.css";
import "@/components/sites/simplywall-st-1b042a47/shared/captured-overrides.css";
import "@/components/sites/simplywall-st-1b042a47/shared/preview-interactions.css";
import "@/components/sites/simplywall-st-1b042a47/shared/i18n/locale.css";

const geistSans = localFont({
  src: "./fonts/GeistLatin.woff2",
  variable: "--font-geist-sans",
  weight: "100 900",
  style: "normal",
  display: "swap",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoLatin.woff2",
  variable: "--font-geist-mono",
  weight: "100 900",
  style: "normal",
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const locale = resolveLocale((await cookies()).get(localeCookie)?.value);
  return {
    title: locale === "zh" ? "TradeAgent — 用证据研究公司" : "TradeAgent — Evidence-led research",
    description: locale === "zh" ? "关注公司，发起有边界的研究，阅读报告与来源。" : "Follow companies, run bounded research and read reports with their sources.",
    icons: {
      icon: "/tradeagent.svg",
    },
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = resolveLocale((await cookies()).get(localeCookie)?.value);
  return (
    <html
      lang={languageTag(locale)}
      className={`${geistSans.variable} ${geistMono.variable} ${sourceBureauSans.variable} ${sourceBureauSerif.variable} ${sourceInter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <LanguageProvider initialLocale={locale}>{children}</LanguageProvider>
      </body>
    </html>
  );
}
