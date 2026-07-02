"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ErrorBanner from "@/components/ErrorBanner";
import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { api, apiFetch } from "@/lib/api";

interface DemoBatch {
  id: string;
  source_filename: string;
  status: string;
  total_rows: number;
  queued_count: number;
  running_count: number;
  published_count: number;
  failed_count: number;
  current_row_number?: number | null;
  created_at: string;
}

interface LinkDropResult {
  project?: { id: string };
  project_url?: string;
  batch?: { status?: string };
}

export default function DemoFactoryPage() {
  const router = useRouter();
  const [batches, setBatches] = useState<DemoBatch[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [linkUrl, setLinkUrl] = useState("");
  const [linkBusinessName, setLinkBusinessName] = useState("");
  const [linkNote, setLinkNote] = useState("");
  const [linkAutoStart, setLinkAutoStart] = useState(true);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [linkSubmitting, setLinkSubmitting] = useState(false);
  const [workerRunning, setWorkerRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const showDevControls = process.env.NEXT_PUBLIC_DEMO_FACTORY_DEV_CONTROLS === "true";

  async function loadBatches() {
    setLoading(true);
    setError(null);
    setStatusMessage(null);
    try {
      setBatches(await api.get<DemoBatch[]>("/demo-sites/batches"));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to load demo batches");
    } finally {
      setLoading(false);
    }
  }

  async function submitLinkDrop(event: React.FormEvent) {
    event.preventDefault();
    if (!linkUrl.trim()) return;
    setLinkSubmitting(true);
    setError(null);
    setStatusMessage(null);
    try {
      const result = await api.post<LinkDropResult>("/demo-sites/import-link", {
        website_url: linkUrl.trim(),
        business_name: linkBusinessName.trim() || null,
        suggested_demo_cta: linkNote.trim() || null,
        demo_angle: linkNote.trim() || null,
        before_after_slider_angle: linkNote.trim() || null,
        auto_start: linkAutoStart,
      });
      setStatusMessage(
        linkAutoStart ? "Project queued and batch started." : "Project queued. Start the batch when ready."
      );
      setLinkUrl("");
      setLinkBusinessName("");
      setLinkNote("");
      await loadBatches();
      if (result.project?.id) {
        router.push(`/demo-factory/projects/${result.project.id}`);
      } else if (result.project_url) {
        router.push(result.project_url);
      }
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Link import failed");
    } finally {
      setLinkSubmitting(false);
    }
  }

  async function runWorkerOnce() {
    setWorkerRunning(true);
    setError(null);
    setStatusMessage(null);
    try {
      const result = await api.post<{ status?: string }>("/demo-sites/dev/run-worker-once?auto_start=true");
      setStatusMessage(`Worker cycle: ${result.status || "completed"}`);
      await loadBatches();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Worker cycle failed");
    } finally {
      setWorkerRunning(false);
    }
  }

  useEffect(() => {
    loadBatches();
  }, []);

  async function uploadCsv(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setSubmitting(true);
    setError(null);
    try {
      const content = await file.text();
      await apiFetch("/demo-sites/import-csv", {
        method: "POST",
        body: content,
        headers: { "Content-Type": "text/csv", "X-Filename": file.name },
      });
      setFile(null);
      await loadBatches();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "CSV import failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function batchAction(batchId: string, action: "start" | "pause" | "resume") {
    try {
      await api.post(`/demo-sites/batches/${batchId}/${action}`);
      await loadBatches();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : `Failed to ${action} batch`);
    }
  }

  const totals = batches.reduce(
    (acc, batch) => ({
      total: acc.total + (batch.total_rows || 0),
      queued: acc.queued + (batch.queued_count || 0),
      running: acc.running + (batch.running_count || 0),
      published: acc.published + (batch.published_count || 0),
      failed: acc.failed + (batch.failed_count || 0),
    }),
    { total: 0, queued: 0, running: 0, published: 0, failed: 0 }
  );

  return (
    <div className="max-w-7xl p-4 md:p-6">
      <PageHeader
        title="Demo Factory"
        description="Upload ranked CSV batches and monitor private demo production"
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={() => setError(null)} />
        </div>
      )}
      {statusMessage && (
        <div className="mb-4 rounded-md border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-100">
          {statusMessage}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-5">
        <StatCard label="Rows" value={totals.total} />
        <StatCard label="Queued" value={totals.queued} />
        <StatCard label="Running" value={totals.running} accent />
        <StatCard label="Published" value={totals.published} />
        <StatCard label="Failed" value={totals.failed} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[420px_minmax(0,1fr)]">
        <div className="space-y-6">
          <form onSubmit={uploadCsv} className="card space-y-4">
            <div>
              <label className="label">Lead CSV</label>
              <input
                type="file"
                accept=".csv,text/csv"
                className="input"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </div>
            <button className="btn-primary w-full" disabled={!file || submitting}>
              {submitting ? "Importing..." : "Import CSV"}
            </button>
          </form>

          <form onSubmit={submitLinkDrop} className="card space-y-4">
            <div>
              <h2 className="font-semibold text-text">Build from a link</h2>
              <p className="mt-1 text-sm text-text-muted">Create a one-row batch from a public website.</p>
            </div>
            <div>
              <label className="label">Website URL</label>
              <input
                className="input"
                type="url"
                placeholder="https://examplecontractor.com"
                value={linkUrl}
                onChange={(event) => setLinkUrl(event.target.value)}
              />
            </div>
            <div>
              <label className="label">Business name override</label>
              <input
                className="input"
                value={linkBusinessName}
                onChange={(event) => setLinkBusinessName(event.target.value)}
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="label">CTA / demo angle note</label>
              <textarea
                className="input min-h-24"
                value={linkNote}
                onChange={(event) => setLinkNote(event.target.value)}
                placeholder="Optional: e.g. make photo-based estimates obvious"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-text-muted">
              <input
                type="checkbox"
                checked={linkAutoStart}
                onChange={(event) => setLinkAutoStart(event.target.checked)}
              />
              Auto-start the one-row batch
            </label>
            <button className="btn-primary w-full" disabled={!linkUrl.trim() || linkSubmitting}>
              {linkSubmitting ? "Queueing..." : "Build Demo"}
            </button>
          </form>

          {showDevControls && (
            <div className="card space-y-3">
              <h2 className="font-semibold text-text">Dev controls</h2>
              <button className="btn-secondary w-full" onClick={runWorkerOnce} disabled={workerRunning}>
                {workerRunning ? "Running..." : "Run one worker cycle"}
              </button>
            </div>
          )}
        </div>

        <div className="card overflow-hidden p-0">
          <div className="border-b border-bg-border p-4">
            <h2 className="font-semibold text-text">Recent Batches</h2>
          </div>
          {loading ? (
            <div className="p-4 text-sm text-text-muted">Loading batches...</div>
          ) : batches.length === 0 ? (
            <div className="p-4 text-sm text-text-muted">No demo batches imported yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-bg-elevated text-left text-xs uppercase text-text-dim">
                  <tr>
                    <th className="px-4 py-3">Batch</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Progress</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-bg-border">
                  {batches.map((batch) => (
                    <tr key={batch.id}>
                      <td className="px-4 py-3">
                        <Link className="font-medium text-accent hover:underline" href={`/demo-factory/batches/${batch.id}`}>
                          {batch.source_filename}
                        </Link>
                        <p className="mt-1 text-xs text-text-dim">Current row {batch.current_row_number || "none"}</p>
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={batch.status} /></td>
                      <td className="px-4 py-3">
                        {batch.published_count}/{batch.total_rows} published, {batch.failed_count} failed
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <button className="btn-secondary px-3 py-1 text-xs" onClick={() => batchAction(batch.id, "start")}>Start</button>
                          <button className="btn-secondary px-3 py-1 text-xs" onClick={() => batchAction(batch.id, "pause")}>Pause</button>
                          <button className="btn-secondary px-3 py-1 text-xs" onClick={() => batchAction(batch.id, "resume")}>Resume</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
