"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import StatCard from "@/components/StatCard";
import { api } from "@/lib/api";

interface Agent {
  id: string;
  name: string;
  description?: string;
  status: string;
  agent_type?: string;
  created_at: string;
}

interface RunRecord {
  id: string;
  agent_id: string;
  status: string;
  action: string;
  business_id?: string;
  created_at: string;
  completed_at?: string;
}

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const agt = await api.get<Agent>(`/agents/${agentId}`);
        setAgent(agt);
        // Try to get run history from ledger
        const ledger = await api.get<RunRecord[]>("/ledger").catch(() => [] as RunRecord[]);
        setRuns(ledger.filter((r) => r.agent_id === agentId).slice(0, 20));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load agent");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [agentId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="p-6"><ErrorBanner message={error} /></div>;
  if (!agent) return <div className="p-6"><ErrorBanner message="Agent not found" /></div>;

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <div className="mb-4">
        <Link href="/agents" className="text-xs text-accent hover:underline">
          ← Back to Agents
        </Link>
      </div>

      <PageHeader
        title={agent.name}
        description={agent.agent_type || "Agent"}
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Status" value={agent.status} accent />
        <StatCard label="Type" value={agent.agent_type || "—"} />
        <StatCard label="Total Runs" value={runs.length} />
        <StatCard label="Created" value={new Date(agent.created_at).toLocaleDateString()} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-text mb-3">Agent Details</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-text-muted">ID</span>
              <span className="text-text font-mono text-xs">{agent.id.slice(0, 8)}...</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Name</span>
              <span className="text-text">{agent.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Type</span>
              <span className="text-text">{agent.agent_type || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Status</span>
              <StatusBadge status={agent.status} />
            </div>
            {agent.description && (
              <div className="pt-2 border-t border-bg-border">
                <p className="text-text-muted mb-1">Description</p>
                <p className="text-text">{agent.description}</p>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-text mb-3">Run History</h3>
          {runs.length === 0 ? (
            <p className="text-sm text-text-muted">No run history available.</p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {runs.map((run) => (
                <div key={run.id} className="flex items-center justify-between py-2 border-b border-bg-border/50">
                  <div>
                    <p className="text-sm text-text">{run.action}</p>
                    <p className="text-xs text-text-dim">
                      {new Date(run.created_at).toLocaleString()}
                    </p>
                  </div>
                  <StatusBadge status={run.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
