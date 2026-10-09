import "server-only";
import { accountPageTitle } from "./account-page-titles";
import { cookies } from "next/headers";
import type { Metadata } from "next";
import { localeCookie, resolveLocale, translate } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/messages";

export async function accountMetadata(path: string): Promise<Metadata> {
  const locale = resolveLocale((await cookies()).get(localeCookie)?.value);
  return { title: translate(locale, accountPageTitle(path) ?? "TradeAgent"), description: "TradeAgent", robots: { index: false, follow: false } };
}

export interface Account {
  user_id: string;
  email: string;
  created_at: string;
}

export function backendUrl(path: string): URL {
  const base = process.env.TRADEAGENT_API_URL ?? "http://127.0.0.1:8000";
  return new URL(path, base);
}

export async function getAccount(): Promise<{ account: Account | null; unavailable: boolean }> {
  const token = (await cookies()).get("tradeagent_session")?.value;
  if (!token) return { account: null, unavailable: false };
  try {
    const response = await fetch(backendUrl("/auth/me"), {
      headers: { Cookie: `tradeagent_session=${token}` },
      cache: "no-store", signal: AbortSignal.timeout(8000),
    });
    if (response.status === 401) return { account: null, unavailable: false };
    if (!response.ok) return { account: null, unavailable: true };
    return { account: await response.json() as Account, unavailable: false };
  } catch {
    return { account: null, unavailable: true };
  }
}
