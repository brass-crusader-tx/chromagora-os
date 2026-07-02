"use client";

import { useMemo, useState } from "react";
import PageHeader from "@/components/PageHeader";
import ErrorBanner from "@/components/ErrorBanner";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";

interface StaleQuoteSimulationResult {
  status: string;
  event_id?: string | null;
  agent_result?: Record<string, unknown>;
}

function isoDaysAgo(days: number) {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 16);
}

function toApiTimestamp(value: string) {
  return new Date(value).toISOString();
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "None";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export default function StaleQuoteDemoPage() {
  const defaultSentAt = useMemo(() => isoDaysAgo(6), []);
  const [form, setForm] = useState({
    business_id: "",
    customer_name: "Morgan Lee",
    customer_contact: "morgan@example.com",
    service_type: "roof repair",
    quote_amount: "4200",
    quote_sent_at: defaultSentAt,
    quote_id: "",
    last_contact_at: "",
  });
  const [result, setResult] = useState<StaleQuoteSimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function runSimulation(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        business_id: form.business_id,
        customer_name: form.customer_name,
        customer_contact: form.customer_contact,
        service_type: form.service_type,
        quote_amount: form.quote_amount ? Number(form.quote_amount) : null,
        quote_sent_at: toApiTimestamp(form.quote_sent_at),
        quote_id: form.quote_id || null,
        last_contact_at: form.last_contact_at ? toApiTimestamp(form.last_contact_at) : null,
      };
      const data = await api.post<StaleQuoteSimulationResult>("/demo/stale-quote-simulation", payload);
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to run stale quote simulation");
    } finally {
      setSubmitting(false);
    }
  }

  const agentResult = result?.agent_result ?? {};
  const detailRows: Array<[string, unknown]> = [
    ["Event ID", result?.event_id],
    ["Agent Status", agentResult.status],
    ["Agent Run ID", agentResult.agent_run_id],
    ["Proposal ID", agentResult.proposal_id],
    ["Action Type", agentResult.action_type],
    ["Requires Approval", agentResult.requires_approval],
    ["Trace ID", agentResult.trace_id],
  ];

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="Stale Quote Demo"
        description="Run the quote.stale loop through event emission, Sales Agent, Context Packet, Policy, Tool Broker, and returned IDs"
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={() => setError(null)} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
        <form onSubmit={runSimulation} className="card space-y-4">
          <div>
            <label className="label">Business ID *</label>
            <input
              className="input"
              value={form.business_id}
              onChange={(e) => setForm({ ...form, business_id: e.target.value })}
              placeholder="UUID"
              required
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
            <div>
              <label className="label">Customer *</label>
              <input
                className="input"
                value={form.customer_name}
                onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Contact *</label>
              <input
                className="input"
                value={form.customer_contact}
                onChange={(e) => setForm({ ...form, customer_contact: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
            <div>
              <label className="label">Service Type *</label>
              <input
                className="input"
                value={form.service_type}
                onChange={(e) => setForm({ ...form, service_type: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Quote Amount</label>
              <input
                className="input"
                type="number"
                min="0"
                step="0.01"
                value={form.quote_amount}
                onChange={(e) => setForm({ ...form, quote_amount: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="label">Quote Sent At *</label>
            <input
              className="input"
              type="datetime-local"
              value={form.quote_sent_at}
              onChange={(e) => setForm({ ...form, quote_sent_at: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="label">Quote ID</label>
            <input
              className="input"
              value={form.quote_id}
              onChange={(e) => setForm({ ...form, quote_id: e.target.value })}
              placeholder="Optional existing quote ID"
            />
          </div>

          <div>
            <label className="label">Last Contact At</label>
            <input
              className="input"
              type="datetime-local"
              value={form.last_contact_at}
              onChange={(e) => setForm({ ...form, last_contact_at: e.target.value })}
            />
          </div>

          <button type="submit" className="btn-primary w-full" disabled={submitting}>
            {submitting ? "Running..." : "Run Simulation"}
          </button>
        </form>

        <div className="space-y-4">
          <div className="card">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <h2 className="font-semibold text-text">Simulation Result</h2>
                <p className="text-sm text-text-muted mt-1">
                  Returned identifiers are enough to inspect the event, agent run, proposal, approvals, ledger, and trace records.
                </p>
              </div>
              {result && <StatusBadge status={result.status} />}
            </div>

            {!result ? (
              <div className="rounded-md border border-dashed border-bg-border p-6 text-sm text-text-dim">
                Run a simulation to see the end-to-end output.
              </div>
            ) : (
              <dl className="grid gap-3 sm:grid-cols-2">
                {detailRows.map(([label, value]) => (
                  <div key={label} className="rounded-md bg-bg-elevated p-3 min-w-0">
                    <dt className="text-xs font-medium uppercase text-text-dim">{label}</dt>
                    <dd className="mt-1 break-words text-sm text-text">{formatValue(value)}</dd>
                  </div>
                ))}
              </dl>
            )}
          </div>

          {result && (
            <div className="card">
              <h2 className="font-semibold text-text mb-3">Raw Agent Output</h2>
              <pre className="max-h-[420px] overflow-auto rounded-md bg-bg p-3 text-xs text-text-muted">
                {JSON.stringify(agentResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
