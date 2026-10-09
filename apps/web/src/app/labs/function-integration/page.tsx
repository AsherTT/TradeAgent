import { ProductHome } from "@/components/product/ProductHome";
import { accountMetadata } from "@/lib/account-api";
import { IntegrationNotice } from "./IntegrationNotice";

export async function generateMetadata() { return accountMetadata("/labs/function-integration"); }

export default function FunctionIntegrationPage() {
  return <>
    <IntegrationNotice />
    <ProductHome />
  </>;
}
