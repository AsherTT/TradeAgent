import type { Metadata } from "next";
import Link from "next/link";
import { FullSourceHome } from "@/components/sites/simplywall-st-1b042a47/product-a/FullSourceHome";

export const metadata: Metadata = { robots: { index: false, follow: false } };

export default function Home() {
  return (
    <FullSourceHome brand="tradeagent" notice={<>完整来源复刻预览 / Full reference preview · Simply Wall St · 原站媒体、评价、功能及外链为参考材料 / Original media, reviews, features and links are reference material. <Link href="/app" className="underline">自有工作台 / TradeAgent workspace</Link></>} />
  );
}
