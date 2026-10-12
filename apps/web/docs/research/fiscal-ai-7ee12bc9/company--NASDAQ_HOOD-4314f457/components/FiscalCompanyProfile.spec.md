# FiscalCompanyProfile Specification

## Overview
- Source https://fiscal.ai/company/NASDAQ_HOOD/, Company Overview card, 2026-10-12.
- Target `src/components/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/FiscalCompanyProfile.tsx` + scoped CSS.
- Screenshots `company-identity-{desktop,tablet,mobile}-source-20261012.png`; full measured trees `identity-overview-*-20261012.json.gz` and detailed state styles `overview-{expanded,focus,hover}-computed-20261012.json.gz`.
- Interaction model: click / native keyboard disclosure. No scroll-triggered state or animation. This is one Overview card, not the rest of the financial/company page.

## DOM Structure
Card → source wrapper divs → stack → h2, description spoiler, ul. Spoiler contains absolute button followed by clipping region div → div → p. ul → li → inline-flex column wrapper → span label → flex row(label p, right-aligned value p or a+SVG), divider. Props title, description, readonly fields `{label,value,href?}`; source reference and product pass their own truthful text. Disclosure uses unique ID + aria-controls/expanded, accessible name; localized control strings via existing LanguageProvider.

## Computed Styles (exact)
- Card relative flex column, padding16px, margin0 border0 radius8px, bg rgb(44,44,53), overflow hidden, shadow none; Jakarta400 16px/24.8px white. No fixed width/height.
- Source outer wrappers: transparent, margin/padding0; internal outer stack flex column gap32px (one child); inner stack flex column align stretch justify flex-start gap10px.
- h2: Jakarta600 16px/20px white margin/padding0.
- Spoiler root: relative block margin0 0 24px, padding0. Content flex column, overflow hidden, max-height60px collapsed, full measured content height expanded, transition max-height .2s. p Jakarta400 14px/20.3px rgb(175,175,182), margin/padding0.
- Button: absolute top100%,left0,height24px; block padding/margin/border0, radius0, transparent bg, white Jakarta400 16px/24.8px, pointer, appearance none, text-align center. Text Show more / Hide.
- ul block width100%, padding/margin0, list-style none, inherited16px/24.8px. li display list-item padding/margin0. Wrapper inline-flex column align flex-start width calc(100% - 20px). span width100%. This 20px subtraction is an observed stylesheet rule, not estimated indentation.
- Field row: flex row justify space-between width100%, padding1px 0, gap normal (no added gap); label/value p12px/18.6px white400 margin0, value text-align right. Wrapper inline-flex baseline is required: row20.6px + divider.8px makes wrapper21.4px; li line box25.2px; five-item list126px. Preserve wrappers, do not flatten to grid/dl.
- Divider block border-top.8px solid rgb(64,64,79), other borders0, height.8px. Source last divider also remains visible in captured states.
- Value link: flex row align center gap4px,12px/18.6px400 rgb(175,175,182), no decoration normally. External SVG12×12, viewBox0 0 24 24, fillnone stroke currentColor width2 roundcaps/joins, paths `M12 6h-6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6`, `M11 13l9-9`, `M15 4h5v5` (actual source icon).

## States & Behaviors
- Click, Enter and Space toggle collapsed/expanded. Default collapsed60px; expanded actual paragraph height, responsive to width. Button shown only when description exceeds60px. No arbitrary cap or always-visible useless button.
- Source captures: mobile expanded paragraph263.8875px; desktop expanded121.7875px. Card default desktop282px (652px width); expanded343.7875px. Actual heights must result from text/font/wrapping, never fixed constants.
- Actual pointer drag onto control without activation: :hover=true, text-decoration underline; no new bg/scale/color. Real keyboard Shift+Tab from website returns focus-visible to button: outline1.6px solid rgb(94,94,116), offset1.6px. Button default outline none. Value links use same hover/focus rules.
- Reduced-motion source has data-reduce-motion=true; respect prefers-reduced-motion for200ms transition.
- Pure CSS intrinsic-size interpolation may be used locally to animate60px→full content without inline styles. Scoped `interpolate-size:allow-keywords`, expanded max-height:max-content; preserve exact start/end geometry and200ms behavior, disclose implementation fallback on unsupported browsers. Verified platform design: https://developer.chrome.com/docs/css-ui/animate-to-height-auto . No global opt-in, no inline height styling.

## Assets
Existing --font-fiscal-jakarta only. No images/video/overlays/background assets in this selected card. Inline external-link SVG above is extracted source geometry.

## Text Content (verbatim reference)
Heading: Company Overview. Button: Show more / Hide.
Description: Robinhood Markets, Inc. is an American financial services company headquartered in Menlo Park, California. It operates a popular electronic trading platform that allows retail investors to trade stocks, exchange-traded funds (ETFs), options, and cryptocurrencies commission-free. The company is known for democratizing finance through its user-friendly mobile app and fractional share trading. In addition to its core brokerage services, Robinhood offers cash management, margin lending, and subscription-based premium features via Robinhood Gold.
Rows: Name | Robinhood Markets, Inc.; CEO | Vladimir Tenev; Website | robinhood.com (https://robinhood.com); Sector | Capital Markets; Year Founded | 2013.
Product SEC directory uses its own issuer fields/provenance/status, not source CEO/sector/prices. Source specimen is separate comparison route.

## Responsive Behavior
1440/768/390 same internal typography/padding/gaps. Source measured card widths652/717.6/348px; internal widths620/685.6/316px. Width is supplied by parent layout; do not hardcode measured widths. Native text wrapping; 60px clipping default and full expanded paragraph. Profile field value wraps for long product strings; local min-width0/overflow-wrap safety allowed and reported. Parent location/order and chart/sidebar are outside this component, must not be claimed as cloned.

## Validation
Builder named export, strict TS, scoped CSS/no inline styles, unique controls, preserve native anchors. Root owns screenshot and same-text geometry/style QA at all3sizes and toggle/hover/focus. Builder typechecks isolated worktree, Chinese commit only2files. No whole page completion claim.
