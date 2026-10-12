import { notFound, redirect } from "next/navigation";
import { fiscalJakarta, fiscalMono } from "@/components/sites/fiscal-ai-7ee12bc9/shared/fonts";
import { CompanyDirectoryDetail } from "@/components/workspace/CompanyDirectoryDetail";
import { accountMetadata, getAccount } from "@/lib/account-api";

export async function generateMetadata() { return accountMetadata("/app/companies/discovery"); }

export default async function DirectoryCompanyPage({ params, searchParams }: {
  params: Promise<{ cik: string }>;
  searchParams: Promise<{ symbol?: string | string[]; exchange?: string | string[] }>;
}) {
  const identity = await getAccount();
  if (!identity.account && !identity.unavailable) redirect("/login");
  const { cik } = await params;
  const { symbol, exchange = "" } = await searchParams;
  if (!/^[0-9]{1,10}$/.test(cik) || typeof symbol !== "string" || !symbol || symbol.length > 32
    || typeof exchange !== "string" || exchange.length > 32) notFound();
  return <main className={`${fiscalJakarta.variable} ${fiscalMono.variable} min-h-screen bg-[#1c1c21] text-white`}>
    <CompanyDirectoryDetail key={`${identity.account?.user_id}:${cik}:${symbol}:${exchange}`} cik={cik} symbol={symbol} exchange={exchange} />
  </main>;
}
