export const accountPageTitles: Record<string, string> = {
  "/": "TradeAgent — Evidence-led research",
  "/app/companies/detail": "Company research | TradeAgent",
  "/references/simply-wall-st": "Simply Wall St — Local reference preview",
  "/app/research": "My research | TradeAgent",
  "/app/research/detail": "Research progress | TradeAgent",
  "/login": "TradeAgent — Sign in",
  "/register": "TradeAgent — Create account",
  "/app": "TradeAgent — Workspace",
  "/labs/r1-company-data-status": "Company source component preview | TradeAgent",
  "/labs/function-integration": "Functional integration preview | TradeAgent",
};

export function accountPageTitle(path: string): string | undefined {
  return accountPageTitles[path.startsWith("/app/research/") ? "/app/research/detail" : path.startsWith("/app/companies/") ? "/app/companies/detail" : path];
}
