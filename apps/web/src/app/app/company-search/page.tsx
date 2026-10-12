import { redirect } from "next/navigation";
import { fiscalJakarta, fiscalMono } from "@/components/sites/fiscal-ai-7ee12bc9/shared/fonts";
import { CompanyDiscoverySearch } from "@/components/workspace/CompanyDiscoverySearch";
import { accountMetadata, getAccount } from "@/lib/account-api";

export async function generateMetadata() { return accountMetadata("/app/company-search"); }

export default async function CompanySearchPage() {
  const identity = await getAccount();
  if (!identity.account && !identity.unavailable) redirect("/login");
  return <main className={`${fiscalJakarta.variable} ${fiscalMono.variable} min-h-screen bg-[#151515] text-white`}>
    <CompanyDiscoverySearch key={identity.account?.user_id ?? "unavailable"} />
  </main>;
}
