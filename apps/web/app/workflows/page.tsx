"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";

interface Workflow {
  id: string;
  name: string;
  description?: string;
  status: string;
  steps?: number;
  last_run_at?: string;
  created_at: string;
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [submitting, setSubmitting] = useState(false);

  async function loadWorkflows() {
    setLoading(true);
    try {
      const data = await api.get<Workflow[]>("/workflows");
      setWorkflows(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load workflows");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkflows();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/workflows", {
        name: form.name,
        description: form.description || null,
        status: "draft",
      });
      setForm({ name: "", description: "" });
      setShowCreate(false);
      loadWorkflows();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create workflow");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="Workflows"
        description="Automated multi-step processes and run status"
        actions={
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="btn-primary"
          >
            {showCreate ? "Cancel" : "+ New Workflow"}
          </button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadWorkflows} />
        </div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold text-text">New Workflow</h2>
          <div>
            <label className="label">Name *</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Client Onboarding"
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What this workflow does"
            />
          </div>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Creating..." : "Create Workflow"}
          </button>
        </form>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : workflows.length === 0 ? (
        <EmptyState
          message="No workflows configured"
          description="Create workflows to automate multi-step processes."
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              + Create Workflow
            </button>
          }
        />
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {workflows.map((wf) => (
            <div key={wf.id} className="card hover:border-accent/30 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-medium text-text">{wf.name}</h3>
                <StatusBadge status={wf.status} />
              </div>
              {wf.description && (
                <p className="text-sm text-text-muted mb-3">{wf.description}</p>
              )}
              <div className="flex gap-4 text-xs text-text-dim">
                {wf.steps !== undefined && <span>{wf.steps} steps</span>}
                {wf.last_run_at && (
                  <span>Last run: {new Date(wf.last_run_at).toLocaleDateString()}</span>
                )}
                <span>Created: {new Date(wf.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex gap-2 mt-4">
                <button className="btn-secondary text-xs">View</button>
                <button className="btn-primary text-xs">Run</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
