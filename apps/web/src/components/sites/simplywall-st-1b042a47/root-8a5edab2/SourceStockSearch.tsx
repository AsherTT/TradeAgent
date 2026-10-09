import { LocalizedText } from "../shared/i18n/LanguageProvider";
export function SourceStockSearch() {
  return (
    <div className="search-embed w-embed source-search-preview">
      <a href="https://simplywall.st/search" className="source-search-link">
        <SolidSearchIcon />
        <span><LocalizedText en={"Research 120k Stocks"} /></span>
      </a>
    </div>
  );
}
import { SolidSearchIcon } from "../shared/icons";
