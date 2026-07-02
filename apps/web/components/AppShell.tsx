"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";

function isStandaloneSurface(pathname: string) {
  return (
    pathname.startsWith("/demo/") ||
    pathname.startsWith("/demo-preview/") ||
    pathname.startsWith("/demo-factory")
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const standalone = isStandaloneSurface(pathname);

  return (
    <ThemeProvider>
      {standalone ? (
        <main className="min-h-screen w-full overflow-auto">{children}</main>
      ) : (
        <>
          <Sidebar />
          <main className="flex-1 overflow-auto">{children}</main>
        </>
      )}
    </ThemeProvider>
  );
}
