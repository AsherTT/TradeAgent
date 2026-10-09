export function HeroMedia() {
  return (
    <div className="flex h-[575px] min-w-0 flex-1 items-center justify-end">
      <video
        className="h-auto w-[837px] max-w-full bg-[var(--slate)] shadow-[rgba(0,0,0,0.2)_0_24px_32px_5px]"
        src="/sites/simplywall-st-1b042a47/root-8a5edab2/videos/simplywall-portfolio-feature.mp4"
        autoPlay
        muted
        loop
        playsInline
      />
    </div>
  );
}
