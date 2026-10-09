"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { NavSearchIcon } from "../shared/icons";
import { LanguageSwitcher, useLanguage } from "../shared/i18n/LanguageProvider";

const featureLinks = [
  { href: "/#portal", zh: "公司与研究门户", en: "Company & research portal" },
  { href: "/#financials", zh: "财务分析", en: "Financial analysis" },
  { href: "/#reading", zh: "报告与证据", en: "Reports & evidence" },
] as const;

const focusClass = "focus-visible:!outline-2 focus-visible:!outline-[#986e2e] focus-visible:!outline-offset-2";

export function EnhancedANavigation() {
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const navigationRef = useRef<HTMLElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const featuresId = useId();
  const menuId = useId();

  useEffect(() => {
    function closeOnOutside(event: PointerEvent) {
      if (event.target instanceof Node && !navigationRef.current?.contains(event.target)) {
        setFeaturesOpen(false);
        setMenuOpen(false);
      }
    }

    function closeOnEscape(event: globalThis.KeyboardEvent) {
      if (event.key !== "Escape" || (!featuresOpen && !menuOpen)) return;
      event.preventDefault();
      setFeaturesOpen(false);
      setMenuOpen(false);
      if (menuOpen) menuRef.current?.focus();
      else featuresRef.current?.focus();
    }

    document.addEventListener("pointerdown", closeOnOutside);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutside);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [featuresOpen, menuOpen]);

  function closeMenus() {
    setFeaturesOpen(false);
    setMenuOpen(false);
  }

  function toggleWithKeyboard(event: KeyboardEvent<HTMLDivElement>, toggle: () => void) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }
  }

  function openOnDesktopHover() {
    if (window.matchMedia("(min-width: 992px) and (hover: hover)").matches) {
      setFeaturesOpen(true);
    }
  }

  return (
    <section ref={navigationRef} data-wf--navigation--variant="base" className="navigation section-55">
      <div data-animation="default" data-collapse="medium" data-duration="300" data-easing="ease" data-easing2="ease" className="navbar w-nav">
        <Link href="/" className={`brand w-nav-brand ${focusClass}`} onClick={closeMenus} aria-label={zh ? "TradeAgent 首页" : "TradeAgent home"}>
          <span className="inline-flex w-[108px] flex-none items-center gap-1 font-[family-name:var(--font-sws-inter)] text-[15px] font-semibold leading-5 text-[#191816]">
            <span aria-hidden="true" className="inline-flex h-5 w-5 flex-none items-center justify-center rounded bg-[#fdcc6a] text-xs">T</span>
            <span>TradeAgent</span>
          </span>
        </Link>
        <nav id={menuId} data-nav-menu-open={menuOpen ? "" : undefined} aria-label={zh ? "主导航" : "Main navigation"} className="nav-menu w-nav-menu">
          <div className="main-links">
            <div onMouseEnter={openOnDesktopHover} onMouseLeave={() => setFeaturesOpen(false)} data-hover="true" data-delay="0" className="dropdown-2 w-dropdown">
              <div ref={featuresRef} aria-expanded={featuresOpen} aria-controls={featuresId} className={`dropdown-toggle w-dropdown-toggle ${focusClass}`} role="button" tabIndex={0} onClick={() => setFeaturesOpen((open) => !open)} onKeyDown={(event) => toggleWithKeyboard(event, () => setFeaturesOpen((open) => !open))}>
                <div aria-hidden="true" className="icon-3 w-icon-dropdown-toggle" />
                <div>{zh ? "产品功能" : "Features"}</div>
              </div>
              <nav id={featuresId} aria-label={zh ? "产品功能" : "Features"} className={`dropdown-content-wrapper w-dropdown-list${featuresOpen ? " w--open" : ""}`}>
                {featureLinks.map((link) => (
                  <Link key={link.href} href={link.href} className={`dropdown-link w-dropdown-link ${focusClass}`} onClick={closeMenus}>{zh ? link.zh : link.en}</Link>
                ))}
              </nav>
            </div>
            {featureLinks.map((link) => (
              <Link key={link.href} href={link.href} className={`top-nav-links dropdown-only w-nav-link ${focusClass}`} onClick={closeMenus}>{zh ? link.zh : link.en}</Link>
            ))}
            <Link href="/#workflow" className={`top-nav-links w-nav-link ${focusClass}`} onClick={closeMenus}>{zh ? "研究流程" : "Research workflow"}</Link>
            <Link href="/#data" className={`top-nav-links w-nav-link ${focusClass}`} onClick={closeMenus}>{zh ? "数据说明" : "Data sources"}</Link>
          </div>
          <div className="search">
            <div className="search-embed w-embed source-search-preview">
              <Link href="/app#companies" className={`source-search-link ${focusClass}`} onClick={closeMenus}>
                <NavSearchIcon />
                <span>{zh ? "登录后搜索公司" : "Sign in to search companies"}</span>
              </Link>
            </div>
          </div>
          <div className="authentication">
            <LanguageSwitcher />
            <Link href="/app" className={`button in-nav w-button ${focusClass}`} onClick={closeMenus}>{zh ? "开始研究" : "Start research"}</Link>
            <Link href="/login" className={`button login in-nav w-button ${focusClass}`} onClick={closeMenus}>{zh ? "登录" : "Log in"}</Link>
          </div>
        </nav>
        <Link href="/#workflow" className={`top-nav-links link-only-on-mobile w-nav-link ${focusClass}`} onClick={closeMenus}>{zh ? "研究流程" : "Research workflow"}</Link>
        <Link href="/login" className={`platform-button-mobile w-nav-link ${focusClass}`} onClick={closeMenus}>{zh ? "登录" : "Log in"}</Link>
        <div ref={menuRef} className={`menu-button w-nav-button${menuOpen ? " w--open" : ""} ${focusClass}`} aria-expanded={menuOpen} aria-controls={menuId} onClick={() => setMenuOpen((open) => !open)} onKeyDown={(event) => toggleWithKeyboard(event, () => setMenuOpen((open) => !open))} role="button" tabIndex={0} aria-label={zh ? "导航菜单" : "Navigation menu"}>
          <div aria-hidden="true" className="w-icon-nav-menu" />
        </div>
      </div>
    </section>
  );
}
