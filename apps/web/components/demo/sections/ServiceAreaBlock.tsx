import type { DemoSectionSpec } from "../types";

export default function ServiceAreaBlock({ section }: { section: DemoSectionSpec }) {
  return (
    <section id={section.section_id} className="bg-slate-50 px-4 py-14">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-bold text-slate-950">{section.heading || "Service area"}</h2>
        {section.body && <p className="mt-3 max-w-3xl text-slate-600">{section.body}</p>}
      </div>
    </section>
  );
}
