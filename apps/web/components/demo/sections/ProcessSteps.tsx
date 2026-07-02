import type { DemoSectionSpec } from "../types";

export default function ProcessSteps({ section }: { section: DemoSectionSpec }) {
  const items = section.items?.length ? section.items : [];
  if (!items.length) return null;
  return (
    <section id={section.section_id} className="px-4 py-14">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-bold text-slate-950">{section.heading || "Process"}</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {items.map((item, index) => (
            <div key={String(item.title || index)} className="rounded-lg border border-slate-200 p-5">
              <p className="text-sm font-semibold text-slate-500">Step {index + 1}</p>
              <h3 className="mt-2 font-semibold text-slate-950">{String(item.title || item.label || "Step")}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{String(item.body || item.value || "")}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
