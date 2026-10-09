import { redirect } from "next/navigation";
import { accountMetadata, getAccount } from "@/lib/account-api";
import { ResearchWorkspace } from "@/components/research/ResearchWorkspace";
import { validResearchId } from "@/components/research/contracts";

export async function generateMetadata() { return accountMetadata("/app/research"); }
export default async function ResearchPage({ searchParams }: { searchParams: Promise<{ company?: string | string[] }> }) {
  const identity = await getAccount();
  if (!identity.account && !identity.unavailable) redirect("/login");
  const { company } = await searchParams;
  const initialCompany = typeof company === "string" && validResearchId(company) ? company : "";
  return <ResearchWorkspace key={`${identity.account?.user_id}:${initialCompany}`} initialCompany={initialCompany} unavailable={identity.unavailable} />;
}
