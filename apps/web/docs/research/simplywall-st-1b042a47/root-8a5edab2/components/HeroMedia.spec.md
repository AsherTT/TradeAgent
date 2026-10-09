# HeroMedia

Source: https://simplywall.st/; scope: the real first-screen video and its wrapper.
Target: src/components/sites/simplywall-st-1b042a47/root-8a5edab2/HeroMedia.tsx.
Reference: source-desktop-1440-20261006.png, source-tablet-768-20261006.png,
source-mobile-390-20261006.png in the namespaced screenshot directory.

## DOM structure

One div contains one video. No player chrome, custom controls, or substitute image.
Parent is the hero flex content row, gap 40px, padding-top 40px; below 991px
that parent becomes a column. Parent construction belongs to HeroSection.

## Exact computed styles and original classes

- Wrapper: `flex h-[575px] min-w-0 flex-1 items-center justify-end`.
  display flex; flex 1 1 0%; min-width 0; align-items center;
  justify-content flex-end; desktop width 780px/height 575px at 1440px capture.
  Transparent background, padding/margin 0, no border/radius/shadow/transform.
- Video: `h-auto w-[837px] max-w-full bg-[var(--slate)] shadow-[rgba(0,0,0,0.2)_0_24px_32px_5px]`.
  block; width 837px subject to max-width 100%; height auto; object-fit contain;
  background #262e3a; shadow rgba(0,0,0,.2) 0 24px 32px 5px; no radius/border.
  Actual video is 780 x 438.913px in the desktop capture.

## States and behaviors

Time driven playback: autoplay, muted, loop, playsInline; controls absent.
Fresh source read confirmed readyState 4 and paused false. No click or hover
effect exists on this component. Do not synchronize frames by mutating the source.
Native media decoding/playback determines rendered frames.

## Assets and text

Local video: /sites/simplywall-st-1b042a47/root-8a5edab2/videos/simplywall-portfolio-feature.mp4.
Verbatim visible text: N/A. Shared source styles/fonts are already prepared.

## Responsive behavior

Preserve the original flex classes rather than freezing measured pixel heights.
Tablet 768px: wrapper/video 672.8 x 378.6px; mobile 390px: 335.2 x 188.625px.
Width follows the hero container; desktop keeps the measured 575px wrapper.
No additional media transition, loading UI or breakpoint is observed.

## Acceptance

Named React component export. Strict TypeScript. No inline styles or source scripts.
Use the real local MP4 and verify typecheck; parent assembly receives visual QA.
