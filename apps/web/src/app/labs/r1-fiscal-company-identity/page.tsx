import { fiscalJakarta, fiscalMono } from "@/components/sites/fiscal-ai-7ee12bc9/shared/fonts";
import { accountMetadata } from "@/lib/account-api";
import { IdentityReferencePreview } from "./IdentityReferencePreview";

export async function generateMetadata() { return accountMetadata("/labs/r1-fiscal-company-identity"); }

export default function FiscalIdentityReferencePage() {
  return <main className={`${fiscalJakarta.variable} ${fiscalMono.variable}`}><IdentityReferencePreview /></main>;
}
