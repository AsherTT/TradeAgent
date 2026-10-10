import { fiscalJakarta } from "@/components/sites/fiscal-ai-7ee12bc9/shared/fonts";
import { accountMetadata } from "@/lib/account-api";
import { FiscalSearchPreview } from "./FiscalSearchPreview";

export async function generateMetadata() {
  return accountMetadata("/labs/r1-fiscal-search");
}

export default function FiscalSearchPreviewPage() {
  return (
    <main className={`${fiscalJakarta.variable} min-h-screen bg-[#151515] py-8 text-white`}>
      <FiscalSearchPreview />
    </main>
  );
}
