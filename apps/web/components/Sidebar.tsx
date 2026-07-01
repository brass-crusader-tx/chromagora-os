"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { useState } from "react";
import { useTheme } from "@/components/ThemeProvider";

const navSections = [
  {
    label: "Core",
    items: [
      { href: "/", label: "Dashboard", icon: "◫" },
      { href: "/businesses", label: "Businesses", icon: "◈" },
      { href: "/agents", label: "Agents", icon: "◇" },
    ],
  },
  {
    label: "Operations",
    items: [
      { href: "/approvals", label: "Approvals", icon: "✓" },
      { href: "/workflows", label: "Workflows", icon: "⟳" },
      { href: "/opportunities", label: "Opportunities", icon: "◎" },
      { href: "/ledger", label: "Ledger", icon: "≡" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/voice", label: "Voice", icon: "♫" },
      { href: "/memory", label: "Memory", icon: "◆" },
      { href: "/crm", label: "CRM", icon: "☎" },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/settings", label: "Settings", icon: "⚙" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme } = useTheme();

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname?.startsWith(href);
  }

  function closeMobile() {
    setMobileOpen(false);
  }

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-4 left-4 z-50 md:hidden btn-secondary p-2"
        aria-label="Toggle menu"
      >
        {mobileOpen ? "✕" : "☰"}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 md:hidden"
          onClick={closeMobile}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed md:static z-40 w-60 h-screen bg-bg-card border-r border-bg-border flex flex-col transition-transform duration-200",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className="p-4 border-b border-bg-border flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-accent" onClick={closeMobile}>
            Chromagora
          </Link>
          <span className="text-xs text-text-dim">OS</span>
        </div>

        <nav className="flex-1 overflow-y-auto p-2 space-y-4">
          {navSections.map((section) => (
            <div key={section.label}>
              <p className="px-3 py-1 text-xs font-semibold text-text-dim uppercase tracking-wider">
                {section.label}
              </p>
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={closeMobile}
                    className={clsx(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                      isActive(item.href)
                        ? "bg-accent/10 text-accent"
                        : "text-text-muted hover:text-text hover:bg-bg-elevated"
                    )}
                  >
                    <span className="text-base opacity-70">{item.icon}</span>
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="p-3 border-t border-bg-border text-xs text-text-dim">
          Chromagora OS — {theme === "dark" ? "Dark" : "Light"} Mode
        </div>
      </aside>
    </>
  );
}
