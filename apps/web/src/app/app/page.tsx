import { redirect } from "next/navigation";
import { Workspace } from "@/components/accounts/Workspace";
import { accountMetadata, getAccount } from "@/lib/account-api";

export async function generateMetadata() { return accountMetadata("/app"); }

export default async function WorkspacePage() {
  const identity = await getAccount();
  if (!identity.account && !identity.unavailable) redirect("/login");
  return <Workspace key={identity.account?.user_id ?? "unavailable"} account={identity.account} unavailable={identity.unavailable} />;
}
