import type { DemoSectionSpec } from "../types";

export default function ReviewCards({ section }: { section: DemoSectionSpec }) {
  if (!section.items?.length) return null;
  return (
    <section id={section.section_id} className="bg-slate-50 px-4 py-14">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-bold text-slate-950">{section.heading || "Reviews"}</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {section.items.map((review, index) => (
            <article key={String(review.source_url || index)} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm leading-6 text-slate-700">{String(review.review_text || "")}</p>
              <p className="mt-4 text-sm font-semibold text-slate-950">{String(review.reviewer_name || "Verified reviewer")}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
