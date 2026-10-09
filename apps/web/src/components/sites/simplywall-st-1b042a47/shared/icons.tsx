import type { SVGProps } from "react";
import { cn } from "@/lib/utils";

export function NavSearchIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      aria-hidden="true"
      className={cn("sws-nav-search-icon", className)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      {...props}
    >
      <circle cx="10.5" cy="10.5" r="6.5" />
      <line x1="15.4" y1="15.4" x2="21" y2="21" />
    </svg>
  );
}

export function SolidSearchIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      aria-hidden="true"
      className={cn("sws-solid-search-icon", className)}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="currentColor"
      {...props}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15.1923 16.6063C14.0237 17.4816 12.5724 18 11 18C7.13401 18 4 14.866 4 11C4 7.13401 7.13401 4 11 4C14.866 4 18 7.13401 18 11C18 12.5723 17.4816 14.0235 16.6065 15.192L19.706 18.2916C20.0965 18.6821 20.0965 19.3153 19.706 19.7058C19.3155 20.0963 18.6823 20.0963 18.2918 19.7058L15.1923 16.6063ZM16 11C16 13.7614 13.7614 16 11 16C8.23858 16 6 13.7614 6 11C6 8.23858 8.23858 6 11 6C13.7614 6 16 8.23858 16 11Z"
      />
    </svg>
  );
}
