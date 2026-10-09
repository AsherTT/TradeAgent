import { redirect } from "next/navigation";
import { AuthForm } from "@/components/accounts/AuthForm";
import { accountMetadata, getAccount } from "@/lib/account-api";

export async function generateMetadata() { return accountMetadata("/register"); }

export default async function RegisterPage() {
  if ((await getAccount()).account) redirect("/app");
  return <AuthForm mode="register" />;
}
