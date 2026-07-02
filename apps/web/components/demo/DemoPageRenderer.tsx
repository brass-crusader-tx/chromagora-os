import ChromagoraDemoFooter from "./ChromagoraDemoFooter";
import GalleryGrid from "./sections/GalleryGrid";
import HeroSection from "./sections/HeroSection";
import ProcessSteps from "./sections/ProcessSteps";
import QuoteCTA from "./sections/QuoteCTA";
import ReviewCards from "./sections/ReviewCards";
import ServiceAreaBlock from "./sections/ServiceAreaBlock";
import ServiceGrid from "./sections/ServiceGrid";
import ContactPanel from "./sections/ContactPanel";
import TrustStrip from "./sections/TrustStrip";
import type { DemoPageSpec, DemoSectionSpec, SiteSpec } from "./types";

function renderSection(section: DemoSectionSpec, siteSpec: SiteSpec) {
  switch (section.type) {
    case "hero":
      return <HeroSection key={section.section_id} section={section} siteSpec={siteSpec} />;
    case "service_grid":
      return <ServiceGrid key={section.section_id} section={section} />;
    case "trust_strip":
      return <TrustStrip key={section.section_id} section={section} />;
    case "gallery_grid":
      return <GalleryGrid key={section.section_id} section={section} />;
    case "review_cards":
      return <ReviewCards key={section.section_id} section={section} />;
    case "process_steps":
      return <ProcessSteps key={section.section_id} section={section} />;
    case "service_area":
      return <ServiceAreaBlock key={section.section_id} section={section} />;
    case "quote_cta":
      return <QuoteCTA key={section.section_id} section={section} />;
    case "contact_panel":
      return <ContactPanel key={section.section_id} section={section} />;
    case "footer_spacer":
      return <div key={section.section_id} className="h-8" />;
    default:
      return null;
  }
}

export default function DemoPageRenderer({ siteSpec, page }: { siteSpec: SiteSpec; page: DemoPageSpec }) {
  return (
    <>
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <a href="#" className="min-w-0 text-sm font-bold text-slate-950 md:text-base">
            {siteSpec.business_name}
          </a>
          <nav className="hidden items-center gap-5 text-sm text-slate-600 md:flex">
            {siteSpec.navigation?.map((item) => (
              <a key={`${item.href}-${item.label}`} href={item.href} className="hover:text-slate-950">
                {item.label}
              </a>
            ))}
          </nav>
          <a
            href={siteSpec.primary_cta.href}
            className="shrink-0 rounded-md px-3 py-2 text-sm font-semibold text-white"
            style={{ backgroundColor: siteSpec.brand?.accent_hex || "#2563eb" }}
          >
            {siteSpec.primary_cta.label}
          </a>
        </div>
      </header>
      <main>
        {page.sections?.map((section) => renderSection(section, siteSpec))}
      </main>
      {siteSpec.chromagora_footer?.enabled !== false && (
        <ChromagoraDemoFooter
          text={siteSpec.chromagora_footer?.text}
          linkUrl={siteSpec.chromagora_footer?.link_url}
        />
      )}
    </>
  );
}
