import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";

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
        <ThemeProvider>
          <Sidebar />
          <main className="flex-1 overflow-auto">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
