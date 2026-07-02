# Demo Factory Renderer Contract

The Demo Factory renderer consumes one canonical artifact: `SiteSpec` JSON. Agents may propose strategy, copy, assets, and section plans, but public demo pages are rendered only through deterministic Next.js components owned by Chromagora.

## Hard Rules

| Rule | Reason |
|---|---|
| No arbitrary generated React | Prevents code execution, style drift, and per-demo source files. |
| No arbitrary generated CSS | Keeps layout and QA deterministic. |
| No arbitrary generated HTML as the primary path | Avoids untrusted markup and exposed prompt artifacts. |
| Unknown section types do not crash | Renderer skips unknown sections and QA reports them. |
| Footer is enforced by renderer | Agents cannot remove or rewrite Chromagora attribution. |
| Before/after reveal is config-driven | The wrapper is a first-class renderer feature, not generated code. |

## SiteSpec Shape

Minimum top-level fields:

| Field | Purpose |
|---|---|
| `project_id` | Project UUID. |
| `business_name` | Display name for the business. |
| `business_vertical` | Service vertical or category. |
| `service_area` | Primary geography/service area. |
| `brand` | Colors, logo, type tone, and visual guidance. |
| `pages` | One or more page specs. v0.1 usually renders one strong landing page. |
| `navigation` | Controlled internal navigation links. |
| `primary_cta` | Main call to action. |
| `sticky_mobile_cta` | Optional mobile CTA. |
| `assets` | Renderer-safe asset references. |
| `reviews` | Verified review snippets only. |
| `trust_claims` | Supported factual claims. |
| `forms` | Form placeholders and verified contact routes. |
| `before_after_reveal` | Reveal wrapper config. |
| `chromagora_footer` | Required footer config. |
| `metadata` | Extensible operational metadata. |

## Controlled Section Types

| Type | Role |
|---|---|
| `hero` | Above-fold message, CTA, and optional hero image. |
| `service_grid` | Service cards from verified or inferred service candidates. |
| `trust_strip` | Supported proof points only. |
| `gallery_grid` | Real business/gallery assets or neutral relevant images. |
| `review_cards` | Verified exact-business reviews. |
| `process_steps` | Simple service process where supported. |
| `service_area` | Geographic/service-area block. |
| `quote_cta` | Mid/late-page CTA band. |
| `contact_panel` | Contact and form placeholder. |
| `footer_spacer` | Layout spacer before enforced footer. |

## Allowed Props

Each section receives structured JSON props such as headings, short body copy, CTA references, asset IDs/URLs, item arrays, and supported claim references. Text is rendered as text, not HTML. Asset references resolve through `demo_site_assets` or published public URLs.

## Footer Enforcement

Every demo page renders `ChromagoraDemoFooter` after the page content:

`Created at Chromagora by human minds`

The logo links to `https://chromagora.com`. The footer is not controlled by agents.

## Before/After Reveal

`before_after_reveal` can configure:

| Field | Purpose |
|---|---|
| `enabled` | Whether the wrapper is active. |
| `orientation` | `horizontal` means pull down; `vertical` means drag across. |
| `before_image_url` | Old-site screenshot. |
| `instruction_text` | Minimal instruction text. |
| `default_reveal_percent` | Initial reveal amount. |

The new demo layer is the deterministic renderer output.
