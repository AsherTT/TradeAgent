# ResearchSection specification

Target: src/components/sites/simplywall-st-1b042a47/root-8a5edab2/ResearchSection.tsx

DOM, verbatim content, child media, and every computed style are recorded in
`computed-full-20261006-1440.json`, root index 5. This record is the exact specification; no estimated values.
Responsive child records: same root index in `computed-full-20261006-768.json` and `computed-full-20261006-390.json`.
Screenshots: corresponding viewport captures under docs/design-references/simplywall-st-1b042a47/root-8a5edab2/.

## Container computed styles
```json
{
  "alignItems": "normal",
  "backdropFilter": "none",
  "background": "rgb(25, 24, 22) none repeat scroll 0% 0% / auto padding-box border-box",
  "backgroundColor": "rgb(25, 24, 22)",
  "border": "0px none rgb(255, 255, 255)",
  "borderRadius": "0px",
  "bottom": "auto",
  "boxShadow": "none",
  "color": "rgb(255, 255, 255)",
  "columnGap": "normal",
  "cursor": "auto",
  "display": "block",
  "filter": "none",
  "flexDirection": "row",
  "flexWrap": "nowrap",
  "fontFamily": "Inter, sans-serif",
  "fontSize": "14px",
  "fontWeight": "400",
  "gap": "normal",
  "gridTemplateColumns": "none",
  "gridTemplateRows": "none",
  "height": "1022px",
  "justifyContent": "normal",
  "left": "auto",
  "letterSpacing": "normal",
  "lineHeight": "20px",
  "margin": "0px",
  "maxHeight": "none",
  "maxWidth": "none",
  "minHeight": "0px",
  "minWidth": "0px",
  "mixBlendMode": "normal",
  "objectFit": "fill",
  "objectPosition": "50% 50%",
  "opacity": "1",
  "overflow": "visible",
  "overflowX": "visible",
  "overflowY": "visible",
  "padding": "40px 0px 60px",
  "position": "static",
  "right": "auto",
  "rowGap": "normal",
  "textDecoration": "none",
  "textOverflow": "clip",
  "textTransform": "none",
  "top": "auto",
  "transform": "none",
  "transition": "all",
  "whiteSpace": "normal",
  "width": "1440px",
  "zIndex": "auto"
}
```

## Responsive container bounds
```json
{
  "768": {
    "height": 1103.1875,
    "width": 752.7999877929688,
    "x": 0,
    "y": 119.375
  },
  "390": {
    "height": 1294.1875,
    "width": 375.2000122070313,
    "x": 0,
    "y": -626.1625366210938
  }
}
```

## Assets and content
Actual URLs resolve via shared/assets.ts and downloaded-media-20261006.json. All source text remains verbatim.

## States and remaining QA
Click-driven: Risks & Rewards activation is captured in research-risks-active.json. Selected tab aria-pressed=true and is-active; selected figure opacity1, others0, transition opacity .3s ease-in-out.
All eight contents and images are captured in the default DOM. Remaining source states and keyboard behavior require QA; local Enter/Space activation supports testing.
