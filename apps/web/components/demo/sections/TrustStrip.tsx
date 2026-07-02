import type { DemoSectionSpec } from "../types";

export default function TrustStrip({ section }: { section: DemoSectionSpec }) {
  const items = section.items?.length ? section.items : [];
  return (
    <section id={section.section_id} className="border-y border-slate-200 bg-slate-950 px-4 py-10 text-white">
      <div className="mx-auto max-w-6xl">
        {section.heading && <h2 className="text-xl font-semibold">{section.heading}</h2>}
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {items.map((item, index) => (
            <div key={String(item.label || index)}>
              <p className="text-sm text-slate-300">{String(item.label || "Signal")}</p>
              <p className="mt-1 font-semibold">{String(item.value || "")}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
