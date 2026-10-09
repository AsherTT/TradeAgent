"use client";

import Link from "next/link";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";

export function IntegrationNotice() {
  const { t } = useLanguage();
  return (
    <aside className="bg-[#262e3a] px-5 py-3 text-center text-sm text-white">
      {t("Functional integration preview, design unapproved.")}{" "}
      <Link href="/" className="underline">{t("Home")}</Link>
    </aside>
  );
}
