# SearchEmptyMessage Specification

## Overview
- Source: https://fiscal.ai/company/NASDAQ_HOOD/; v6.0.2, 2026-10-10.
- Target: `src/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchEmptyMessage.tsx` and same-name CSS Module.
- Screenshots in `docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/`: `source-{desktop,tablet,mobile}-search-empty-message-20261010.png`.
- Interaction model: static paragraph within the search result scroll area.
- Scope: the paragraph only; parent scroll viewport, table wrapper, zero-height result containers, search state, tabs and navigation remain outside this component.

## DOM Structure
- One `p` containing exactly `No results found...`.
- Named-export server component; no props or client state at this reference stage.
- No button/link/tabindex/role or additional focus target.
- Do not copy the parent's three empty result containers into the paragraph component.
- Parent assembly supplies the local Jakarta font variable and available width.
- No route, global CSS, backend or account changes.

## Computed Styles (exact source values)
- Evidence: `v602-{desktop,tablet,mobile}-search-empty-message-20261010.json`, all enumerated CSS plus explicit computed longhand/shorthand properties for paragraph and its surrounding subtree.
- display: block; box-sizing: border-box; position: static.
- font-family: Plus Jakarta Sans, sans-serif; local equivalent `var(--font-fiscal-jakarta), sans-serif`.
- font-size: 16px; font-weight: 400; line-height: 24.8px; letter-spacing: normal.
- color: rgb(255,255,255); text-align: start; white-space: normal.
- padding: 16px on all four sides; margin: 0px on all four sides.
- border: 0px none; border-radius: 0px; background-color: transparent; background-image: none.
- width: available parent width; height: content-based (56.8px for observed single line). No fixed width/height.
- min-width: 0px; min-height: 0px; max-width/max-height: none.
- overflow: visible; opacity: 1; cursor: auto; box-shadow: none; transform: none.
- text-decoration: none; text-transform: none.
- transition-property: all; duration/delay: 0s; timing: ease. animation-name: none, duration: 0s. No animation logic.
- Use CSS Module for exact source measurements, consistent with existing Fiscal components.

## States & Behaviors
- Only the static empty-result message is in scope. Parent decides when it renders.
- Desktop pointer/click evidence: `v602-desktop-search-empty-message-pointer-20261010.json`.
- Exact text clicked; paragraph reports hover=true while all recorded computed properties and rectangle remain equal to before; active element remains `main-search-bar-modal`.
- No navigation, independent keyboard action, scroll behavior or content transition.
- No invented interactivity, live region or loading state.

## Per-State Content
- One state, no-result message; query used: `zzzznonexistentcompany987654`.
- Successful-result, loading and failure states belong to unfinished parent/search specs.

## Assets
- Existing local Jakarta 400 font in `shared/fonts.ts`; inherited parent variable.
- No SVG, image, video, canvas or layered media in this subtree. No download required.

## Text Content (verbatim)
No results found...
- Preserve three ASCII dots; translation will be a recorded product adaptation when the parent is ready.

## Responsive Behavior
- Desktop 1440×1000: paragraph width 966px, height 56.8px.
- Tablet 768×1000: width 657.2px, height 56.8px.
- Mobile 390×1000: width 317.375px, height 56.8px.
- Identical typography, padding and margins; no component breakpoint, content wraps naturally when needed.
- Tablet/mobile observations come from resizing the already-open desktop dialog, not freshly opening a dialog at each size. This component spec does not assert complete responsive dialog behavior. Prior fresh-open tablet evidence remains separate.

## Validation / dispatch gate
- Complete paragraph CSS/content, screenshots, pointer before/after and three widths captured.
- Read applicable AGENTS.md and Next bundled server component guide before implementing.
- Run `npx tsc --noEmit`; parent runs production build after merge.
- Parent compares actual rendered component geometry/typography at all three recorded parent widths. Component validation does not complete search, source pathname or /app.
