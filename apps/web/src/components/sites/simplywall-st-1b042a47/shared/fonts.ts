import localFont from "next/font/local";

export const sourceInter = localFont({
  src: "../../../../../public/sites/simplywall-st-1b042a47/shared/fonts/InterLatin.woff2",
  variable: "--font-sws-inter",
  weight: "300 700",
  style: "normal",
  display: "swap",
  adjustFontFallback: false,
});

export const sourceBureauSans = localFont({
  src: "../../../../../public/sites/simplywall-st-1b042a47/shared/fonts/BureauSans.woff2",
  variable: "--font-sws-bureau-sans",
  weight: "100 900",
  style: "normal",
  display: "swap",
  adjustFontFallback: false,
});

export const sourceBureauSerif = localFont({
  src: "../../../../../public/sites/simplywall-st-1b042a47/shared/fonts/BureauSerif.woff2",
  variable: "--font-sws-bureau-serif",
  weight: "500",
  style: "normal",
  display: "swap",
  adjustFontFallback: false,
});
