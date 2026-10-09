import { notFound, redirect } from "next/navigation";
import { CompanyWorkspace } from "@/components/workspace/CompanyWorkspace";
import { validResearchId } from "@/components/research/contracts";
import { accountMetadata, getAccount } from "@/lib/account-api";

export async function generateMetadata() { return accountMetadata("/app/companies/detail"); }

export default async function CompanyPage({ params }: { params: Promise<{ instrumentId: string }> }) {
  const identity = await getAccount();
  if (!identity.account && !identity.unavailable) redirect("/login");
  const { instrumentId } = await params;
  if (!validResearchId(instrumentId)) notFound();
  return <CompanyWorkspace key={`${identity.account?.user_id}:${instrumentId}`} instrumentId={instrumentId} />;
}
