"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import StatCard from "@/components/StatCard";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";

interface Business {
  id: string;
  name: string;
}

interface Agent {
  id: string;
  name: string;
  status: string;
}

interface Approval {
  id: string;
  action_type: string;
  status: string;
  created_at: string;
}

interface LedgerEntry {
  id: string;
  action: string;
  actor: string;
  created_at: string;
  dollar_impact?: number | null;
}

export default function DashboardPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [biz, agt, appr, ledg] = await Promise.all([
        api.get<Business[]>("/businesses"),
        api.get<Agent[]>("/agents"),
        api.get<Approval[]>("/approvals"),
        api.get<LedgerEntry[]>("/ledger"),
      ]);
      setBusinesses(biz);
      setAgents(agt);
      setApprovals(appr);
      setLedger(ledg);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const pendingApprovals = approvals.filter((a) => a.status === "pending");
  const activeAgents = agents.filter((a) => a.status === "active");

  if (loading) return <LoadingSpinner message="Loading dashboard..." />;
  if (error) return <div className="p-6"><ErrorBanner message={error} onRetry={loadData} /></div>;

  return (
    <div className="p-4 md:p-6 max-w-7xl">
      <PageHeader
        title="Dashboard"
        description="Overview of your Chromagora OS operations"
      />

    {/* Stats Grid */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <StatCard label="Businesses" value={businesses.length} icon="◈" accent />
      <StatCard label="Active Agents" value={activeAgents.length} icon="◇" />
      <StatCard label="Pending Approvals" value={pendingApprovals.length} icon="✓" />
      <StatCard label="Ledger Entries" value={ledger.length} icon="≡" />
    </div>

    <div className="grid md:grid-cols-2 gap-6">
      {/* Recent Approvals */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-text">Recent Approvals</h2>
          <Link href="/approvals" className="text-xs text-accent hover:underline">
            View all →
          </Link>
        </div>
        {pendingApprovals.length === 0 ? (
          <p className="text-sm text-text-muted">No pending approvals</p>
        ) : (
          <div className="space-y-2">
            {pendingApprovals.slice(0, 5).map((a) => (
              <div key={a.id} className="flex items-center justify-between py-2 border-b border-bg-border/50 last:border-0">
                <div>
                  <p className="text-sm text-text">{a.action_type}</p>
                  <p className="text-xs text-text-dim">{new Date(a.created_at).toLocaleDateString()}</p>
                </div>
                <StatusBadge status={a.status} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Ledger */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-text">Recent Activity</h2>
          <Link href="/ledger" className="text-xs text-accent hover:underline">
            View all →
          </Link>
        </div>
        {ledger.length === 0 ? (
          <p className="text-sm text-text-muted">No recent activity</p>
        ) : (
          <div className="space-y-2">
            {ledger.slice(0, 5).map((entry) => (
              <div key={entry.id} className="flex items-center justify-between py-2 border-b border-bg-border/50 last:border-0">
                <div>
                  <p className="text-sm text-text">{entry.action}</p>
                  <p className="text-xs text-text-dim">{entry.actor}</p>
                </div>
                <div className="text-right">
                  {typeof entry.dollar_impact === "number" && (
                    <p className="text-sm text-text">${entry.dollar_impact.toLocaleString()}</p>
                  )}
                  <p className="text-xs text-text-dim">{new Date(entry.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agents Overview */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-text">Agents</h2>
          <Link href="/agents" className="text-xs text-accent hover:underline">
            View all →
          </Link>
        </div>
        {agents.length === 0 ? (
          <p className="text-sm text-text-muted">No agents registered</p>
        ) : (
          <div className="space-y-2">
            {agents.slice(0, 5).map((agent) => (
              <div key={agent.id} className="flex items-center justify-between py-2 border-b border-bg-border/50 last:border-0">
                <p className="text-sm text-text">{agent.name}</p>
                <StatusBadge status={agent.status} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Links */}
      <div className="card">
        <h2 className="font-semibold text-text mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-2">
          <Link href="/businesses" className="btn-secondary text-xs justify-start">
            ◈ Businesses
          </Link>
          <Link href="/agents" className="btn-secondary text-xs justify-start">
            ◇ Agents
          </Link>
          <Link href="/opportunities" className="btn-secondary text-xs justify-start">
            ◎ Opportunities
          </Link>
          <Link href="/workflows" className="btn-secondary text-xs justify-start">
            ⟳ Workflows
          </Link>
          <Link href="/voice" className="btn-secondary text-xs justify-start">
            ♫ Voice
          </Link>
          <Link href="/crm" className="btn-secondary text-xs justify-start">
            ☎ CRM
          </Link>
        </div>
      </div>
    </div>
  </div>
  );
}
