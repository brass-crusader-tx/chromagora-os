"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";

interface LedgerEntry {
  id: string;
  action: string;
  actor: string;
  agent_id?: string;
  business_id?: string;
  dollar_impact?: number | null;
  status: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export default function LedgerPage() {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  async function loadLedger() {
    setLoading(true);
    try {
      const data = await api.get<LedgerEntry[]>("/ledger");
      setEntries(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load ledger");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLedger();
  }, []);

  const filtered = entries.filter((entry) => {
    const matchesSearch =
      !search ||
      entry.action.toLowerCase().includes(search.toLowerCase()) ||
      entry.actor.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || entry.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const uniqueStatuses = [...new Set(entries.map((e) => e.status))];
  const totalImpact = entries.reduce((sum, e) => sum + (e.dollar_impact || 0), 0);

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="Action Ledger"
        description={`${entries.length} entries · Total impact: $${totalImpact.toLocaleString()}`}
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadLedger} />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <input
          className="input flex-1"
          placeholder="Search by action or actor..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input w-auto"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Statuses</option>
          {uniqueStatuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          message="No ledger entries found"
          description="Actions will be recorded here as agents execute tasks."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-bg-border">
                <th className="text-left py-3 px-4 text-text-dim font-medium">Action</th>
                <th className="text-left py-3 px-4 text-text-dim font-medium">Actor</th>
                <th className="text-left py-3 px-4 text-text-dim font-medium">Status</th>
                <th className="text-right py-3 px-4 text-text-dim font-medium">Impact</th>
                <th className="text-right py-3 px-4 text-text-dim font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry) => (
                <tr key={entry.id} className="border-b border-bg-border/50 hover:bg-bg-elevated">
                  <td className="py-3 px-4 text-text">{entry.action}</td>
                  <td className="py-3 px-4 text-text-muted">{entry.actor}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={entry.status} />
                  </td>
                  <td className="py-3 px-4 text-right">
                    {typeof entry.dollar_impact === "number" ? (
                      <span className={entry.dollar_impact >= 0 ? "text-success" : "text-danger"}>
                        {entry.dollar_impact >= 0 ? "+" : ""}${entry.dollar_impact.toLocaleString()}
                      </span>
                    ) : (
                      <span className="text-text-dim">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right text-text-dim">
                    {new Date(entry.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
