import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#f8fafc",
          card: "#ffffff",
          elevated: "#f1f5f9",
          border: "#e2e8f0",
        },
        accent: {
          DEFAULT: "#4f46e5",
          hover: "#4338ca",
          muted: "#6366f1",
        },
        text: {
          DEFAULT: "#1e293b",
          muted: "#64748b",
          dim: "#94a3b8",
        },
        success: "#16a34a",
        warning: "#d97706",
        danger: "#dc2626",
      },
    },
  },
  plugins: [],
} satisfies Config;
