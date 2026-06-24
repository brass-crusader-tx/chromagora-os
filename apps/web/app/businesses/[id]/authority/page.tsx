"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiBaseUrl } from "@/lib/supabase";
import clsx from "clsx";

interface AuthorityEnvelope {
  id: string;
  business_id: string;
  name: string;
  description: string | null;
  agent_scope: string | null;
  action_type_scope: string | null;
  autonomy_level: number;
  max_dollar_exposure: number | null;
  requires_approval: boolean;
  is_active: boolean;
  created_at: string;
}

const AUTONOMY_LEVELS = [
  { value: 0, label: "Observe", desc: "Read-only, no actions" },
  { value: 1, label: "Analyze", desc: "Pattern detection, classification" },
  { value: 2, label: "Draft", desc: "Generate content, no sending" },
  { value: 3, label: "Internal Action", desc: "DB writes, internal ops" },
  { value: 4, label: "Low-Risk External", desc: "Email, bounded messages" },
  { value: 5, label: "Bounded Negotiation", desc: "Within defined limits" },
  { value: 6, label: "Binding Execution", desc: "Always requires approval" },
];

export default function AuthorityPage() {
  const params = useParams();
  const router = useRouter();
  const businessId = params.id as string;

  const [envelopes, setEnvelopes] = useState<AuthorityEnvelope[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);

  // Form state
  const [form, setForm] = useState({
    name: "",
    description: "",
    agent_scope: "",
    action_type_scope: "",
    autonomy_level: 0,
    max_dollar_exposure: "",
    requires_approval: true,
  });

  async function loadEnvelopes() {
    try {
      const res = await fetch(
        `${apiBaseUrl}/businesses/${businessId}/authority`
      );
      if (res.ok) {
        setEnvelopes(await res.json());
      }
    } catch {
      // API may not be running
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEnvelopes();
  }, [businessId]);

  function resetForm() {
    setForm({
      name: "",
      description: "",
      agent_scope: "",
      action_type_scope: "",
      autonomy_level: 0,
      max_dollar_exposure: "",
      requires_approval: true,
    });
    setEditId(null);
    setShowCreate(false);
  }

  function startEdit(env: AuthorityEnvelope) {
    setForm({
      name: env.name,
      description: env.description || "",
      agent_scope: env.agent_scope || "",
      action_type_scope: env.action_type_scope || "",
      autonomy_level: env.autonomy_level,
      max_dollar_exposure: env.max_dollar_exposure?.toString() || "",
      requires_approval: env.requires_approval,
    });
    setEditId(env.id);
    setShowCreate(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      ...form,
      business_id: businessId,
      agent_scope: form.agent_scope || null,
      action_type_scope: form.action_type_scope || null,
      max_dollar_exposure: form.max_dollar_exposure
        ? parseFloat(form.max_dollar_exposure)
        : null,
    };

    const url = editId
      ? `${apiBaseUrl}/businesses/${businessId}/authority/${editId}`
      : `${apiBaseUrl}/businesses/${businessId}/authority`;
    const method = editId ? "PATCH" : "POST";

    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        resetForm();
        loadEnvelopes();
      }
    } catch {
      // API may not be running
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Deactivate this envelope?")) return;
    try {
      await fetch(
        `${apiBaseUrl}/businesses/${businessId}/authority/${id}`,
        { method: "DELETE" }
      );
      loadEnvelopes();
    } catch {
      // API may not be running
    }
  }

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text">
            Authority Envelopes
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Define what agents can do for this business. Higher autonomy = more
            responsibility.
          </p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowCreate(true);
          }}
          className="btn-primary"
        >
          + New Envelope
        </button>
      </div>

      {/* Create / Edit form */}
      {showCreate && (
        <form onSubmit={handleSubmit} className="card mb-6 space-y-4">
          <h2 className="text-lg font-semibold">
            {editId ? "Edit Envelope" : "New Envelope"}
          </h2>

          <div>
            <label className="label">Name</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) =>
                setForm({ ...form, name: e.target.value })
              }
              placeholder="e.g. Roofing Sales Agent"
              required
            />
          </div>

          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="What this envelope governs"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Agent Scope</label>
              <input
                className="input"
                value={form.agent_scope}
                onChange={(e) =>
                  setForm({ ...form, agent_scope: e.target.value })
                }
                placeholder="e.g. sales_agent (null = all)"
              />
            </div>
            <div>
              <label className="label">Action Type Scope</label>
              <input
                className="input"
                value={form.action_type_scope}
                onChange={(e) =>
                  setForm({ ...form, action_type_scope: e.target.value })
                }
                placeholder="e.g. send_email (null = all)"
              />
            </div>
          </div>

          <div>
            <label className="label">
              Autonomy Level ({form.autonomy_level}) —{" "}
              {AUTONOMY_LEVELS[form.autonomy_level]?.label}
            </label>
            <input
              type="range"
              min={0}
              max={6}
              value={form.autonomy_level}
              onChange={(e) =>
                setForm({
                  ...form,
                  autonomy_level: parseInt(e.target.value),
                })
              }
              className="w-full accent-accent"
            />
            <p className="text-xs text-text-dim mt-1">
              {AUTONOMY_LEVELS[form.autonomy_level]?.desc}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Max Dollar Exposure</label>
              <input
                className="input"
                type="number"
                value={form.max_dollar_exposure}
                onChange={(e) =>
                  setForm({ ...form, max_dollar_exposure: e.target.value })
                }
                placeholder="No limit"
              />
            </div>
            <div className="flex items-end pb-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.requires_approval}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      requires_approval: e.target.checked,
                    })
                  }
                  className="w-4 h-4 accent-accent"
                />
                <span className="text-sm text-text-muted">
                  Requires approval
                </span>
              </label>
            </div>
          </div>

          <div className="flex gap-2">
            <button type="submit" className="btn-primary">
              {editId ? "Update" : "Create"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Envelope list */}
      {loading ? (
        <p className="text-text-muted">Loading...</p>
      ) : envelopes.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-text-muted">
            No authority envelopes configured.
          </p>
          <p className="text-xs text-text-dim mt-2">
            Create one to define what agents can do for this business.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {envelopes.map((env) => (
            <div
              key={env.id}
              className={clsx(
                "card flex items-center justify-between",
                !env.is_active && "opacity-50"
              )}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-text">{env.name}</h3>
                  <span
                    className={clsx(
                      "badge",
                      env.is_active
                        ? "bg-success/20 text-success"
                        : "bg-bg-border text-text-dim"
                    )}
                  >
                    {env.is_active ? "Active" : "Inactive"}
                  </span>
                  <span className="badge bg-accent/20 text-accent">
                    L{env.autonomy_level}
                  </span>
                </div>
                {env.description && (
                  <p className="text-sm text-text-muted mt-1 truncate">
                    {env.description}
                  </p>
                )}
                <div className="flex gap-4 mt-2 text-xs text-text-dim">
                  {env.agent_scope && <span>Agent: {env.agent_scope}</span>}
                  {env.action_type_scope && (
                    <span>Action: {env.action_type_scope}</span>
                  )}
                  {env.max_dollar_exposure && (
                    <span>Max: ${env.max_dollar_exposure.toLocaleString()}</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => startEdit(env)}
                  className="btn-secondary text-xs"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(env.id)}
                  className="btn-danger text-xs"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
