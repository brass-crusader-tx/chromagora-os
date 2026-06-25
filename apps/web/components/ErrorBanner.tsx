interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-danger">⚠</span>
        <span className="text-sm text-danger">{message}</span>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-danger text-xs">
          Retry
        </button>
      )}
    </div>
  );
}
