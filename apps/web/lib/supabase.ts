import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder.supabase.co";
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "placeholder-key";

export const supabase = createBrowserClient(supabaseUrl, supabaseKey);

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
