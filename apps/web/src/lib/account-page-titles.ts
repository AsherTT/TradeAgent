export const accountPageTitles: Record<string, string> = {
  "/": "TradeAgent — Evidence-led research",
  "/app/companies/detail": "Company research | TradeAgent",
  "/app/companies/discovery": "Company directory details | TradeAgent",
  "/app/company-search": "Company directory search | TradeAgent",
  "/references/simply-wall-st": "Simply Wall St — Local reference preview",
  "/app/research": "My research | TradeAgent",
  "/app/research/detail": "Research progress | TradeAgent",
  "/login": "TradeAgent — Sign in",
  "/register": "TradeAgent — Create account",
  "/app": "TradeAgent — Workspace",
  "/labs/r1-company-data-status": "Company source component preview | TradeAgent",
  "/labs/r1-fiscal-search": "Fiscal search component preview | TradeAgent",
  "/labs/r1-fiscal-company-identity": "Fiscal company identity comparison | TradeAgent",
  "/labs/function-integration": "Functional integration preview | TradeAgent",
};

export function accountPageTitle(path: string): string | undefined {
  if (Object.hasOwn(accountPageTitles, path)) return accountPageTitles[path];
  return accountPageTitles[path.startsWith("/app/research/") ? "/app/research/detail" : path.startsWith("/app/companies/discovery/") ? "/app/companies/discovery" : path.startsWith("/app/companies/") ? "/app/companies/detail" : path];
}
