# SearchClearButton Specification

## Overview
- Source: https://fiscal.ai/company/NASDAQ_HOOD/, v6.0.2, 2026-10-10.
- Target: `src/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchClearButton.tsx` and same-name CSS Module.
- Screenshots in the same page-key screenshot namespace: `source-desktop-hood-pages-tab-20261010.jpg`, `source-tablet-clear-search-20261010.jpg`, `source-mobile-clear-search-20261010.jpg`.
- Interaction: native button, controlled by the unfinished search parent. Parent shows it in direct-page query mode and clears query when notified.
- Scope: this button and two spans only. No query storage, result list, routing, focus restoration, disabled/loading variant or independent state.

## DOM Structure and contract
- `button > span(inner) > span(label)`; label exactly `Clear Search`.
- Named-export client component; explicit `type="button"` avoids accidental form submit.
- Required prop `onClear: () => void`; pass to native onClick. No manual Enter/Space handlers, no duplicated activation callback, no DOM lookup, no local state.
- Normal native button keyboard focus. Do not add positive tabindex, autofocus or remove native semantics.
- Parent provides the local Jakarta font variable; parent controls conditional rendering, focus and query/results.
- No route/global CSS/backend edits; use same-site CSS Module for precise source style.

## Computed Styles (source values)
- `v602-clear-search-{desktop,tablet,mobile}-default-20261010.json` captures all enumerated computed properties plus explicit shorthands and complete DOM for all three nodes. All recorded styles equal across the three widths.

### Button
- inline-block; relative; box-sizing:border-box; width:100px; height:30px.
- min-width/min-height:0; max-width/max-height:none; margin:0; padding:0 10px.
- border:0.8px solid transparent; radius:24px; transparent background; no image/shadow.
- local Jakarta sans-serif, 12px/12px, weight600, normal letter spacing; color:rgb(175,175,182).
- text-align:center; text-transform/text-decoration:none; white-space:normal.
- overflow:hidden; opacity:1; cursor:pointer; transform:none; animation:none.
- transition:opacity 0.2s ease-in-out (delay0s).
- Default computed outline is none (rgb175/175/182,2.4px), offset0. No visible default ring.

### Inner span
- flex row; align-items:center; justify-content:center; height:100% of button content box (28.4px); available content width78.4px.
- box-sizing:border-box; position:static; margin/padding/border:0; radius0; background transparent.
- inherits 12px/12px weight600, color and font; cursor:pointer; white-space:normal; overflow:visible.
- opacity:1; transform:none; transition:transform 0.15s ease, opacity 0.1s ease (both delay0).

### Label span
- flex row; align-items:center; justify-content:normal; content height28.4px; measured text width73.5875px (do not hardcode).
- box-sizing:border-box; static; min-width/min-height:auto; no padding/margin/border/radius/background.
- inherits typography/color/cursor; white-space:nowrap; overflow:hidden.
- opacity1; transform:none; transition all 0s ease; no animation.

## States & Behaviors
- Default: above values; enabled, not hovered/focused.
- Hover: button opacity1→0.7; children computed opacity remains1. Transition is opacity0.2s ease-in-out.
- Keyboard focus-visible: outline1.6px solid rgb(94,94,116); offset1.6px. Without hover opacity1, with hover opacity0.7.
- Pressed `:active`: button translates down1px (source computed matrix(1,0,0,1,0,1)); other subtree properties unchanged apart from simultaneous hover/focus. Use CSS :active, no JS state.
- Evidence: desktop-hover, desktop-focus, desktop-focus-without-hover and desktop-pressed JSON in the same v602-clear-search namespace.
- Pointer release activates clear; mobile native Space also activates clear. Query becomes empty and button disappears; current source has one recent result plus30 defaults (31links).
- Current native mouse and Space sequence leaves BODY focused after removal, whereas earlier locator sequence kept input focus. Record both; this child must not impose focus restoration. Parent integration owns it.
- Callback is the only side effect. Do not clear source history or implement Clear All.
- Disabled/loading variants not observed and outside scope; no invented styles or props.

## Per-State Content
- Same `Clear Search` text in default/hover/focus/pressed states.
- Absence belongs to parent after clear or outside direct-page query mode.

## Assets
- Existing local Jakarta600 file and `shared/fonts.ts` variable; no icon/SVG/image/video/canvas/download.

## Text Content (verbatim)
Clear Search
- Source-stage English; later product translation belongs to parent adapter.

## Responsive Behavior
- 1440×1000,768×1000,390×1000: button100×30, inner78.4×28.4, text73.5875×28.4.
- No component breakpoint; parent position/layout changes. Tablet/mobile were resized while dialog remained open; no claim about fresh-open dialog layout.

## Validation / dispatch gate
- Default three sizes, pointer nonhover/hover, keyboard focus with/without hover, pressed and mouse/Space activation captured.
- Read AGENTS.md and relevant bundled Next client component/CSS docs; npx tsc --noEmit before commit.
- Parent runs check/build and actual hydrated browser mouse/Enter/Space callback validation, all measured state styles and three-size comparison.
- Keep complete search, Next parent layout and /app completion separate.
