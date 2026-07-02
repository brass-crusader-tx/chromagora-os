import { notFound } from "next/navigation";
import DemoSiteRenderer from "@/components/demo/DemoSiteRenderer";
import type { SiteSpec } from "@/components/demo/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_CHROMAGORA_API_KEY || process.env.NEXT_PUBLIC_API_KEY;

async function loadPreview(projectId: string, specId?: string): Promise<SiteSpec | null> {
  const query = specId ? `?spec_id=${encodeURIComponent(specId)}` : "";
  const res = await fetch(`${API_BASE}/demo-sites/projects/${encodeURIComponent(projectId)}/site-spec-preview${query}`, {
    cache: "no-store",
    headers: API_KEY ? { "X-API-Key": API_KEY } : {},
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load preview SiteSpec: ${res.status}`);
  const body = await res.json();
  return body.site_spec as SiteSpec;
}

export default async function DemoPreviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ spec_id?: string }>;
}) {
  const { projectId } = await params;
  const { spec_id } = await searchParams;
  const siteSpec = await loadPreview(projectId, spec_id);
  if (!siteSpec) notFound();
  return <DemoSiteRenderer siteSpec={siteSpec} />;
}
