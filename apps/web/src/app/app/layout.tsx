import type { ReactNode } from "react";
import { fiscalJakarta, fiscalMono } from "@/components/sites/fiscal-ai-7ee12bc9/shared/fonts";
import { AppShell } from "@/components/workspace/AppShell";

export default function WorkbenchLayout({ children }: { children: ReactNode }) {
  return <div className={`${fiscalJakarta.variable} ${fiscalMono.variable}`}><AppShell>{children}</AppShell></div>;
}
