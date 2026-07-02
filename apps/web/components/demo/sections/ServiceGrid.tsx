import type { DemoSectionSpec } from "../types";

export default function ServiceGrid({ section }: { section: DemoSectionSpec }) {
  const items = section.items?.length ? section.items : [{ title: "Core services", body: section.body }];
  return (
    <section id={section.section_id} className="px-4 py-14">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-bold text-slate-950">{section.heading || "Services"}</h2>
          {section.body && <p className="mt-3 text-slate-600">{section.body}</p>}
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item, index) => (
            <article key={String(item.title || index)} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-950">{String(item.title || item.label || "Service")}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{String(item.body || item.value || "Clear service information.")}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
