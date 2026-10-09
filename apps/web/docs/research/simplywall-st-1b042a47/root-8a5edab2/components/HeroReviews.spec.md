# HeroReviews

Source: https://simplywall.st/; scope: two source review images below the video row.
Target: src/components/sites/simplywall-st-1b042a47/root-8a5edab2/HeroReviews.tsx.
References: source-desktop-1440-20261006.png, source-tablet-768-20261006.png,
source-mobile-390-20261006.png in the namespaced screenshot directory.

## DOM structure

Grid div -> two flex divs -> one real image each. No textual reconstruction of images.

## Exact computed styles and classes

- Outer: `hero__review grid grid-cols-[1fr_1fr] items-center py-[16px]`.
  display grid; two equal columns; align-items center; padding 16px 0;
  no margin, border, radius, background fill, shadow, transform or transition.
  At 1440px: width 1360px, columns 680px/680px, height 238.538px.
- Each child: `flex items-center justify-center`; transparent; margin/padding 0.
- First image: `h-auto w-[708px]`; display block; max-width 100%; height auto;
  rendered 680 x 206.538px. Alt: `Trustpilot review: Epic product`.
- Second image: `h-auto w-[523px]`; display block; max-width 100%; height auto;
  rendered 523 x 44px. Alt: `4.6 App Store, 4.3 Trustpilot, 4.6 Google Play`.

## States and behaviors

Static imagery, no links, buttons, scrolling animation, hover effect or time changes.
States/transitions: N/A. Preserve image intrinsic aspect ratios.

## Assets and verbatim text

- /sites/simplywall-st-1b042a47/root-8a5edab2/images/epic-product.png.
- /sites/simplywall-st-1b042a47/root-8a5edab2/images/reviews.svg.
Visible text belongs to those real images; do not recreate it in HTML.

## Responsive behavior

At max-width 991px, captured source stylesheet changes hero__review to one column.
768px: outer 672.8 x 280.35px; first image 672.8 x 204.35px; second 523 x 44px.
390px: outer 335.2 x 162.012px; first 335.2 x 101.812px; second 335.2 x 28.2px.
No additional responsive visual state is observed.

## Acceptance

Named React export, strict TypeScript, actual local images, no inline styles.
Source styles already include the measured 991px rule; verify typecheck.
