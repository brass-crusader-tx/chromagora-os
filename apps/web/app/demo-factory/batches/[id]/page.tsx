"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ErrorBanner from "@/components/ErrorBanner";
import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";

interface BatchDetail {
  batch: {
    id: string;
    source_filename: string;
    status: string;
    total_rows: number;
    queued_count: number;
    running_count: number;
    published_count: number;
    failed_count: number;
    current_row_number?: number | null;
  };
  rows: Array<{
    id: string;
    row_number: number;
    rank?: number | null;
    business_name: string;
    website_url?: string | null;
    demo_slug: string;
    status: string;
    last_error?: string | null;
    project_id?: string | null;
    project?: {
      id: string;
      status: string;
      current_stage?: string | null;
      demo_host?: string | null;
    } | null;
  }>;
}

export default function DemoBatchDetailPage() {
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = useState<BatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    setError(null);
    try {
      setDetail(await api.get<BatchDetail>(`/demo-sites/batches/${params.id}`));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to load batch");
    }
  }

  useEffect(() => {
    if (params.id) loadDetail();
  }, [params.id]);

  async function projectAction(projectId: string, action: "retry" | "archive") {
    try {
      await api.post(`/demo-sites/projects/${projectId}/${action}`);
      await loadDetail();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : `Failed to ${action} project`);
    }
  }

  if (!detail && !error) return <div className="p-6 text-sm text-text-muted">Loading batch...</div>;

  return (
    <div className="max-w-7xl p-4 md:p-6">
      <PageHeader
        title={detail?.batch.source_filename || "Demo Batch"}
        description="Rows are shown in processing order"
        actions={<Link className="btn-secondary" href="/demo-factory">Back</Link>}
      />
      {error && <ErrorBanner message={error} onRetry={loadDetail} />}
      {detail && (
        <>
          <div className="mt-4 grid gap-4 md:grid-cols-5">
            <StatCard label="Total" value={detail.batch.total_rows} />
            <StatCard label="Queued" value={detail.batch.queued_count} />
            <StatCard label="Running" value={detail.batch.running_count} accent />
            <StatCard label="Published" value={detail.batch.published_count} />
            <StatCard label="Failed" value={detail.batch.failed_count} />
          </div>
          <div className="mt-6 card overflow-hidden p-0">
            <div className="flex items-center justify-between border-b border-bg-border p-4">
              <div>
                <h2 className="font-semibold text-text">Rows</h2>
                <p className="text-sm text-text-muted">Current row {detail.batch.current_row_number || "none"}</p>
              </div>
              <StatusBadge status={detail.batch.status} size="md" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-bg-elevated text-left text-xs uppercase text-text-dim">
                  <tr>
                    <th className="px-4 py-3">Order</th>
                    <th className="px-4 py-3">Business</th>
                    <th className="px-4 py-3">Slug</th>
                    <th className="px-4 py-3">Stage</th>
                    <th className="px-4 py-3">Demo</th>
                    <th className="px-4 py-3">Error</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-bg-border">
                  {detail.rows.map((row) => (
                    <tr key={row.id}>
                      <td className="px-4 py-3">#{row.row_number}{row.rank ? ` / rank ${row.rank}` : ""}</td>
                      <td className="px-4 py-3">
                        {row.project_id ? (
                          <Link className="font-medium text-accent hover:underline" href={`/demo-factory/projects/${row.project_id}`}>
                            {row.business_name}
                          </Link>
                        ) : row.business_name}
                        {row.website_url && <p className="text-xs text-text-dim">{row.website_url}</p>}
                      </td>
                      <td className="px-4 py-3">{row.demo_slug}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={row.project?.status || row.status} />
                        <p className="mt-1 text-xs text-text-dim">{row.project?.current_stage || row.status}</p>
                      </td>
                      <td className="px-4 py-3">
                        {row.project?.demo_host && row.project.status === "published" ? (
                          <Link className="text-accent hover:underline" href={`/demo/${row.demo_slug}`}>Open</Link>
                        ) : "Not published"}
                      </td>
                      <td className="max-w-xs px-4 py-3 text-xs text-danger">{row.last_error}</td>
                      <td className="px-4 py-3">
                        {row.project_id && (
                          <div className="flex gap-2">
                            <button className="btn-secondary px-3 py-1 text-xs" onClick={() => projectAction(row.project_id!, "retry")}>Retry</button>
                            <button className="btn-danger px-3 py-1 text-xs" onClick={() => projectAction(row.project_id!, "archive")}>Archive</button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
