import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Chromagora OS",
  description: "Multi-agent operating system for SMBs",
};

const themeInitScript = `(()=>{try{var t=localStorage.getItem("chromagora-theme");if(t==="light"){document.documentElement.classList.add("light")}}catch(e){}})()`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="flex">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
