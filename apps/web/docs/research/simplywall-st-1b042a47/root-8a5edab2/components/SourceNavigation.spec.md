# SourceNavigation specification

Target: src/components/sites/simplywall-st-1b042a47/root-8a5edab2/SourceNavigation.tsx

DOM, verbatim content, child media, and every computed style are recorded in
`computed-full-20261006-1440.json`, root index 0. This record is the exact specification; no estimated values.
Responsive child records: same root index in `computed-full-20261006-768.json` and `computed-full-20261006-390.json`.
Screenshots: corresponding viewport captures under docs/design-references/simplywall-st-1b042a47/root-8a5edab2/.

## Container computed styles
```json
{
  "alignItems": "normal",
  "backdropFilter": "none",
  "background": "rgba(253, 204, 106, 0.12) none repeat scroll 0% 0% / auto padding-box border-box",
  "backgroundColor": "rgba(253, 204, 106, 0.12)",
  "border": "0px none rgb(25, 24, 22)",
  "borderRadius": "0px",
  "bottom": "0px",
  "boxShadow": "none",
  "color": "rgb(25, 24, 22)",
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
  "height": "0px",
  "justifyContent": "normal",
  "left": "0px",
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
  "padding": "0px",
  "position": "relative",
  "right": "0px",
  "rowGap": "normal",
  "textDecoration": "none",
  "textOverflow": "clip",
  "textTransform": "none",
  "top": "0px",
  "transform": "none",
  "transition": "all",
  "whiteSpace": "normal",
  "width": "1440px",
  "zIndex": "999"
}
```

## Responsive container bounds
```json
{
  "768": {
    "height": 0,
    "width": 752.7999877929688,
    "x": 0,
    "y": -5848
  },
  "390": {
    "height": 0,
    "width": 375.2000122070313,
    "x": 0,
    "y": -5848
  }
}
```

## Assets and content
Actual URLs resolve via shared/assets.ts and downloaded-media-20261006.json. All source text remains verbatim.

## States and remaining QA
Desktop Features hover and Escape are captured in desktop-features-hover-open.json. White dropdown, 6px radius; existing source CSS implements w--open.
Mobile opened layout captured in mobile-menu-open.json: menu top72px, margins0 12px, padding0 24px, display block and white background. Open button receives w--open. Opening/closing transition still needs comparison.
Search field default appearance uses captured dimensions. Preview link goes to source search; remote suggestions/authentication are not implemented.
