import BeforeAfterReveal from "./BeforeAfterReveal";
import DemoPageRenderer from "./DemoPageRenderer";
import StickyMobileCTA from "./StickyMobileCTA";
import type { SiteSpec } from "./types";

export default function DemoSiteRenderer({ siteSpec }: { siteSpec: SiteSpec }) {
  const firstPage = siteSpec.pages?.[0];
  if (!firstPage) {
    return (
      <div className="min-h-screen bg-white p-8 text-slate-950">
        Demo page unavailable.
      </div>
    );
  }

  const page = (
    <div
      className="min-h-screen bg-white text-slate-950"
      style={{
        "--demo-primary": siteSpec.brand?.primary_hex || "#1f2937",
        "--demo-accent": siteSpec.brand?.accent_hex || "#2563eb",
      } as React.CSSProperties}
    >
      <DemoPageRenderer siteSpec={siteSpec} page={firstPage} />
      <StickyMobileCTA cta={siteSpec.sticky_mobile_cta} />
    </div>
  );

  return siteSpec.before_after_reveal?.enabled ? (
    <BeforeAfterReveal config={siteSpec.before_after_reveal}>{page}</BeforeAfterReveal>
  ) : (
    page
  );
}
