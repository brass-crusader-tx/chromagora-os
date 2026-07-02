import type { DemoSectionSpec } from "../types";

export default function ContactPanel({ section }: { section: DemoSectionSpec }) {
  return (
    <section id={section.section_id} className="px-4 py-14">
      <div className="mx-auto grid max-w-6xl gap-8 md:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h2 className="text-3xl font-bold text-slate-950">{section.heading || "Contact"}</h2>
          {section.body && <p className="mt-3 text-slate-600">{section.body}</p>}
        </div>
        <form className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Name" />
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Phone or email" />
          </div>
          <textarea className="mt-4 min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="What can we help with?" />
          <button type="button" className="mt-4 rounded-md bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            {section.cta?.label || "Send request"}
          </button>
        </form>
      </div>
    </section>
  );
}
