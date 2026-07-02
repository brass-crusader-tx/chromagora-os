import { notFound } from "next/navigation";
import DemoSiteRenderer from "@/components/demo/DemoSiteRenderer";
import type { SiteSpec } from "@/components/demo/types";

const API_BASE =
  process.env.DEMO_FACTORY_INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_CHROMAGORA_API_KEY || process.env.NEXT_PUBLIC_API_KEY;

type SiteSpecLoadResult = {
  siteSpec: SiteSpec | null;
  unavailable?: boolean;
};

async function loadSiteSpec(slug: string): Promise<SiteSpecLoadResult> {
  const res = await fetch(`${API_BASE}/demo-sites/public/${encodeURIComponent(slug)}/site-spec`, {
    cache: "no-store",
    headers: API_KEY ? { "X-API-Key": API_KEY } : {},
  });
  if (res.status === 404) return { siteSpec: null };
  if (!res.ok) return { siteSpec: null, unavailable: true };
  const body = await res.json();
  return { siteSpec: body.site_spec as SiteSpec };
}

export default async function PublicDemoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const { siteSpec, unavailable } = await loadSiteSpec(slug);
  if (unavailable) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
        <div className="max-w-md text-center">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-400">Demo unavailable</p>
          <h1 className="mt-3 text-3xl font-semibold">This preview is still being prepared.</h1>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            The demo URL is live, but the published SiteSpec is not available yet.
          </p>
        </div>
      </main>
    );
  }
  if (!siteSpec) notFound();
  return <DemoSiteRenderer siteSpec={siteSpec} />;
}
