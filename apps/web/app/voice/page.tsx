"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";

interface VoiceCall {
  id: string;
  caller_number?: string;
  recipient_number?: string;
  direction: string;
  status: string;
  duration_seconds?: number;
  summary?: string;
  created_at: string;
}

interface VoiceSummary {
  id: string;
  call_id?: string;
  summary: string;
  key_points?: string[];
  action_items?: string[];
  created_at: string;
}

export default function VoicePage() {
  const [calls, setCalls] = useState<VoiceCall[]>([]);
  const [summaries, setSummaries] = useState<VoiceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"calls" | "summaries">("calls");

  async function loadData() {
    setLoading(true);
    try {
      const [c, s] = await Promise.all([
        api.get<VoiceCall[]>("/voice/list"),
        api.get<VoiceSummary[]>("/voice/summaries").catch(() => [] as VoiceSummary[]),
      ]);
      setCalls(c);
      setSummaries(s);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load voice data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function formatDuration(seconds: number | undefined) {
    if (!seconds) return "—";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  }

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="Voice"
        description="Call records and AI-generated summaries"
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadData} />
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-bg-border mb-6">
        {(["calls", "summaries"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-accent text-accent"
                : "border-transparent text-text-muted hover:text-text"
            }`}
          >
            {tab === "calls" ? `Calls (${calls.length})` : `Summaries (${summaries.length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : activeTab === "calls" ? (
        calls.length === 0 ? (
          <EmptyState
            message="No calls recorded"
            description="Voice calls will appear here when agents handle phone communications."
          />
        ) : (
          <div className="space-y-3">
            {calls.map((call) => (
              <div key={call.id} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`badge ${call.direction === "inbound" ? "bg-accent/20 text-accent" : "bg-bg-border text-text-dim"}`}>
                        {call.direction}
                      </span>
                      <StatusBadge status={call.status} />
                    </div>
                    <p className="text-sm text-text">
                      {call.caller_number || "Unknown"} → {call.recipient_number || "Unknown"}
                    </p>
                    <div className="flex gap-4 mt-2 text-xs text-text-dim">
                      <span>Duration: {formatDuration(call.duration_seconds)}</span>
                      <span>{new Date(call.created_at).toLocaleString()}</span>
                    </div>
                    {call.summary && (
                      <p className="text-sm text-text-muted mt-2 italic">"{call.summary}"</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      ) : summaries.length === 0 ? (
        <EmptyState
          message="No summaries available"
          description="AI-generated call summaries will appear here."
        />
      ) : (
        <div className="space-y-4">
          {summaries.map((summary) => (
            <div key={summary.id} className="card">
              <p className="text-sm text-text mb-3">{summary.summary}</p>
              {summary.key_points && summary.key_points.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs font-medium text-text-muted mb-1">Key Points:</p>
                  <ul className="list-disc list-inside text-sm text-text-muted space-y-1">
                    {summary.key_points.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}
              {summary.action_items && summary.action_items.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs font-medium text-text-muted mb-1">Action Items:</p>
                  <ul className="list-disc list-inside text-sm text-text-muted space-y-1">
                    {summary.action_items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="text-xs text-text-dim mt-2">
                {new Date(summary.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
