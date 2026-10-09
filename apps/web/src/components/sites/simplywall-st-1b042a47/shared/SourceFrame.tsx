import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function SourceFrame({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn("sws-source", className)}>{children}</div>;
}
