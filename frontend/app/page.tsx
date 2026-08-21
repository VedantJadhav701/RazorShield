import Hero from "@/components/landing/Hero";
import InformationStrip from "@/components/landing/InformationStrip";
import CoreStatement from "@/components/landing/CoreStatement";
import ScenarioPreview from "@/components/landing/ScenarioPreview";
import Pipeline from "@/components/landing/Pipeline";
import TrustProof from "@/components/landing/TrustProof";
import SLMSection from "@/components/landing/SLMSection";
import FinalCTA from "@/components/landing/FinalCTA";

export default function LandingPage() {
  return (
    <div className="bg-brand-black min-h-screen">
      <Hero />
      <InformationStrip />
      <CoreStatement />
      <ScenarioPreview />
      <Pipeline />
      <TrustProof />
      <SLMSection />
      <FinalCTA />
    </div>
  );
}
