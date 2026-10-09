import localFont from "next/font/local";

export const fiscalJakarta = localFont({
  src: [
    { path: "../../../../../public/sites/fiscal-ai-7ee12bc9/shared/fonts/43adbc7c773e.ttf", weight: "400", style: "normal" },
    { path: "../../../../../public/sites/fiscal-ai-7ee12bc9/shared/fonts/f2374e6da2f0.ttf", weight: "500", style: "normal" },
    { path: "../../../../../public/sites/fiscal-ai-7ee12bc9/shared/fonts/0ee86126fb55.ttf", weight: "600", style: "normal" },
  ],
  variable: "--font-fiscal-jakarta",
  display: "swap",
  adjustFontFallback: false,
});

export const fiscalMono = localFont({
  src: [
    { path: "../../../../../public/sites/fiscal-ai-7ee12bc9/shared/fonts/38f8abefb8f8.ttf", weight: "400", style: "normal" },
    { path: "../../../../../public/sites/fiscal-ai-7ee12bc9/shared/fonts/4da63a1b968e.ttf", weight: "500", style: "normal" },
  ],
  variable: "--font-fiscal-mono",
  display: "swap",
  adjustFontFallback: false,
});

export const fiscalGrotesk = localFont({
  src: "../../../../../public/sites/fiscal-ai-7ee12bc9/shared/fonts/56632cca6632.ttf",
  weight: "500",
  style: "normal",
  variable: "--font-fiscal-grotesk",
  display: "swap",
  adjustFontFallback: false,
});
