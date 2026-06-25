"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import { api } from "@/lib/api";

interface Business {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [submitting, setSubmitting] = useState(false);

  async function loadBusinesses() {
    setLoading(true);
    try {
      const data = await api.get<Business[]>("/businesses");
      setBusinesses(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load businesses");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBusinesses();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/businesses", {
        name: form.name,
        description: form.description || null,
      });
      setForm({ name: "", description: "" });
      setShowCreate(false);
      loadBusinesses();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create business");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl">
      <PageHeader
        title="Businesses"
        description="Manage your client businesses and their agent configurations"
        actions={
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="btn-primary"
          >
            {showCreate ? "Cancel" : "+ New Business"}
          </button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadBusinesses} />
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold text-text">New Business</h2>
          <div>
            <label className="label">Name *</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Acme Roofing"
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Optional description"
            />
          </div>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Creating..." : "Create Business"}
          </button>
        </form>
      )}

      {/* Business List */}
      {loading ? (
        <LoadingSpinner />
      ) : businesses.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-text-muted">No businesses found.</p>
          <p className="text-xs text-text-dim mt-2">
            Create your first business to get started.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {businesses.map((biz) => (
            <div key={biz.id} className="card hover:border-accent/30 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-text">{biz.name}</h3>
                  {biz.description && (
                    <p className="text-sm text-text-muted mt-1 truncate">{biz.description}</p>
                  )}
                  <p className="text-xs text-text-dim mt-1">
                    Created {new Date(biz.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-2 ml-4">
                  <Link href={`/businesses/${biz.id}`} className="btn-secondary text-xs">
                    Overview
                  </Link>
                  <Link href={`/businesses/${biz.id}/authority`} className="btn-secondary text-xs">
                    Authority
                  </Link>
                  <Link href={`/businesses/${biz.id}/tools`} className="btn-secondary text-xs">
                    Tools
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
