"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ErrorBanner from "@/components/ErrorBanner";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";

interface Project {
  id: string;
  business_name: string;
  source_url?: string | null;
  normalized_domain?: string | null;
  status: string;
  current_stage?: string | null;
  demo_slug: string;
  demo_host?: string | null;
  error_message?: string | null;
}

interface Artifacts {
  brand_documents: Array<Record<string, any>>;
  assets: Array<Record<string, any>>;
  reviews: Array<Record<string, any>>;
  site_specs: Array<Record<string, any>>;
  model_calls: Array<Record<string, any>>;
  supervisor_events: Array<Record<string, any>>;
}

export default function DemoProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [artifacts, setArtifacts] = useState<Artifacts | null>(null);
  const [qa, setQa] = useState<Array<Record<string, any>>>([]);
  const [deployment, setDeployment] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [heroHeading, setHeroHeading] = useState("");
  const [ctaLabel, setCtaLabel] = useState("");
  const [ctaHref, setCtaHref] = useState("");
  const [savingSpec, setSavingSpec] = useState(false);
  const [publishingSpec, setPublishingSpec] = useState(false);
  const [draftSpecId, setDraftSpecId] = useState<string | null>(null);

  async function loadProject() {
    setError(null);
    try {
      const [projectData, artifactData, qaData, deploymentData] = await Promise.all([
        api.get<Project>(`/demo-sites/projects/${params.id}`),
        api.get<Artifacts>(`/demo-sites/projects/${params.id}/artifacts`),
        api.get<Array<Record<string, any>>>(`/demo-sites/projects/${params.id}/qa`),
        api.get<Record<string, any> | null>(`/demo-sites/projects/${params.id}/deployment`),
      ]);
      setProject(projectData);
      setArtifacts(artifactData);
      setQa(qaData);
      setDeployment(deploymentData);
      const latestSpec = artifactData.site_specs?.[0]?.spec_json;
      const hero = latestSpec?.pages?.[0]?.sections?.find((section: any) => section.type === "hero");
      setHeroHeading(String(hero?.heading || ""));
      setCtaLabel(String(latestSpec?.primary_cta?.label || hero?.cta?.label || ""));
      setCtaHref(String(latestSpec?.primary_cta?.href || hero?.cta?.href || "#contact"));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to load project");
    }
  }

  useEffect(() => {
    if (params.id) loadProject();
  }, [params.id]);

  async function retry() {
    try {
      await api.post(`/demo-sites/projects/${params.id}/retry`);
      await loadProject();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Retry failed");
    }
  }

  async function saveDraftSpec() {
    const latest = artifacts?.site_specs?.[0];
    if (!latest?.spec_json) {
      setError("No SiteSpec is available to edit yet");
      return;
    }
    setSavingSpec(true);
    setError(null);
    try {
      const spec = structuredClone(latest.spec_json);
      spec.primary_cta = { ...(spec.primary_cta || {}), label: ctaLabel, href: ctaHref || "#contact" };
      if (spec.sticky_mobile_cta) {
        spec.sticky_mobile_cta = { ...spec.sticky_mobile_cta, label: ctaLabel, href: ctaHref || "#contact" };
      }
      for (const page of spec.pages || []) {
        for (const section of page.sections || []) {
          if (section.type === "hero") {
            section.heading = heroHeading;
            if (section.cta) section.cta = { ...section.cta, label: ctaLabel, href: ctaHref || "#contact" };
          }
          if (["quote_cta", "contact_panel"].includes(section.type) && section.cta) {
            section.cta = { ...section.cta, label: ctaLabel, href: ctaHref || "#contact" };
          }
        }
      }
      const result = await api.patch<{ site_spec_row: { id: string } }>(
        `/demo-sites/projects/${params.id}/site-spec`,
        { spec_id: latest.id, spec_json: spec, republish: false }
      );
      setDraftSpecId(result.site_spec_row.id);
      await loadProject();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to save SiteSpec draft");
    } finally {
      setSavingSpec(false);
    }
  }

  async function publishSpec(specId?: string | null) {
    const targetSpecId = specId || draftSpecId || artifacts?.site_specs?.[0]?.id;
    if (!targetSpecId) {
      setError("No SiteSpec is available to publish");
      return;
    }
    setPublishingSpec(true);
    setError(null);
    try {
      await api.post(`/demo-sites/projects/${params.id}/publish-spec/${targetSpecId}`);
      await loadProject();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to publish SiteSpec");
    } finally {
      setPublishingSpec(false);
    }
  }

  const brandDoc = artifacts?.brand_documents?.[0];
  const oldScreenshot = artifacts?.assets?.find((asset) => asset.asset_type === "old_site_screenshot");
  const visualQa = qa.find((report) => report.report_type === "visual");
  const latestSpec = artifacts?.site_specs?.[0];
  const previewSpecId = draftSpecId || latestSpec?.id;

  return (
    <div className="max-w-7xl p-4 md:p-6">
      <PageHeader
        title={project?.business_name || "Demo Project"}
        description={project?.normalized_domain || project?.source_url || ""}
        actions={
          <div className="flex gap-2">
            {project?.status === "published" && <Link className="btn-primary" href={`/demo/${project.demo_slug}`}>Open Demo</Link>}
            <button className="btn-secondary" onClick={retry}>Retry Stage</button>
          </div>
        }
      />
      {error && <ErrorBanner message={error} onRetry={loadProject} />}
      {project && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-6">
            <section className="card">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-text">Project State</h2>
                  <p className="mt-1 text-sm text-text-muted">{project.current_stage || "No active stage"}</p>
                </div>
                <StatusBadge status={project.status} size="md" />
              </div>
              {project.demo_host && <p className="mt-4 text-sm text-text-muted">Host: {project.demo_host}</p>}
              {project.error_message && <p className="mt-4 text-sm text-danger">{project.error_message}</p>}
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <PreviewCard title="Old Site Screenshot" asset={oldScreenshot} />
              <PreviewCard title="New Site QA Screenshot" asset={visualQa?.screenshots_json?.[0]} />
            </section>

            <section className="card">
              <h2 className="font-semibold text-text">BrandDoc Summary</h2>
              <p className="mt-3 text-sm text-text-muted">{String(brandDoc?.summary || "No BrandDoc yet")}</p>
              {brandDoc?.document_json && (
                <pre className="mt-4 max-h-80 overflow-auto rounded-md bg-bg p-3 text-xs text-text-muted">
                  {JSON.stringify(brandDoc.document_json, null, 2)}
                </pre>
              )}
            </section>

            <section className="card">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-text">Edit Demo Copy</h2>
                  <p className="mt-1 text-sm text-text-muted">Save edits as a new SiteSpec draft before publishing.</p>
                </div>
                {previewSpecId && (
                  <Link className="btn-secondary" href={`/demo-preview/${params.id}?spec_id=${previewSpecId}`}>
                    Preview
                  </Link>
                )}
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                  <label className="label">Hero heading</label>
                  <input className="input" value={heroHeading} onChange={(event) => setHeroHeading(event.target.value)} />
                </div>
                <div>
                  <label className="label">Primary CTA label</label>
                  <input className="input" value={ctaLabel} onChange={(event) => setCtaLabel(event.target.value)} />
                </div>
                <div>
                  <label className="label">Primary CTA href</label>
                  <input className="input" value={ctaHref} onChange={(event) => setCtaHref(event.target.value)} />
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn-primary" onClick={saveDraftSpec} disabled={!latestSpec || savingSpec}>
                  {savingSpec ? "Saving..." : "Save Draft"}
                </button>
                <button className="btn-secondary" onClick={() => publishSpec()} disabled={!previewSpecId || publishingSpec}>
                  {publishingSpec ? "Publishing..." : "Run QA + Publish"}
                </button>
              </div>
            </section>

            <section className="card">
              <h2 className="font-semibold text-text">QA Reports</h2>
              <div className="mt-4 space-y-3">
                {qa.length === 0 ? <p className="text-sm text-text-muted">No QA reports yet.</p> : qa.map((report) => (
                  <div key={report.id} className="rounded-md bg-bg-elevated p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-text">{report.report_type}</p>
                      <StatusBadge status={report.status} />
                    </div>
                    <pre className="mt-2 max-h-48 overflow-auto text-xs text-text-muted">{JSON.stringify(report.report_json || report, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <aside className="space-y-6">
            <section className="card">
              <h2 className="font-semibold text-text">Deployment</h2>
              {deployment ? (
                <div className="mt-3 space-y-2 text-sm text-text-muted">
                  <StatusBadge status={String(deployment.status)} />
                  <p>{String(deployment.demo_url || "")}</p>
                </div>
              ) : <p className="mt-3 text-sm text-text-muted">Not deployed.</p>}
            </section>

            <section className="card">
              <h2 className="font-semibold text-text">Reviews</h2>
              <p className="mt-3 text-sm text-text-muted">{artifacts?.reviews?.length || 0} stored review records</p>
            </section>

            <section className="card">
              <h2 className="font-semibold text-text">Model Calls</h2>
              <div className="mt-3 space-y-2">
                {(artifacts?.model_calls || []).map((call) => (
                  <div key={call.id} className="rounded-md bg-bg-elevated p-2 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-text">{String(call.stage)}</span>
                      <StatusBadge status={String(call.status)} />
                    </div>
                    <p className="mt-1 text-text-dim">{String(call.model)}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="card">
              <h2 className="font-semibold text-text">Supervisor Events</h2>
              <div className="mt-3 space-y-2 text-xs text-text-muted">
                {(artifacts?.supervisor_events || []).map((event) => (
                  <p key={event.id}>{String(event.event_type)}: {String(event.message || "")}</p>
                ))}
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  );
}

function PreviewCard({ title, asset }: { title: string; asset?: Record<string, any> }) {
  const path = asset?.public_url || asset?.path || asset?.storage_path;
  return (
    <div className="card">
      <h2 className="font-semibold text-text">{title}</h2>
      {path ? (
        <div className="mt-3 aspect-video overflow-hidden rounded-md bg-bg-elevated">
          {String(path).startsWith("http") || String(path).startsWith("/") ? (
            <img src={String(path)} alt={title} className="h-full w-full object-cover" />
          ) : (
            <div className="grid h-full place-items-center p-4 text-center text-xs text-text-muted">{String(path)}</div>
          )}
        </div>
      ) : (
        <div className="mt-3 grid aspect-video place-items-center rounded-md bg-bg-elevated text-sm text-text-dim">
          Not available
        </div>
      )}
    </div>
  );
}
