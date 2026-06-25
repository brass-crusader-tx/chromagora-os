"use client";

import { useState } from "react";
import PageHeader from "@/components/PageHeader";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="p-4 md:p-6 max-w-3xl">
      <PageHeader
        title="Settings"
        description="Configure your Chromagora OS preferences"
      />

      <div className="space-y-6">
        {/* API Configuration */}
        <div className="card">
          <h2 className="font-semibold text-text mb-4">API Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="label">Backend API URL</label>
              <input
                className="input"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
              />
              <p className="text-xs text-text-dim mt-1">
                The URL of your Chromagora backend API server.
              </p>
            </div>
          </div>
        </div>

        {/* Theme */}
        <div className="card">
          <h2 className="font-semibold text-text mb-4">Appearance</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text">Dark Mode</p>
                <p className="text-xs text-text-dim">Always enabled for optimal experience</p>
              </div>
              <span className="badge bg-success/20 text-success">Active</span>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <h2 className="font-semibold text-text mb-4">Notifications</h2>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 accent-accent" />
              <div>
                <p className="text-sm text-text">Approval Requests</p>
                <p className="text-xs text-text-dim">Get notified when agents request approval</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 accent-accent" />
              <div>
                <p className="text-sm text-text">Agent Status Changes</p>
                <p className="text-xs text-text-dim">Alerts when agents go offline or error</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-accent" />
              <div>
                <p className="text-sm text-text">Daily Summary</p>
                <p className="text-xs text-text-dim">Receive a daily activity digest</p>
              </div>
            </label>
          </div>
        </div>

        {/* About */}
        <div className="card">
          <h2 className="font-semibold text-text mb-4">About</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-muted">Version</span>
              <span className="text-text">0.1.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Framework</span>
              <span className="text-text">Next.js 15</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Theme</span>
              <span className="text-text">Dark Mode</span>
            </div>
          </div>
        </div>

        {/* Save */}
        <div className="flex items-center gap-4">
          <button onClick={handleSave} className="btn-primary">
            Save Settings
          </button>
          {saved && (
            <span className="text-sm text-success">✓ Settings saved</span>
          )}
        </div>
      </div>
    </div>
  );
}
