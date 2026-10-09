import { redirect } from "next/navigation";
import { accountMetadata, getAccount } from "@/lib/account-api";
import { ResearchRun } from "@/components/research/ResearchRun";

export async function generateMetadata() { return accountMetadata("/app/research/detail"); }
export default async function ResearchDetailPage({ params }: { params: Promise<{ runId: string }> }) {
  const identity = await getAccount();
  if (!identity.account && !identity.unavailable) redirect("/login");
  const { runId } = await params;
  return <ResearchRun key={runId} runId={runId} unavailable={identity.unavailable} />;
}
