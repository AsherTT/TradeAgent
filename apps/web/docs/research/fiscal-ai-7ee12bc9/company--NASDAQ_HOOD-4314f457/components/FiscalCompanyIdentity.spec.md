# FiscalCompanyIdentity Specification

## Overview
- Source: https://fiscal.ai/company/NASDAQ_HOOD/ (2026-10-12).
- Target: `src/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/FiscalCompanyIdentity.tsx` plus scoped CSS module.
- Screenshots: `docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/company-identity-{desktop,tablet,mobile}-source-20261012.png`.
- Interaction model: static identity sub-block. Quote, bookmark/notes and audio siblings are outside this selected component. Do not add inert imitations of them.
- Full measured trees: `identity-overview-{desktop,tablet,mobile}-20261012.json.gz`; first identity row's first two children are the scoped reference.

## DOM Structure
Source card → flex parent → identity row → logo div/span/img + name stack (h1 + market flex/p). Preserve these wrappers and source measurement geometry. Product props are name, exchangeSymbol (formatted e.g. NASDAQ-HOOD), optional local logoSrc. No routing or API inside this static component.

## Computed Styles (measured, not estimates)
- Card: position relative, display flex/column, width100%, padding0, margin0, border0, border-radius8px, bg rgb(44,44,53), box-shadow none, overflow visible, white text, Plus Jakarta Sans 400 16px/24.8px.
- Parent: flex row at >=1024px, column below, gap4px, padding0 8px, height100%. Only identity child in this selected subset.
- Identity row: flex row, align-items center, gap6px, padding8px 0, margin0, height100%; no border/background/radius/transform.
- Logo wrapper: div block; span block width/height/min-width/min-height46px, margin-right4px, radius6px, overflow hidden, z-index -1; img46×46, object-fit contain/object-position center, inline source display.
- Stack: display flex/column, gap4px, align-items stretch, justify-content center, margin-right auto, height100%.
- h1: Plus Jakarta Sans 600, 24px/31.92px, white, margin/padding0, normal letter spacing. min-width200px at >=768px; below640px 19.2px/22.4px. Preserve native wrapping.
- Market flex: flex row, align-items center, flex-wrap wrap, gap6px. p:14px/20.3px 400 white, margin/padding0.
- Default dimensions with Robinhood reference: identity row desktop/tablet height72.2125px; mobile62.7px. Logo46×46; h1 desktop/tablet281.525×31.9125; mobile225.225×22.4. Font measurement rounding is browser-produced; do not hardcode these text widths.

## States & Behaviors
No click/hover/focus state exists on the selected identity logo/name/market. Static; no transitions/scroll listeners. Source quote/action siblings stay out of scope. Product names may be longer; allow wrapping without replacing the font scale or clipping names.

## Assets
- Use shared `--font-fiscal-jakarta` already downloaded; no global typography edits.
- Reference logo: `/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/search-images-20261011/logo-HOOD.png`, observed and downloaded previously, confirmed source 46px company logo.
- Product logo missing: reserve same46px box; use plain ticker text supplied by adapter only if needed. Do not invent or request a source-site private logo API.
- No background image, overlays, videos, SVGs in selected block.

## Text Content (verbatim reference)
- Robinhood Markets, Inc.
- NASDAQ-HOOD
- image alt: Robinhood Markets, Inc. Website
Product values come from the actual SEC identity adapter; reference values stay in isolated comparison route.

## Responsive Behavior
- Desktop1440: row, title24px/31.92, minimum title width200, logo46px.
- Tablet768: same selected identity geometry; outer card's quote moves below in the source, but quote is outside this subset.
- Mobile390: title19.2/22.4, logo46px, natural wrapping; parent column. No fixed row heights or text widths.
- Observed utility breakpoints: 640px title;768px title min-width;1024px outer direction. Do not change existing namespace/source components or source page routes.

## Build and validation
Named export; strict TS; scoped CSS; no inline style. Builder runs `npx tsc --noEmit` in isolated worktree and commits only this component/CSS with Chinese message. Parent integration and three-size same-text geometry/styles + screenshot QA are owned by root after merge. This spec does not authorize claiming the full company page is cloned.
