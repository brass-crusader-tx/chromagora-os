"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorBanner from "@/components/ErrorBanner";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";

interface Contact {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  title?: string;
  notes?: string;
  tags?: string[];
  created_at: string;
}

export default function CRMPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    company: "",
    title: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");

  async function loadContacts() {
    setLoading(true);
    try {
      const data = await api.get<Contact[]>("/crm/contacts");
      setContacts(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load contacts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadContacts();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/crm/contacts", {
        name: form.name,
        email: form.email || null,
        phone: form.phone || null,
        company: form.company || null,
        title: form.title || null,
        notes: form.notes || null,
      });
      setForm({ name: "", email: "", phone: "", company: "", title: "", notes: "" });
      setShowCreate(false);
      loadContacts();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create contact");
    } finally {
      setSubmitting(false);
    }
  }

  const filtered = contacts.filter(
    (c) =>
      !search ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.company || "").toLowerCase().includes(search.toLowerCase()) ||
      (c.email || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4 md:p-6 max-w-6xl">
      <PageHeader
        title="CRM"
        description={`${contacts.length} contacts in your customer relationship management`}
        actions={
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="btn-primary"
          >
            {showCreate ? "Cancel" : "+ Add Contact"}
          </button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={loadContacts} />
        </div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold text-text">New Contact</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Name *</label>
              <input
                className="input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="John Smith"
                required
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="john@example.com"
              />
            </div>
            <div>
              <label className="label">Phone</label>
              <input
                className="input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+1 (555) 123-4567"
              />
            </div>
            <div>
              <label className="label">Company</label>
              <input
                className="input"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label className="label">Title</label>
              <input
                className="input"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="CEO"
              />
            </div>
            <div>
              <label className="label">Notes</label>
              <input
                className="input"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Optional notes"
              />
            </div>
          </div>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Adding..." : "Add Contact"}
          </button>
        </form>
      )}

      {/* Search */}
      <div className="mb-6">
        <input
          className="input max-w-md"
          placeholder="Search contacts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          message={search ? "No contacts match your search" : "No contacts yet"}
          description={search ? "Try a different search term." : "Add contacts to build your CRM."}
          action={
            !search && (
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                + Add Contact
              </button>
            )
          }
        />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((contact) => (
            <div key={contact.id} className="card hover:border-accent/30 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center text-sm text-accent font-bold flex-shrink-0">
                  {contact.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-text">{contact.name}</h3>
                  {contact.title && contact.company && (
                    <p className="text-xs text-text-muted">{contact.title} at {contact.company}</p>
                  )}
                  {contact.email && (
                    <p className="text-xs text-text-dim mt-1 truncate">{contact.email}</p>
                  )}
                  {contact.phone && (
                    <p className="text-xs text-text-dim">{contact.phone}</p>
                  )}
                  {contact.tags && contact.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap mt-2">
                      {contact.tags.map((tag) => (
                        <span key={tag} className="badge bg-bg-elevated text-text-dim">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
