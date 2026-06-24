import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-text mb-4">
          Chromagora OS
        </h1>
        <p className="text-text-muted text-lg mb-8">
          Multi-agent operating system for small and medium businesses.
        </p>
        <div className="grid grid-cols-2 gap-4 text-left">
          <Link
            href="/businesses"
            className="card hover:border-accent/50 transition-colors"
          >
            <h2 className="font-semibold text-text mb-1">Businesses</h2>
            <p className="text-sm text-text-muted">
              Manage clients, authority, and tools
            </p>
          </Link>
          <Link
            href="/approvals"
            className="card hover:border-accent/50 transition-colors"
          >
            <h2 className="font-semibold text-text mb-1">Approvals</h2>
            <p className="text-sm text-text-muted">
              Review agent-proposed actions
            </p>
          </Link>
          <Link
            href="/agents"
            className="card hover:border-accent/50 transition-colors"
          >
            <h2 className="font-semibold text-text mb-1">Agents</h2>
            <p className="text-sm text-text-muted">
              Workforce and agent runs
            </p>
          </Link>
          <Link
            href="/demo"
            className="card hover:border-accent/50 transition-colors"
          >
            <h2 className="font-semibold text-text mb-1">Demo</h2>
            <p className="text-sm text-text-muted">
              Run simulation loops
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
