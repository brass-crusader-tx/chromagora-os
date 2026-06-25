"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";

interface MemoryArtifact {
  id: string;
  name?: string;
  artifact_type?: string;
  content?: string;
  source?: string;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

export default function MemoryPage() {
  const [artifacts, setArtifacts] = useState<MemoryArtifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  async function loadArtifacts() {
    setLoading(true);
    try {
      const data = await api.get<MemoryArtifact[]>("/memory/artifacts");
      setArtifacts(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load memory artifacts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadArtifacts();
  }, []);

  const filtered = artifacts.filter((a) => {
    const matchesSearch =
      !search ||
      (a.name || "").toLowerCase().includes(search.toLowerCase()) ||
      (a.content || "").toLowerCase().includes(search.toLowerCase()) ||
      (a.tags || []).some((t) => t.toLowerCase().includes(search.toLowerCase()));
    const matchesType = typeFilter === "all" || a.artifact_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const uniqueTypes = [...new Set(artifacts.map((a) => a.artifact_type).filter(Boolean))];

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="Memory"
        description={`${artifacts.length} artifacts stored in agent memory`}
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadArtifacts} />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <input
          className="input flex-1"
          placeholder="Search artifacts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input w-auto"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="all">All Types</option>
          {uniqueTypes.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          message="No memory artifacts found"
          description="Agents store knowledge and context here during operations."
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((artifact) => (
            <div key={artifact.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-text">
                      {artifact.name || artifact.id.slice(0, 8)}
                    </h3>
                    {artifact.artifact_type && (
                      <StatusBadge status={artifact.artifact_type} />
                    )}
                    {artifact.source && (
                      <span className="text-xs text-text-dim">from {artifact.source}</span>
                    )}
                  </div>
                  {artifact.tags && artifact.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap mb-2">
                      {artifact.tags.map((tag) => (
                        <span key={tag} className="badge bg-bg-elevated text-text-dim">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  {expanded === artifact.id && artifact.content && (
                    <div className="mt-3 p-3 bg-bg rounded-md">
                      <pre className="text-sm text-text-muted whitespace-pre-wrap font-mono">
                        {artifact.content}
                      </pre>
                    </div>
                  )}
                  <p className="text-xs text-text-dim mt-2">
                    {new Date(artifact.created_at).toLocaleString()}
                    {artifact.updated_at && ` · Updated ${new Date(artifact.updated_at).toLocaleString()}`}
                  </p>
                </div>
                {artifact.content && (
                  <button
                    onClick={() => setExpanded(expanded === artifact.id ? null : artifact.id)}
                    className="btn-secondary text-xs ml-4"
                  >
                    {expanded === artifact.id ? "Collapse" : "Expand"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
