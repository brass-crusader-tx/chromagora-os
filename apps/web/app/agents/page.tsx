"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";

interface Agent {
  id: string;
  name: string;
  description?: string;
  status: string;
  agent_type?: string;
  created_at: string;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", agent_type: "" });
  const [submitting, setSubmitting] = useState(false);

  async function loadAgents() {
    setLoading(true);
    try {
      const data = await api.get<Agent[]>("/agents");
      setAgents(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAgents();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/agents", {
        name: form.name,
        description: form.description || null,
        agent_type: form.agent_type || null,
        status: "active",
      });
      setForm({ name: "", description: "", agent_type: "" });
      setShowCreate(false);
      loadAgents();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create agent");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="Agents"
        description="Register and manage your AI agents"
        actions={
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="btn-primary"
          >
            {showCreate ? "Cancel" : "+ New Agent"}
          </button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadAgents} />
        </div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold text-text">New Agent</h2>
          <div>
            <label className="label">Name *</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Sales Assistant"
              required
            />
          </div>
          <div>
            <label className="label">Type</label>
            <input
              className="input"
              value={form.agent_type}
              onChange={(e) => setForm({ ...form, agent_type: e.target.value })}
              placeholder="e.g. sales_agent, support_bot"
            />
          </div>
          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What this agent does"
            />
          </div>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Creating..." : "Create Agent"}
          </button>
        </form>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : agents.length === 0 ? (
        <EmptyState
          message="No agents registered"
          description="Create your first agent to start automating operations."
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              + Create Agent
            </button>
          }
        />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <Link
              key={agent.id}
              href={`/agents/${agent.id}`}
              className="card hover:border-accent/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-sm text-accent font-bold">
                  {agent.name.charAt(0).toUpperCase()}
                </div>
                <StatusBadge status={agent.status} />
              </div>
              <h3 className="font-medium text-text">{agent.name}</h3>
              {agent.agent_type && (
                <p className="text-xs text-accent mt-1">{agent.agent_type}</p>
              )}
              {agent.description && (
                <p className="text-sm text-text-muted mt-2 line-clamp-2">{agent.description}</p>
              )}
              <p className="text-xs text-text-dim mt-3">
                Created {new Date(agent.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
