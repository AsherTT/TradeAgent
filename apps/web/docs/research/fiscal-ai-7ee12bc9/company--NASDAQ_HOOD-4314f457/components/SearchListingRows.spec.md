# SearchListingRows Specification

2026-10-12 / FE-02 / R1 incremental component, not whole search completion.

## Overview
- Source: https://fiscal.ai/company/NASDAQ_HOOD/ → search → Apple → 36 Listings.
- Target: src/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/SearchListingRows.tsx and .module.css.
- Screenshots: docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/listings-source-{desktop,tablet,mobile}-open-20261012.png.
- Evidence: listings-apple-{desktop,tablet,mobile}-query-open-20261012.json; listings-mobile-exact-css-20261012.json; listings-expanded-data-20261012.json. Raw computed-property enumeration omits shorthand values; explicit-property evidence supplies padding/gap/line-height.
- Interaction model: click-driven rows; enclosing company controls expansion. Component does not own query, category, expansion or navigation.

## DOM Structure
- Stack of alternate-listing anchors, followed by source separator.
- Anchor: left section span → flag frame div → actual flag img; body div → label span → market paragraph; empty description span is geometrically zero.
- Props: readonly SearchListing[]; onSelect(listing, MouseEvent<HTMLAnchorElement>); idPrefix for row IDs. Named export; use existing SearchListing type.
- Each anchor preserves source href as https://fiscal.ai + listing.href. Parent handles bounded local preview selection. No fetched/guessed listings in this component.

## Exact Computed Styles
- Stack: flex column; align-items stretch; justify-content flex-start; gap 2px; padding/margin 0; full available width. Observed 36-row stack height 1160.8px, all three widths.
- Anchor: display flex; align-items center; position relative; box-sizing border-box; padding 5px 16px; margin/border 0; radius 4px; background transparent; cursor pointer; no text decoration; full width.
- Anchor font: source Plus Jakarta Sans via var(--font-fiscal-jakarta), sans-serif; 16px/24.8px, weight 400; white default. Its visible label is 14px/20.3px, weight 400, rgb(175,175,182).
- Anchor height: 30.3px; generated from padding + paragraph line box, not fixed height.
- Left section: flex; align-items/justify-content center; margin 0 12px 0 0; width/height 18px; transition transform .15s.
- Flag frame: flex center; position relative; border .8px solid transparent; radius 4px; width/height/min-width/min-height 18px; box-sizing border-box.
- Image: block; position absolute; width/height 16.4px; border-radius 9999px; source asset supplied by listing.flag. alt supplied by listing.flagAlt; do not replace flags with emoji.
- Body: display block; flex 1; overflow hidden; text-overflow ellipsis; label span inline 14px/21.7px. Market p display block; margin/padding 0; 14px/20.3px; white-space normal.
- Separator: source horizontal border rgb(64,64,79), .8px; no padding/margin. Parent stack separates header and child region by 10px. Separator appears only for an open region, after the rows.
- Existing source NavLink hover token rgb(64,64,79), keyboard-active rgb(28,28,33). Native focus-visible outline may use existing row focus token rgb(94,94,116); record as accessibility adaptation, do not change resting geometry.

## States & Behaviors
- Component exists only when parent expanded; empty listings renders nothing.
- Click any alternate listing passes exactly that listing and event once; parent can prevent navigation and confirm source selection.
- Native anchors retain keyboard Enter and focus behavior. No nested interactive controls.
- Parent disclosure and row selection must remain separate: expanding cannot choose a company or close search.
- Multiple companies can expand simultaneously; Apple remains expanded when query narrows to AAPL while that company remains mounted. Hidden/unmounted company expansion resets. Language switch keeps mounted state.
- Chevron belongs to parent control: 16x16; transform none closed → rotate(180deg) open; .2s cubic-bezier(.4,0,.2,1).
- No additional entrance animation observed; do not invent one.

## Content & Assets
- Verbatim Apple first rows: DB:APC (/company/XFRA_APC/), DB:APC8 (/company/XFRA_APC8/), DB:APC0 (/company/XFRA_APC0/), XTRA:APC (/company/XETR_APC/), LSE:0R2V (/company/XLON_0R2V/).
- Full row snapshots live in listings-expanded-data-20261012.json, including aliases that repeat a source pathname. Key by stable parent + row index/market, never href alone.
- Flag URLs were observed as /_next/image/?url=https%3A%2F%2Fcdn.fiscal.ai%2Fflags%2F{country}.svg&w=3840&q=75; integration supplies actual downloaded local SVG paths. Shared source Jakarta font already exists.
- English market codes are data, identical in Chinese. Do not translate exchange/ticker or infer ADR/share-class identity.

## Responsive Behavior
- 1440/768/390: same one-column child stack; flag remains visible even when parent company logo is hidden on mobile. Same 14px market text/30.3px row and 2px gap at all sampled widths.
- Width follows enclosing source search viewport; do not set a separate max-width or impose a guessed breakpoint.
- Parent source card/native scrollbar width differences are outside this leaf spec and must be compared during assembly.

## Validation
- Typecheck required before handoff. Use scoped CSS Module and named exports, strict TS/no any, no inline styles.
- Preserve existing routes, assets and source namespaces. Builder edits only the two target component files; foreman integrates parent/data and performs source/local three-width and interaction QA.
