"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";

interface Opportunity {
  id: string;
  title: string;
  description?: string;
  stage: string;
  value?: number;
  source?: string;
  contact_name?: string;
  business_id?: string;
  created_at: string;
}

const STAGES = ["new", "qualified", "proposal", "negotiation", "won", "lost"];

const STAGE_LABELS: Record<string, string> = {
  new: "New",
  qualified: "Qualified",
  proposal: "Proposal",
  negotiation: "Negotiation",
  won: "Won",
  lost: "Lost",
};

const STAGE_COLORS: Record<string, string> = {
  new: "bg-accent/20 text-accent",
  qualified: "bg-accent/20 text-accent",
  proposal: "bg-warning/20 text-warning",
  negotiation: "bg-warning/20 text-warning",
  won: "bg-success/20 text-success",
  lost: "bg-danger/20 text-danger",
};

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", value: "", contact_name: "" });
  const [submitting, setSubmitting] = useState(false);

  async function loadOpportunities() {
    setLoading(true);
    try {
      const data = await api.get<Opportunity[]>("/opportunities");
      setOpportunities(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load opportunities");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOpportunities();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/opportunities", {
        title: form.title,
        description: form.description || null,
        value: form.value ? parseFloat(form.value) : null,
        contact_name: form.contact_name || null,
        stage: "new",
      });
      setForm({ title: "", description: "", value: "", contact_name: "" });
      setShowCreate(false);
      loadOpportunities();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create opportunity");
    } finally {
      setSubmitting(false);
    }
  }

  const totalValue = opportunities.reduce((sum, o) => sum + (o.value || 0), 0);
  const wonValue = opportunities.filter((o) => o.stage === "won").reduce((sum, o) => sum + (o.value || 0), 0);

  // Group by stage
  const byStage = STAGES.reduce(
    (acc, stage) => {
      acc[stage] = opportunities.filter((o) => o.stage === stage);
      return acc;
    },
    {} as Record<string, Opportunity[]>
  );

  return (
    <div className="p-4 md:p-6 max-w-7xl">
      <PageHeader
        title="Opportunities"
        description={`${opportunities.length} deals · Total: $${totalValue.toLocaleString()} · Won: $${wonValue.toLocaleString()}`}
        actions={
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="btn-primary"
          >
            {showCreate ? "Cancel" : "+ New Opportunity"}
          </button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadOpportunities} />
        </div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold text-text">New Opportunity</h2>
          <div>
            <label className="label">Title *</label>
            <input
              className="input"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Acme Corp Roofing Contract"
              required
            />
          </div>
          <div>
            <label className="label">Contact Name</label>
            <input
              className="input"
              value={form.contact_name}
              onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
              placeholder="John Smith"
            />
          </div>
          <div>
            <label className="label">Estimated Value ($)</label>
            <input
              className="input"
              type="number"
              value={form.value}
              onChange={(e) => setForm({ ...form, value: e.target.value })}
              placeholder="50000"
            />
          </div>
          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Brief description"
            />
          </div>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Creating..." : "Create Opportunity"}
          </button>
        </form>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : opportunities.length === 0 ? (
        <EmptyState
          message="No opportunities tracked"
          description="Add opportunities to track your sales pipeline."
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              + Add Opportunity
            </button>
          }
        />
      ) : (
        /* Kanban Board */
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => (
            <div key={stage} className="kanban-column flex-shrink-0 w-64">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`badge ${STAGE_COLORS[stage]}`}>{STAGE_LABELS[stage]}</span>
                </div>
                <span className="text-xs text-text-dim">{byStage[stage].length}</span>
              </div>
              <div className="space-y-2">
                {byStage[stage].map((opp) => (
                  <div key={opp.id} className="bg-bg border border-bg-border rounded-lg p-3 hover:border-accent/30 transition-colors cursor-pointer">
                    <p className="text-sm font-medium text-text mb-1">{opp.title}</p>
                    {opp.contact_name && (
                      <p className="text-xs text-text-muted">{opp.contact_name}</p>
                    )}
                    {opp.value && (
                      <p className="text-sm font-medium text-success mt-2">
                        ${opp.value.toLocaleString()}
                      </p>
                    )}
                    <p className="text-xs text-text-dim mt-1">
                      {new Date(opp.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
