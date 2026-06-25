"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";

interface Approval {
  id: string;
  action_type: string;
  description?: string;
  status: string;
  business_id?: string;
  dollar_amount?: number;
  created_at: string;
  resolved_at?: string;
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "pending" | "resolved">("all");
  const [processing, setProcessing] = useState<string | null>(null);

  async function loadApprovals() {
    setLoading(true);
    try {
      const data = await api.get<Approval[]>("/approvals");
      setApprovals(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApprovals();
  }, []);

  async function handleApprove(id: string) {
    setProcessing(id);
    try {
      await api.post(`/approvals/${id}/approve`);
      loadApprovals();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to approve");
    } finally {
      setProcessing(null);
    }
  }

  async function handleReject(id: string) {
    setProcessing(id);
    try {
      await api.post(`/approvals/${id}/reject`);
      loadApprovals();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to reject");
    } finally {
      setProcessing(null);
    }
  }

  const filtered = approvals.filter((a) => {
    if (filter === "pending") return a.status === "pending";
    if (filter === "resolved") return a.status !== "pending";
    return true;
  });

  const pendingCount = approvals.filter((a) => a.status === "pending").length;

  return (
    <div className="p-4 md:p-6 max-w-5xl">
      <PageHeader
        title="Approvals"
        description={`${pendingCount} pending approval${pendingCount !== 1 ? "s" : ""} requiring your review`}
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadApprovals} />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {(["all", "pending", "resolved"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`btn text-xs ${
              filter === f ? "btn-primary" : "btn-secondary"
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
            {f === "pending" && pendingCount > 0 && (
              <span className="ml-1 bg-warning/30 text-warning px-1.5 py-0.5 rounded-full text-xs">
                {pendingCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          message={`No ${filter === "all" ? "" : filter} approvals`}
          description="Approvals will appear here when agents request authorization for actions."
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((approval) => (
            <div key={approval.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-text">{approval.action_type}</h3>
                    <StatusBadge status={approval.status} />
                  </div>
                  {approval.description && (
                    <p className="text-sm text-text-muted">{approval.description}</p>
                  )}
                  <div className="flex gap-4 mt-2 text-xs text-text-dim">
                    {approval.dollar_amount && (
                      <span className="text-warning font-medium">
                        ${approval.dollar_amount.toLocaleString()}
                      </span>
                    )}
                    <span>Created {new Date(approval.created_at).toLocaleString()}</span>
                    {approval.resolved_at && (
                      <span>Resolved {new Date(approval.resolved_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>

                {approval.status === "pending" && (
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleApprove(approval.id)}
                      disabled={processing === approval.id}
                      className="btn-success text-xs"
                    >
                      ✓ Approve
                    </button>
                    <button
                      onClick={() => handleReject(approval.id)}
                      disabled={processing === approval.id}
                      className="btn-danger text-xs"
                    >
                      ✕ Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
