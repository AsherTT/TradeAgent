import { DemoPanel } from "@/components/product/DemoPanel";
import { SourceFrame } from "../shared/SourceFrame";
import { EnhancedANavigation } from "./EnhancedANavigation";
import { EnhancedAHero } from "./EnhancedAHero";
import { EnhancedAPlatform } from "./EnhancedAPlatform";
import { EnhancedASearch } from "./EnhancedASearch";
import { EnhancedAWorkflow } from "./EnhancedAWorkflow";
import { EnhancedAFooter } from "./EnhancedAFooter";

export function EnhancedAHome() {
  return (
    <SourceFrame className="home-page">
      <EnhancedANavigation />
      <main className="home-content" id="main">
        <EnhancedAHero media={<div id="demo"><DemoPanel appearance="source-frame" /></div>} />
        <EnhancedAPlatform />
        <EnhancedASearch />
        <EnhancedAWorkflow />
      </main>
      <EnhancedAFooter />
    </SourceFrame>
  );
}
