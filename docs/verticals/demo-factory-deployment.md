# Demo Factory Deployment

Demo Factory publishing marks a passing SiteSpec as current and records a private demo URL. v0.1 local development uses `/demo/{slug}`. Production wildcard host routing maps `{slug}.demo.chromagora.com` to the same renderer.

## DNS

| Record | Target |
|---|---|
| `*.demo.chromagora.com` | Frontend hosting target for the Chromagora Next.js app. |

The wildcard should point to the same frontend that serves the Operator Cockpit and public demo renderer.

## Host Mapping

Production middleware should resolve:

```txt
{slug}.demo.chromagora.com -> /demo/{slug}
```

Local development can use:

```txt
http://localhost:3000/demo/{slug}
```

## SiteSpec Resolution

The public renderer loads:

```txt
GET /demo-sites/public/{slug}/site-spec
```

The API resolves the active tenant, finds the published deployment/spec for `demo_slug`, and returns the current `SiteSpec` JSON.

## Publish Behavior

1. Worker creates or updates `demo_site_specs`.
2. QA passes without blocking issues.
3. Deployment service marks previous project specs non-current.
4. Latest passing SiteSpec becomes current.
5. `demo_site_deployments` is inserted or updated with:
   - `demo_slug`
   - `demo_host`
   - `demo_url`
   - `status = published`
6. Project and batch row become `published`.
7. `demo_site.published` event is emitted.

## Rollback Behavior

Rollback should mark a prior `demo_site_specs` row as `is_current = true` and archive the failed/newer deployment record. The renderer always reads the current published spec, so rollback does not require generated source files.

## Storage Buckets

| Bucket | Contents |
|---|---|
| `demo-source-snapshots` | Old-site screenshots and crawl artifacts. |
| `demo-business-assets` | Scraped business images/logos. |
| `demo-rendered-screenshots` | QA render screenshots. |
| `demo-public-assets` | Published demo-safe images. |
| `chromagora-brand-assets` | Chromagora C logo and shared brand assets. |

Paths should be tenant/project scoped, for example:

```txt
{tenant_id}/{project_id}/source/home-desktop.png
{tenant_id}/{project_id}/qa/mobile.png
```
