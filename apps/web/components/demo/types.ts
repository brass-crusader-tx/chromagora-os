export interface CTAConfig {
  label: string;
  href: string;
  kind?: string;
  aria_label?: string | null;
}

export interface BeforeAfterRevealConfig {
  enabled?: boolean;
  orientation?: "horizontal" | "vertical";
  before_image_url?: string | null;
  before_mobile_image_url?: string | null;
  before_desktop_image_url?: string | null;
  instruction_text?: string;
  default_reveal_percent?: number;
}

export interface DemoSectionSpec {
  type: string;
  section_id: string;
  variant?: string | null;
  heading?: string | null;
  eyebrow?: string | null;
  body?: string | null;
  cta?: CTAConfig | null;
  items?: Array<Record<string, unknown>>;
  props?: Record<string, unknown>;
}

export interface DemoPageSpec {
  slug: string;
  title: string;
  description?: string | null;
  sections: DemoSectionSpec[];
}

export interface SiteSpec {
  project_id: string;
  business_name: string;
  business_vertical: string;
  service_area?: string | null;
  brand: {
    primary_hex?: string;
    secondary_hex?: string;
    accent_hex?: string;
    logo_url?: string | null;
  };
  pages: DemoPageSpec[];
  navigation: Array<{ label: string; href: string }>;
  primary_cta: CTAConfig;
  sticky_mobile_cta?: CTAConfig | null;
  assets?: Array<Record<string, unknown>>;
  reviews?: Array<Record<string, unknown>>;
  trust_claims?: string[];
  forms?: Array<Record<string, unknown>>;
  before_after_reveal?: BeforeAfterRevealConfig;
  chromagora_footer?: {
    enabled?: boolean;
    text?: string;
    link_url?: string;
  };
  metadata?: Record<string, unknown>;
}
