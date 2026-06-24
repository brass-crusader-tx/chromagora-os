"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiBaseUrl } from "@/lib/supabase";
import clsx from "clsx";

interface ToolDefinition {
  id: string;
  name: string;
  description: string | null;
  target_system: string;
  tool_action: string;
  risk_level_default: string;
  autonomy_level_required_default: number;
  is_external_action: boolean;
}

interface ToolPermission {
  id: string;
  tool_definition_id: string;
  is_enabled: boolean;
  max_autonomy_level: number;
  requires_approval_override: boolean | null;
  tool_definitions: ToolDefinition;
}

const RISK_COLORS: Record<string, string> = {
  low: "text-success bg-success/20",
  medium: "text-warning bg-warning/20",
  high: "text-danger bg-danger/20",
};

export default function ToolsPage() {
  const params = useParams();
  const businessId = params.id as string;

  const [permissions, setPermissions] = useState<ToolPermission[]>([]);
  const [definitions, setDefinitions] = useState<ToolDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    try {
      const [permRes, defRes] = await Promise.all([
        fetch(`${apiBaseUrl}/businesses/${businessId}/tools`),
        fetch(`${apiBaseUrl}/businesses/${businessId}/tools/definitions`),
      ]);
      if (permRes.ok) setPermissions(await permRes.json());
      if (defRes.ok) setDefinitions(await defRes.json());
    } catch {
      // API may not be running
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [businessId]);

  async function toggleTool(toolDefId: string, currentlyEnabled: boolean) {
    const endpoint = currentlyEnabled ? "disable" : "enable";
    try {
      await fetch(
        `${apiBaseUrl}/businesses/${businessId}/tools/${toolDefId}/${endpoint}`,
        { method: "POST" }
      );
      loadData();
    } catch {
      // API may not be running
    }
  }

  async function updateAutonomy(toolDefId: string, level: number) {
    try {
      await fetch(
        `${apiBaseUrl}/businesses/${businessId}/tools/${toolDefId}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ max_autonomy_level: level }),
        }
      );
      loadData();
    } catch {
      // API may not be running
    }
  }

  // Merge definitions with permissions
  const merged = definitions.map((def) => {
    const perm = permissions.find(
      (p) => p.tool_definition_id === def.id
    );
    return {
      definition: def,
      permission: perm,
      isEnabled: perm?.is_enabled ?? false,
    };
  });

  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text">Tool Permissions</h1>
        <p className="text-sm text-text-muted mt-1">
          Enable or disable tools for this business. Control which actions
          agents can execute.
        </p>
      </div>

      {loading ? (
        <p className="text-text-muted">Loading...</p>
      ) : merged.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-text-muted">No tool definitions registered.</p>
          <p className="text-xs text-text-dim mt-2">
            Tools must be registered by the system.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {merged.map(({ definition, permission, isEnabled }) => (
            <div
              key={definition.id}
              className={clsx(
                "card flex items-center justify-between transition-opacity",
                !isEnabled && "opacity-60"
              )}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-text">
                    {definition.name}
                  </h3>
                  <span
                    className={clsx(
                      "badge",
                      RISK_COLORS[definition.risk_level_default] ||
                        "bg-bg-border text-text-dim"
                    )}
                  >
                    {definition.risk_level_default}
                  </span>
                  {definition.is_external_action && (
                    <span className="badge bg-warning/20 text-warning">
                      external
                    </span>
                  )}
                </div>
                {definition.description && (
                  <p className="text-sm text-text-muted mt-1">
                    {definition.description}
                  </p>
                )}
                <div className="flex gap-4 mt-2 text-xs text-text-dim">
                  <span>Target: {definition.target_system}</span>
                  <span>Action: {definition.tool_action}</span>
                  <span>
                    Default autonomy: L
                    {definition.autonomy_level_required_default}
                  </span>
                </div>

                {/* Autonomy level slider (only when enabled) */}
                {isEnabled && (
                  <div className="mt-3 flex items-center gap-3">
                    <span className="text-xs text-text-dim w-16">
                      Autonomy: L
                      {permission?.max_autonomy_level ??
                        definition.autonomy_level_required_default}
                    </span>
                    <input
                      type="range"
                      min={0}
                      max={6}
                      value={
                        permission?.max_autonomy_level ??
                        definition.autonomy_level_required_default
                      }
                      onChange={(e) =>
                        updateAutonomy(
                          definition.id,
                          parseInt(e.target.value)
                        )
                      }
                      className="flex-1 accent-accent"
                    />
                  </div>
                )}
              </div>

              {/* Toggle */}
              <div className="ml-4">
                <button
                  onClick={() =>
                    toggleTool(definition.id, isEnabled)
                  }
                  className={clsx(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                    isEnabled
                      ? "bg-accent"
                      : "bg-bg-border"
                  )}
                >
                  <span
                    className={clsx(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      isEnabled ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
                <p className="text-xs text-text-dim mt-1 text-center">
                  {isEnabled ? "On" : "Off"}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
