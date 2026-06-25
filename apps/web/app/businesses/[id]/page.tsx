"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";
import clsx from "clsx";

interface Business {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

interface AuthorityEnvelope {
  id: string;
  name: string;
  autonomy_level: number;
  is_active: boolean;
}

interface ToolPermission {
  id: string;
  tool_definitions: { name: string };
  is_enabled: boolean;
  max_autonomy_level: number;
}

interface AutonomyScorecard {
  business_id: string;
  total_envelopes: number;
  avg_autonomy: number;
  max_autonomy: number;
  active_tools: number;
  total_tools: number;
}

const TABS = ["Overview", "Authority", "Tools", "Autonomy"] as const;
type Tab = (typeof TABS)[number];

export default function BusinessDetailPage() {
  const params = useParams();
  const businessId = params.id as string;
  const [activeTab, setActiveTab] = useState<Tab>("Overview");

  const [business, setBusiness] = useState<Business | null>(null);
  const [envelopes, setEnvelopes] = useState<AuthorityEnvelope[]>([]);
  const [tools, setTools] = useState<ToolPermission[]>([]);
  const [scorecard, setScorecard] = useState<AutonomyScorecard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const biz = await api.get<Business>(`/businesses/${businessId}`);
        setBusiness(biz);

        const [env, perm, score] = await Promise.all([
          api.get<AuthorityEnvelope[]>(`/businesses/${businessId}/authority`),
          api.get<ToolPermission[]>(`/businesses/${businessId}/tools`),
          api.get<AutonomyScorecard>(`/businesses/${businessId}/autonomy/scorecard`).catch(() => null),
        ]);
        setEnvelopes(env);
        setTools(perm);
        if (score) setScorecard(score);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load business");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [businessId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="p-6"><ErrorBanner message={error} /></div>;
  if (!business) return <div className="p-6"><ErrorBanner message="Business not found" /></div>;

  const activeEnvelopes = envelopes.filter((e) => e.is_active);
  const enabledTools = tools.filter((t) => t.is_enabled);

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <div className="mb-4">
        <Link href="/businesses" className="text-xs text-accent hover:underline">
          ← Back to Businesses
        </Link>
      </div>

      <PageHeader
        title={business.name}
        description={business.description || `Business ID: ${businessId.slice(0, 8)}...`}
      />

      {/* Tabs */}
      <div className="flex border-b border-bg-border mb-6 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
              activeTab === tab
                ? "border-accent text-accent"
                : "border-transparent text-text-muted hover:text-text"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "Overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Active Envelopes" value={activeEnvelopes.length} accent />
            <StatCard label="Active Tools" value={enabledTools.length} />
            <StatCard label="Created" value={new Date(business.created_at).toLocaleDateString()} />
          </div>
          <div className="card">
            <h3 className="font-semibold text-text mb-3">Recent Authority Envelopes</h3>
            {activeEnvelopes.length === 0 ? (
              <p className="text-sm text-text-muted">No active envelopes.</p>
            ) : (
              <div className="space-y-2">
                {activeEnvelopes.slice(0, 3).map((env) => (
                  <div key={env.id} className="flex items-center justify-between py-2 border-b border-bg-border/50">
                    <span className="text-sm text-text">{env.name}</span>
                    <StatusBadge status={env.is_active ? "active" : "inactive"} />
                  </div>
                ))}
              </div>
            )}
            <Link href={`/businesses/${businessId}/authority`} className="text-xs text-accent hover:underline mt-3 inline-block">
              Manage Authority →
            </Link>
          </div>
        </div>
      )}

      {activeTab === "Authority" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-text-muted">
              Authority envelopes define what agents can do for this business.
            </p>
            <Link href={`/businesses/${businessId}/authority`} className="btn-primary text-xs">
              Manage Envelopes
            </Link>
          </div>
          {envelopes.length === 0 ? (
            <div className="card text-center py-8">
              <p className="text-text-muted">No authority envelopes configured.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {envelopes.map((env) => (
                <div key={env.id} className={clsx("card", !env.is_active && "opacity-50")}>
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-text">{env.name}</span>
                    <StatusBadge status={env.is_active ? "active" : "inactive"} />
                    <span className="badge bg-accent/20 text-accent">L{env.autonomy_level}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "Tools" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-text-muted">
              Tool permissions for this business.
            </p>
            <Link href={`/businesses/${businessId}/tools`} className="btn-primary text-xs">
              Manage Tools
            </Link>
          </div>
          {tools.length === 0 ? (
            <div className="card text-center py-8">
              <p className="text-text-muted">No tool permissions configured.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {tools.map((perm) => (
                <div key={perm.id} className={clsx("card flex items-center justify-between", !perm.is_enabled && "opacity-50")}>
                  <span className="text-text">{perm.tool_definitions?.name || perm.id.slice(0, 8)}</span>
                  <StatusBadge status={perm.is_enabled ? "active" : "inactive"} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "Autonomy" && (
        <div className="space-y-6">
          {scorecard ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <StatCard label="Total Envelopes" value={scorecard.total_envelopes} />
                <StatCard label="Avg Autonomy" value={scorecard.avg_autonomy.toFixed(1)} accent />
                <StatCard label="Max Autonomy" value={scorecard.max_autonomy} />
                <StatCard label="Active Tools" value={scorecard.active_tools} />
                <StatCard label="Total Tools" value={scorecard.total_tools} />
              </div>
              <div className="card">
                <h3 className="font-semibold text-text mb-3">Autonomy Distribution</h3>
                <div className="space-y-2">
                  {Array.from({ length: 7 }, (_, i) => {
                    const count = envelopes.filter((e) => e.autonomy_level === i).length;
                    const pct = envelopes.length > 0 ? (count / envelopes.length) * 100 : 0;
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-xs text-text-dim w-8">L{i}</span>
                        <div className="flex-1 bg-bg rounded-full h-2">
                          <div
                            className="bg-accent rounded-full h-2 transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-text-dim w-6 text-right">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="card text-center py-8">
              <p className="text-text-muted">No autonomy data available.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
