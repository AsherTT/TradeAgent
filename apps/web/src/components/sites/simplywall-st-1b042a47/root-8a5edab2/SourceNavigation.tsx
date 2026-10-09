"use client";

import { LanguageSwitcher, LocalizedImage, LocalizedText, useLanguage } from "../shared/i18n/LanguageProvider";

import { useEffect, useState } from "react";
import { getSourceAsset } from "../shared/assets";
import { SourceStockSearch } from "./SourceStockSearch";
import { TradeAgentLogo } from "../shared/TradeAgentLogo";

export function SourceNavigation({ brand = "source" }: { brand?: "source" | "tradeagent" }) {
  const { t } = useLanguage();
  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setFeaturesOpen(false);
        setMenuOpen(false);
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);
  return (
      <section data-wf--navigation--variant={"base"} className={"navigation section-55"}>
        <div data-animation={"default"} data-collapse={"medium"} data-duration={"300"} data-easing={"ease"} data-easing2={"ease"} role={"banner"} className={"navbar w-nav"}>
          <a className={"brand w-nav-brand"} href={brand === "tradeagent" ? "/" : "https://simplywall.st/?r=0"}>
            {brand === "tradeagent" ? <TradeAgentLogo placement="header" /> : <LocalizedImage src={getSourceAsset("https://marketing.simplywall.st/assets/Simply-Wall-St-Logo-HD.svg")} width={"108"} alt={""} className={"logo-image"} />}
          </a>
          <nav data-nav-menu-open={menuOpen ? "" : undefined} role={"navigation"} className={"nav-menu w-nav-menu"}>
            <div className={"main-links"}>
              <div onMouseEnter={() => setFeaturesOpen(true)} onMouseLeave={() => setFeaturesOpen(false)} data-hover={"true"} data-delay={"0"} className={"dropdown-2 w-dropdown"}>
                <div aria-expanded={featuresOpen} className={"dropdown-toggle w-dropdown-toggle"} role={"button"} tabIndex={0} aria-haspopup={"menu"}>
                  <div className={"icon-3 w-icon-dropdown-toggle"}>

                  </div>
                  <div>
                    <LocalizedText en={"Features"} />
                  </div>
                </div>
                <nav className={`dropdown-content-wrapper w-dropdown-list${featuresOpen ? " w--open" : ""}`}>
                  <a href={"https://simplywall.st/features/portfolio"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Portfolio Tracker"} />
                  </a>
                  <a href={"https://simplywall.st/feature/dividend-tracker"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Dividend Tracker"} />
                  </a>
                  <a href={"https://simplywall.st/discover/investing-ideas"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Stock Investing Ideas"} />
                  </a>
                  <a href={"https://simplywall.st/features/stock-screener"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Stock Screener"} />
                  </a>
                  <a href={"https://simplywall.st/features/stock-watchlist"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Watchlists"} />
                  </a>
                  <a href={"https://simplywall.st/features/community-narratives"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Community Narratives"} />
                  </a>
                  <a href={"https://simplywall.st/features/ask-charlie"} className={"dropdown-link w-dropdown-link"}>
                    <LocalizedText en={"Charlie AI"} />
                  </a>
                </nav>
              </div>
              <a href={"https://simplywall.st/features/portfolio"} className={"top-nav-links dropdown-only w-nav-link"}>
                <LocalizedText en={"Portfolio Tracker & Analysis"} />
              </a>
              <a href={"https://simplywall.st/feature/dividend-tracker"} className={"top-nav-links dropdown-only w-nav-link"}>
                <LocalizedText en={"Dividend Tracker"} />
              </a>
              <a href={"https://simplywall.st/features/stock-screener"} className={"top-nav-links dropdown-only w-nav-link"}>
                <LocalizedText en={"Stock Screener"} />
              </a>
              <a href={"https://simplywall.st/features/community-narratives"} className={"top-nav-links dropdown-only w-nav-link"}>
                <LocalizedText en={"Community Narratives"} />
              </a>
              <a href={"https://simplywall.st/features/ask-charlie"} className={"top-nav-links dropdown-only w-nav-link"}>
                <LocalizedText en={"Charlie AI"} />
              </a>
              <a href={"https://simplywall.st/plans"} className={"top-nav-links w-nav-link"}>
                <LocalizedText en={"Plans"} />
              </a>
              <a href={"https://simplywall.st/about"} className={"top-nav-links w-nav-link"}>
                <LocalizedText en={"About"} />
              </a>
              <a href={"https://simplywall.st/advertising"} className={"top-nav-links w-nav-link"}>
                <LocalizedText en={"Advertising"} />
              </a>
            </div>
            <div className={"search"}>
              <SourceStockSearch />
            </div>
            <div className={"authentication"}>
              <LanguageSwitcher />
              <a data-id={"create-account-link"} href={"/register"} className={"button in-nav w-button nav-cta--guest"}>
                <LocalizedText en={"Create a TradeAgent account"} />
              </a>
              <a data-id={"log-in-link"} href={"/login"} className={"button login in-nav w-button nav-cta--guest"}>
                <LocalizedText en={"Log in"} />
              </a>
              <a data-id={"dashboard-link"} href={"/app"} className={"button login in-nav w-button nav-cta--auth"}>
                <LocalizedText en={"Dashboard"} />
              </a>
            </div>
          </nav>
          <a href={"https://simplywall.st/plans"} className={"top-nav-links link-only-on-mobile w-nav-link"}>
            <LocalizedText en={"Plans"} />
          </a>
          <a href={"/login"} data-id={"log-in-link"} className={"platform-button-mobile w-nav-link nav-cta--guest"}>
            <LocalizedText en={"Log in"} />
          </a>
          <a href={"/app"} data-id={"dashboard-link"} className={"platform-button-mobile w-nav-link nav-cta--auth"}>
            <LocalizedText en={"Dashboard"} />
          </a>
          <div className={`menu-button w-nav-button${menuOpen ? " w--open" : ""}`} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setMenuOpen(!menuOpen); } }} role={"button"} tabIndex={0} aria-label={t("menu")} aria-haspopup={"menu"}>
            <div className={"w-icon-nav-menu"}>

            </div>
          </div>
        </div>
      </section>
  );
}
