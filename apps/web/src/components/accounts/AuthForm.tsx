"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { accountStyles } from "./styles";
import { AccountShell } from "./AccountShell";
import { accountCopy, accountError, readApiError } from "./copy";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { locale } = useLanguage();
  const copy = accountCopy(locale);
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const registering = mode === "register";
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    const data = new FormData(event.currentTarget);
    setPending(true); setError(null);
    try {
      const response = await fetch(`/api/backend/auth/${mode}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: data.get("email"), password: data.get("password") }),
      });
      if (!response.ok) { setError(await readApiError(response)); return; }
      router.replace("/app"); router.refresh();
    } catch { setError("backend_unavailable"); }
    finally { setPending(false); }
  }
  return <AccountShell><section className={`${accountStyles.card} mx-auto my-4 max-w-[460px]`}>
    <p className={accountStyles.eyebrow}>TradeAgent</p>
    <h1 className={accountStyles.heading}>{registering ? copy.join : copy.welcome}</h1>
    <p className={accountStyles.muted}>{registering ? copy.registration : copy.intro}</p>
    <form onSubmit={submit} className={"mt-7 flex flex-col gap-[10px] [&_label]:mt-2 [&_label]:text-sm [&_label]:font-medium"} aria-busy={pending}>
      <label htmlFor="email">{copy.email}</label>
      <input className={accountStyles.input} id="email" name="email" type="email" autoComplete="email" maxLength={254} required disabled={pending} />
      <label htmlFor="password">{copy.password}</label>
      <input className={accountStyles.input} id="password" name="password" type="password" autoComplete={registering ? "new-password" : "current-password"}
        minLength={registering ? 12 : 1} maxLength={128} aria-describedby={registering ? "password-hint" : undefined} required disabled={pending} />
      {registering && <small id="password-hint" className={accountStyles.muted}>{copy.passwordHint}</small>}
      {error && <p role="alert" className={accountStyles.error}>{accountError(locale, error)}</p>}
      <button className={`${accountStyles.button} mt-4 w-full`} disabled={pending}>{pending ? copy.pending : registering ? copy.register : copy.login}</button>
    </form>
    <p className={"mt-6 text-center text-sm [&_a]:ml-[6px] [&_a]:text-[#986e2e] [&_a]:underline"}>{registering ? copy.haveAccount : copy.noAccount} <Link href={registering ? "/login" : "/register"}>{registering ? copy.login : copy.register}</Link></p>
  </section></AccountShell>;
}
