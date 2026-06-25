"use client";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: string;
  trend?: string;
  trendUp?: boolean;
  accent?: boolean;
}

export default function StatCard({
  label,
  value,
  icon,
  trend,
  trendUp,
  accent,
}: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-text-muted">{label}</p>
          <p
            className={`text-2xl font-bold mt-1 ${
              accent ? "text-accent" : "text-text"
            }`}
          >
            {value}
          </p>
          {trend && (
            <p
              className={`text-xs mt-1 ${
                trendUp ? "text-success" : "text-danger"
              }`}
            >
              {trendUp ? "↑" : "↓"} {trend}
            </p>
          )}
        </div>
        {icon && <span className="text-2xl opacity-60">{icon}</span>}
      </div>
    </div>
  );
}
