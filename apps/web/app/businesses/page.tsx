"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiBaseUrl } from "@/lib/supabase";

interface Business {
  id: string;
  name: string;
  created_at: string;
}

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${apiBaseUrl}/businesses`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setBusinesses)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl font-bold text-text mb-6">Businesses</h1>

      {loading ? (
        <p className="text-text-muted">Loading...</p>
      ) : businesses.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-text-muted">No businesses found.</p>
          <p className="text-xs text-text-dim mt-2">
            Add a business via Supabase to get started.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {businesses.map((biz) => (
            <div key={biz.id} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-text">{biz.name}</h3>
                  <p className="text-xs text-text-dim mt-1">
                    ID: {biz.id.slice(0, 8)}...
                  </p>
                </div>
                <div className="flex gap-2">
                  <Link
                    href={`/businesses/${biz.id}/authority`}
                    className="btn-secondary text-xs"
                  >
                    Authority
                  </Link>
                  <Link
                    href={`/businesses/${biz.id}/tools`}
                    className="btn-secondary text-xs"
                  >
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
