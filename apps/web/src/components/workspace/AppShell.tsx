"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { FiscalAppHeader } from "@/components/sites/fiscal-ai-7ee12bc9/shared/FiscalAppHeader";
import { FiscalAppSidebar, type AppNavigationItem } from "@/components/sites/fiscal-ai-7ee12bc9/shared/FiscalAppSidebar";
import { LanguageSwitcher, useLanguage } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/LanguageProvider";
import { WorkbenchLayoutContext } from "./WorkbenchLayoutContext";
import styles from "./AppShell.module.css";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { locale } = useLanguage();
  const zh = locale === "zh";
  const [navigation, setNavigation] = useState({ pathname, open: false });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const searchRef = useRef<HTMLAnchorElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const open = navigation.pathname === pathname && navigation.open;
  // Persistent layouts must discard the previous route's drawer, including A → B → A.
  if (navigation.pathname !== pathname) {
    setNavigation({ pathname, open: false });
  }

  const searchLabel = zh ? "搜索公司" : "Search companies";
  const items: AppNavigationItem[] = [
    { id: "portal", href: "/app", label: zh ? "研究门户" : "Portal", icon: "dashboard", selected: pathname === "/app" },
    { id: "companies", href: "/app/company-search", label: zh ? "公司" : "Companies", icon: "query", selected: pathname === "/app/company-search" || pathname.startsWith("/app/companies/") },
    { id: "research", href: "/app/research", label: zh ? "研究" : "Research", icon: "analysis", selected: pathname === "/app/research" || pathname.startsWith("/app/research/") },
    { id: "account", href: "/app#account", label: zh ? "账户" : "Account", icon: "settings", selected: false },
  ];

  function closeNavigation(restore: boolean) {
    returnFocus.current = restore ? buttonRef.current : null;
    setNavigation({ pathname, open: false });
  }

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sidebarRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      returnFocus.current?.focus();
      returnFocus.current = null;
    };
  }, [open]);

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 1024px)");
    function handleDesktop(event: MediaQueryListEvent) {
      if (!event.matches) return;
      if (sidebarRef.current?.contains(document.activeElement)) returnFocus.current = searchRef.current;
      setNavigation({ pathname, open: false });
    }
    desktop.addEventListener("change", handleDesktop);
    return () => desktop.removeEventListener("change", handleDesktop);
  }, [pathname]);

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (open) {
        if (event.key === "Escape") {
          event.preventDefault();
          returnFocus.current = buttonRef.current;
          setNavigation({ pathname, open: false });
        } else if (event.key === "Tab") {
          const controls = Array.from(sidebarRef.current?.querySelectorAll<HTMLElement>("a[href], button:not(:disabled), input:not(:disabled), [tabindex='0']") ?? []);
          const first = controls[0];
          const last = controls.at(-1);
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault(); last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault(); first?.focus();
          }
        }
        return;
      }
      if (event.key !== "/" || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey || event.repeat || event.isComposing) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.matches("input, textarea, select") || target.isContentEditable || target.closest('[contenteditable]:not([contenteditable="false"])'))) return;
      if (document.querySelector('[role="dialog"][aria-modal="true"]')) return;
      event.preventDefault();
      router.push("/app/company-search");
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, pathname, router]);

  const languageControl = <div className={styles.language}><LanguageSwitcher appearance="account" /></div>;
  return <WorkbenchLayoutContext.Provider value={true}>
    <div className={styles.shell}>
      <div inert={open}>
        <a href="#workbench-content" className={styles.skip}>{zh ? "跳到正文" : "Skip to content"}</a>
        <FiscalAppHeader searchHref="/app/company-search" searchLabel={searchLabel} languageControl={languageControl}
          navigationLabel={zh ? "打开导航" : "Open navigation"} expanded={open}
          onOpenNavigation={() => setNavigation({ pathname, open: true })} buttonRef={buttonRef} searchRef={searchRef} />
      </div>
      <FiscalAppSidebar items={items} open={open} navigationLabel={zh ? "工作台导航" : "Workbench navigation"}
        closeLabel={zh ? "关闭导航" : "Close navigation"} searchLabel={searchLabel} searchHref="/app/company-search"
        onClose={() => closeNavigation(true)} onNavigate={() => closeNavigation(false)} sidebarRef={sidebarRef} languageControl={languageControl} />
      <div id="workbench-content" tabIndex={-1} inert={open} className={styles.content}>{children}</div>
    </div>
  </WorkbenchLayoutContext.Provider>;
}
