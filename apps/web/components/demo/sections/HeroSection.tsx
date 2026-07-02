import type { DemoSectionSpec, SiteSpec } from "../types";

export default function HeroSection({ section, siteSpec }: { section: DemoSectionSpec; siteSpec: SiteSpec }) {
  return (
    <section className="bg-slate-50">
      <div className="mx-auto grid min-h-[72vh] max-w-6xl items-center gap-8 px-4 py-14 md:grid-cols-[1.1fr_0.9fr] md:py-20">
        <div>
          {section.eyebrow && (
            <p className="mb-3 text-sm font-semibold uppercase text-slate-500">{section.eyebrow}</p>
          )}
          <h1 className="max-w-3xl text-4xl font-bold leading-tight text-slate-950 md:text-6xl">
            {section.heading || siteSpec.business_name}
          </h1>
          {section.body && <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">{section.body}</p>}
          {section.cta && (
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={section.cta.href}
                className="rounded-md px-5 py-3 text-sm font-semibold text-white"
                style={{ backgroundColor: siteSpec.brand?.accent_hex || "#2563eb" }}
              >
                {section.cta.label}
              </a>
              <a href="#services" className="rounded-md border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-950">
                View services
              </a>
            </div>
          )}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-semibold text-slate-500">{siteSpec.business_vertical}</p>
          <p className="mt-3 text-2xl font-bold text-slate-950">{siteSpec.service_area || "Local service area"}</p>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Clear service hierarchy, proof-aware messaging, and a direct quote path for mobile visitors.
          </p>
        </div>
      </div>
    </section>
  );
}
