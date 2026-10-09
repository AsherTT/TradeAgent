# Source foundation specification

Date: 2026-10-06, Asia/Shanghai. Scope: available-font wiring, scoped source tokens,
the source wrapper, and two measured inline SVGs. This is a partial foundation
milestone, not a completed clone or permission to dispatch page builders.

## Overview

- Source: https://simplywall.st/
- Target: `src/components/sites/simplywall-st-1b042a47/shared/`.
- Destination route remains `/`; the untouched scaffold is not replaced here.
- References: `computed-full-20261006-{1440,768,390}.json`,
  `svg-computed-20261006.json`, and `source-css/72584aff0dd8d4f5.css`.
- Screenshots: `source-{desktop-1440,tablet-768,mobile-390}-20261006.png`
  in the existing namespaced screenshot directory.
- Interaction model: static foundation; page interactions remain outside this milestone.

## DOM structure

`SourceFrame` renders one scoped `.sws-source` div around supplied children.
It does not assemble a page, inject captured HTML, copy tracking scripts, or alter
existing routes. Caller-owned layout remains caller-owned.
The root layout supplies the two local font CSS variables while retaining the
existing Geist and Geist Mono bootstrap variables.
The template theme must resolve its sans/mono stacks through those variables;
hard-coded upstream family names cannot address next/font/local generated faces.

## Computed styles and source declarations

- Body: background `rgb(237, 235, 225)`, text `rgb(25, 24, 22)`,
  `Inter, sans-serif`, 14px / 20px, margin 0, border-box descendants.
- Source CSS tokens: cream `#edebe1`, ink `#191816`, gold `#fdcc6a`,
  bronze `#986e2e`, tan `#d9b97a`, slate `#262e3a`, grey `#8c929b`.
- Source `.wrap`: max-width 1600px, margin `0 auto`, padding `0 40px`.
- BureauSans: normal, source font-face weight range 100–900, display swap.
- BureauSerif: normal, source font-face weight 500, display swap.
  Element weight 400 does not change the font-face declaration into a 400 face.
- Source `.serif`: `font-family: var(--serif)`, element font-weight 300.
  Preserve that element style separately from the 500 font-face declaration.
- Nav search SVG: 18px × 18px, viewBox `0 0 24 24`, fill none,
  stroke `rgb(152, 110, 46)`, stroke-width 2.2, round line cap.
  Circle `(10.5,10.5)` with radius 6.5; line `(15.4,15.4)` to `(21,21)`.
- Solid search SVG: 24px × 24px, block, fill `rgb(158, 115, 51)`.
  Preserve the extracted evenodd path verbatim. The fill differs from its
  inherited text color `rgb(26, 34, 46)`.
- Next font optimization may rename font families; expose them through the
  site-scoped variables rather than assuming their generated names.

## States and behaviors

Static wrappers and icons: N/A for hover/click transitions.
Source font-face display swap is retained. Runtime font asset serving must be
checked; a successful build is not font-loaded visual QA.
Do not implement navigation, research tabs, buttons, or loading states here.

## Assets

Use the previously exported real BureauSans/BureauSerif files under
`public/sites/simplywall-st-1b042a47/shared/fonts/`.
Their provenance is in `foundation-bundle.json` and `source-css/manifest.json`.
The source inline SVG markup is in `page-assets-20261006-current.json`.
Inter export failed through the asset-bundle interface; keep its literal source
font stack and explicitly leave self-hosting and fidelity qualification pending.
Source assets are for the isolated emulation lab; product-use rights remain pending.

## Text content

N/A: the foundation does not render source marketing copy or placeholder content.

## Responsive behavior

- 1440px / 768px: source wrap padding `0 40px`.
- 390px: source wrap padding `0 20px`.
- Actual source rule: `(max-width: 640px)`; preserve this measured rule rather
  than treating the three acceptance widths as breakpoints.

## Acceptance

Lint, strict typecheck and production build must pass. Existing root scaffold,
Geist startup fix, and all preserved research must remain intact.
Check both new local font resources return 200 in the running development server.
This milestone does not satisfy the full foundation/page pre-dispatch checklist:
Inter, remaining media, complete interactions and section specs are still needed.
