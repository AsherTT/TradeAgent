import { FullSourceHome } from "@/components/sites/simplywall-st-1b042a47/product-a/FullSourceHome";
import { cookies } from "next/headers";
import Link from "next/link";
import { localeCookie, previewDescription, previewTitle, resolveLocale, translate } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/messages";

export async function generateMetadata() {
  const locale = resolveLocale((await cookies()).get(localeCookie)?.value);
  return { title: translate(locale, previewTitle), description: translate(locale, previewDescription), robots: { index: false, follow: false }, icons: { icon: "/sites/simplywall-st-1b042a47/root-8a5edab2/media/8ab7ce228edc9ef6.png" } };
}

export default function Home() {
  return (
    <FullSourceHome notice={<>来源参考复刻 / Source reference · Simply Wall St · 这里保留原站产品链接，不是 TradeAgent 功能 / Original-site links are reference material. <Link href="/" className="underline">返回产品 / Back to product</Link></>} />
  );
}