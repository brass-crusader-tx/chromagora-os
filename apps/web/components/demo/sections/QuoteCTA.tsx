import type { DemoSectionSpec } from "../types";

export default function QuoteCTA({ section }: { section: DemoSectionSpec }) {
  return (
    <section id={section.section_id} className="px-4 py-14">
      <div className="mx-auto max-w-6xl rounded-lg bg-slate-950 px-5 py-10 text-white md:px-10">
        <h2 className="text-3xl font-bold">{section.heading || "Request a quote"}</h2>
        {section.body && <p className="mt-3 max-w-2xl text-slate-300">{section.body}</p>}
        {section.cta && (
          <a href={section.cta.href} className="mt-6 inline-flex rounded-md bg-white px-5 py-3 text-sm font-semibold text-slate-950">
            {section.cta.label}
          </a>
        )}
      </div>
    </section>
  );
}
