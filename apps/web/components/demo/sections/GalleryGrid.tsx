import type { DemoSectionSpec } from "../types";

export default function GalleryGrid({ section }: { section: DemoSectionSpec }) {
  if (!section.items?.length) return null;
  return (
    <section id={section.section_id} className="px-4 py-14">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-bold text-slate-950">{section.heading || "Gallery"}</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {section.items.map((item, index) => {
            const url = typeof item.url === "string" ? item.url : "";
            return (
              <div key={String(item.id || item.url || index)} className="aspect-[4/3] overflow-hidden rounded-lg bg-slate-100">
                {url ? (
                  <img src={url} alt={String(item.alt || "Gallery image")} className="h-full w-full object-cover" />
                ) : (
                  <div className="grid h-full place-items-center text-sm text-slate-500">Image unavailable</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
