import type { ReactNode } from "react";
import { SourceFrame } from "../shared/SourceFrame";
import { SourceNavigation } from "../root-8a5edab2/SourceNavigation";
import { HeroSection } from "../root-8a5edab2/HeroSection";
import { PlatformSection } from "../root-8a5edab2/PlatformSection";
import { TrackingSection } from "../root-8a5edab2/TrackingSection";
import { PortfolioAnalysisSection } from "../root-8a5edab2/PortfolioAnalysisSection";
import { ResearchSection } from "../root-8a5edab2/ResearchSection";
import { StockSearchSection } from "../root-8a5edab2/StockSearchSection";
import { DiscoverySection } from "../root-8a5edab2/DiscoverySection";
import { SmartUpdatesSection } from "../root-8a5edab2/SmartUpdatesSection";
import { CommunitySection } from "../root-8a5edab2/CommunitySection";
import { TestimonialsSection } from "../root-8a5edab2/TestimonialsSection";
import { FinalCtaSection } from "../root-8a5edab2/FinalCtaSection";
import { SourceFooter } from "../root-8a5edab2/SourceFooter";

export function FullSourceHome({ brand = "source", notice }: {
  brand?: "source" | "tradeagent";
  notice: ReactNode;
}) {
  return (
    <SourceFrame className="home-page">
      <aside className="bg-[#262e3a] px-5 py-3 text-center text-xs leading-5 text-white">{notice}</aside>
      <SourceNavigation brand={brand} />
      <main className="home-content">
        <HeroSection />
        <PlatformSection />
        <TrackingSection />
        <PortfolioAnalysisSection />
        <ResearchSection />
        <StockSearchSection />
        <DiscoverySection />
        <SmartUpdatesSection />
        <CommunitySection />
        <TestimonialsSection />
        <FinalCtaSection />
      </main>
      <SourceFooter brand={brand} />
    </SourceFrame>
  );
}
