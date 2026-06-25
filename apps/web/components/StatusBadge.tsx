import clsx from "clsx";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const STATUS_STYLES: Record<string, string> = {
  active: "bg-success/20 text-success",
  inactive: "bg-bg-border text-text-dim",
  pending: "bg-warning/20 text-warning",
  approved: "bg-success/20 text-success",
  rejected: "bg-danger/20 text-danger",
  running: "bg-accent/20 text-accent",
  completed: "bg-success/20 text-success",
  failed: "bg-danger/20 text-danger",
  error: "bg-danger/20 text-danger",
  paused: "bg-warning/20 text-warning",
  draft: "bg-bg-border text-text-dim",
  sent: "bg-accent/20 text-accent",
  bound: "bg-accent/20 text-accent",
  requires_approval: "bg-warning/20 text-warning",
  observing: "bg-bg-border text-text-dim",
  analyzing: "bg-accent/20 text-accent",
};

export default function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] || "bg-bg-border text-text-dim";
  return (
    <span
      className={clsx(
        "badge",
        style,
        size === "md" && "px-3 py-1 text-sm"
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
