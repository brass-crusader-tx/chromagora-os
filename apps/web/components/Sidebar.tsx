"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const navItems = [
  { href: "/businesses", label: "Businesses" },
  { href: "/approvals", label: "Approvals" },
  { href: "/agents", label: "Agents" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/ledger", label: "Ledger" },
  { href: "/demo", label: "Demo" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 h-screen bg-bg-card border-r border-bg-border flex flex-col">
      <div className="p-4 border-b border-bg-border">
        <Link href="/" className="text-lg font-bold text-accent">
          Chromagora
        </Link>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "block px-3 py-2 rounded-md text-sm transition-colors",
              pathname?.startsWith(item.href)
                ? "bg-accent/10 text-accent"
                : "text-text-muted hover:text-text hover:bg-bg-elevated"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="p-3 border-t border-bg-border text-xs text-text-dim">
        v0.1 — Dark Mode
      </div>
    </aside>
  );
}
