interface EmptyStateProps {
  message: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ message, description, action }: EmptyStateProps) {
  return (
    <div className="card text-center py-12">
      <p className="text-text-muted text-lg">{message}</p>
      {description && (
        <p className="text-sm text-text-dim mt-2">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
