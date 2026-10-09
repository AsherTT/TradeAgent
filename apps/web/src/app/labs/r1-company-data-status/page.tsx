import "./preview.css";

import { sourceBureauSans, sourceBureauSerif } from "@/components/sites/simplywall-st-1b042a47/shared/fonts";
import { accountMetadata } from "@/lib/account-api";
import { CompanySourcePreview } from "./CompanySourcePreview";

export async function generateMetadata() {
  return accountMetadata("/labs/r1-company-data-status");
}

export default function CompanyDataStatusPreviewPage() {
  return (
    <main className={`${sourceBureauSans.variable} ${sourceBureauSerif.variable} sws-company-preview min-h-screen bg-[#151515] py-8 text-white`}>
      <CompanySourcePreview />
    </main>
  );
}
