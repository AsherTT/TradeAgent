# SearchGuidance Specification

## Overview
- Target file: `src/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchGuidance.tsx`
- Screenshots: `docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/source-v602-desktop-search-no-results.jpg` and `source-v602-mobile-search-no-results.jpg` in the same directory.
- Source: https://fiscal.ai/company/NASDAQ_HOOD/; v6.0.2, 2026-10-10.
- Interaction model: static text inside the search dialog, outside its result scroll area.
- Scope: only the bottom guidance and separator. Dialog visibility, position, widths, result lists and keyboard selection belong to their own unfinished specifications.

## DOM Structure
- `div` contains one `p` with three inline `span` examples interspersed with text.
- No link, button, image, SVG, video, canvas or layered assets within this subtree.
- Use a server component, named export, no props or client state; CSS Module for exact source values.
- Parent assembly will provide the local Jakarta font variable and dialog width. Do not create a route or modify an existing route.

## Computed Styles (exact values from getComputedStyle)
- Evidence: `v602-desktop-search-tip.json.gz`, `v602-tablet-search-tip.json.gz`, `v602-mobile-search-tip.json.gz` contain every enumerated computed CSS property for all five elements.

### Container
- display: block; position: static; box-sizing: border-box; flex-shrink: 0; flex-grow: 0.
- padding: 10px 16px; margin: 0; background-color: rgba(0,0,0,0).
- border-top-width: 0.8px; border-top-style: solid; border-top-color: rgb(175,175,182); other border widths: 0px; border radii: 0px.
- width: parent available width; max-width: none; height determined by text wrapping.
- Font: local Plus Jakarta Sans, sans-serif; inherited 16px/24.8px, weight 400; color rgb(255,255,255).
- overflow: visible; transform: none; box-shadow: none; opacity: 1; cursor: auto.

### Paragraph
- display: block; margin: 0; padding: 0; border widths: 0; background transparent.
- font-family: local Plus Jakarta Sans, sans-serif; font-size: 12px; font-weight: 400; line-height: 16.8px.
- color: rgb(175,175,182); text-align: center; white-space: normal; letter-spacing: normal.
- text-transform: none; text-decoration: none; opacity: 1; overflow: visible.

### Three inline examples
- display: inline; font-family and 12px/16.8px inherited; font-weight: 600.
- color: rgb(154,148,137); text-align: center; margin and padding: 0; border widths: 0.
- white-space: normal; text-decoration: none; background transparent; cursor: auto.

## States & Behaviors
- Static within parent; no independent scroll/click/time/keyboard state.
- Click on the exact `"MSFT pages"` span places the pointer on the text; URL and dialog state remain unchanged.
- Pointer before/after: all computed properties and rectangles for container, paragraph and spans are equal (`v602-mobile-search-tip-pointer.json.gz`). This is a static span, not a hover trigger or link.
- Transition: all elements report property all, duration 0s, delay 0s, easing ease. No animation required.
- Do not introduce button semantics, focus targets, tab index or navigation into this text.

## Per-State Content
- Same complete text in empty query, HOOD query and no-results states; responsive wrapping alone changes height.

## Assets
- Font foundation: `src/components/sites/fiscal-ai-7ee12bc9/shared/fonts.ts`, Jakarta weights 400/600 already downloaded and configured.
- Font CSS: `var(--font-fiscal-jakarta), sans-serif`; parent supplies variables.
- Icons/images: N/A, none in the captured subtree.

## Text Content (verbatim)
Tip: Navigate directly to pages by typing "Tesla income statement", "Apple estimates", or "MSFT pages"
- Inline spans: `"Tesla income statement"`, `"Apple estimates"`, `"MSFT pages"` (quotes included).
- Preserve the comma and single spaces exactly; do not translate or add content at this reference stage.

## Responsive Behavior
- Desktop 1440×1000: parent width 966px; paragraph 934px wide, 16.8px high; container 37.6px high.
- Tablet 768×1000: parent width 657.2px; paragraph 625.2px wide, 16.8px high; container 37.6px high.
- Mobile 390×1000: parent width 317.375px; paragraph 285.375px wide, 50.4px high (three lines); container 71.2px high.
- No component breakpoint or layout switch: ordinary inline text wrapping inside parent width. Do not hard-code captured widths or heights.
- Same padding, fonts, colors and border at all three widths.

## Validation / dispatch gate
- Complete subtree content, CSS, source screenshots, pointer comparison and three widths captured.
- Run `npx tsc --noEmit` before finishing; parent runs production build after merging.
- No product data, route, authentication, backend or global CSS changes permitted in this builder task.
