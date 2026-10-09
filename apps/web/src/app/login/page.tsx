import { redirect } from "next/navigation";
import { AuthForm } from "@/components/accounts/AuthForm";
import { accountMetadata, getAccount } from "@/lib/account-api";

export async function generateMetadata() { return accountMetadata("/login"); }

export default async function LoginPage() {
  if ((await getAccount()).account) redirect("/app");
  return <AuthForm mode="login" />;
}
