"use client";

import type { CTAConfig } from "./types";

export default function StickyMobileCTA({ cta }: { cta?: CTAConfig | null }) {
  if (!cta) return null;
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur md:hidden">
      <a href={cta.href} className="block rounded-md bg-slate-950 px-4 py-3 text-center text-sm font-semibold text-white">
        {cta.label}
      </a>
    </div>
  );
}
