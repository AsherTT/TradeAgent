import { LocalizedImage } from "../shared/i18n/LanguageProvider";

export function HeroReviews() {
  return (
    <div className="hero__review grid grid-cols-[1fr_1fr] items-center py-[16px]">
      <div className="flex items-center justify-center">
        <LocalizedImage
          className="h-auto w-[708px]"
          src="/sites/simplywall-st-1b042a47/root-8a5edab2/images/epic-product.png"
          alt="Trustpilot review: Epic product"
        />
      </div>
      <div className="flex items-center justify-center">
        <LocalizedImage
          className="h-auto w-[523px]"
          src="/sites/simplywall-st-1b042a47/root-8a5edab2/images/reviews.svg"
          alt="4.6 App Store, 4.3 Trustpilot, 4.6 Google Play"
        />
      </div>
    </div>
  );
}
