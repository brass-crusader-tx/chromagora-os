"""Visual QA for Demo Factory renders."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from chromagora_schemas.demo_factory import SiteSpec


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PUBLIC_ASSET_ROOT = PROJECT_ROOT / "apps" / "web" / "public" / "demo-assets"
BLOCKING_MARKERS = ["{{", "lorem ipsum", "as an ai", "ai-generated", "todo", "fixme"]


def run_visual_qa(*, sb, tenant_id: UUID, project_id: UUID, spec_id: UUID, site_spec: SiteSpec) -> dict[str, Any]:
    serialized = json.dumps(site_spec.model_dump(mode="json"), sort_keys=True).lower()
    blocking = [f"Unresolved or exposed marker: {marker}" for marker in BLOCKING_MARKERS if marker in serialized]
    warnings: list[str] = []
    screenshots: list[dict[str, Any]] = []
    render_checks: dict[str, Any] = {
        "schema_checked": True,
        "footer_present": site_spec.chromagora_footer.enabled,
        "before_after_enabled": site_spec.before_after_reveal.enabled,
        "before_desktop_image_present": bool(site_spec.before_after_reveal.before_desktop_image_url or site_spec.before_after_reveal.before_image_url),
        "before_mobile_image_present": bool(site_spec.before_after_reveal.before_mobile_image_url or site_spec.before_after_reveal.before_image_url),
    }

    if not site_spec.chromagora_footer.enabled:
        blocking.append("Chromagora footer disabled")
    if not site_spec.primary_cta.label:
        blocking.append("Primary CTA missing")
    if not site_spec.before_after_reveal.enabled:
        _screenshot_issue("Before/after reveal is disabled", blocking, warnings)
    else:
        if not render_checks["before_desktop_image_present"]:
            _screenshot_issue("Desktop old-site screenshot is missing", blocking, warnings)
        if not render_checks["before_mobile_image_present"]:
            _screenshot_issue("Mobile old-site screenshot is missing", blocking, warnings)

    render_base_url = os.getenv("DEMO_FACTORY_RENDER_BASE_URL")
    if render_base_url:
        try:
            rendered = _run_playwright_visual_qa(render_base_url, tenant_id, project_id, spec_id)
            screenshots.extend(rendered["screenshots"])
            render_checks.update(rendered["checks"])
            blocking.extend(rendered["blocking"])
            warnings.extend(rendered["warnings"])
        except Exception as exc:
            message = f"Visual render QA could not run: {exc}"
            if os.getenv("DEMO_FACTORY_VISUAL_QA_REQUIRED", "").lower() in {"1", "true", "yes"}:
                blocking.append(message)
            else:
                warnings.append(message)
    else:
        warnings.append("DEMO_FACTORY_RENDER_BASE_URL not set; renderer screenshot QA skipped")

    status = "failed" if blocking else "passed"
    report = {
        "id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "project_id": str(project_id),
        "spec_id": str(spec_id),
        "report_type": "visual",
        "status": status,
        "blocking_issues_json": blocking,
        "warnings_json": warnings,
        "screenshots_json": screenshots,
        "report_json": render_checks,
    }
    sb.table("demo_site_qa_reports").insert(report).execute()
    return report


def _screenshot_issue(message: str, blocking: list[str], warnings: list[str]) -> None:
    if os.getenv("DEMO_FACTORY_SCREENSHOTS_REQUIRED", "").lower() in {"1", "true", "yes"}:
        blocking.append(message)
    else:
        warnings.append(message)


def _run_playwright_visual_qa(
    render_base_url: str,
    tenant_id: UUID,
    project_id: UUID,
    spec_id: UUID,
) -> dict[str, Any]:
    output_dir = PUBLIC_ASSET_ROOT / str(tenant_id) / str(project_id) / "qa"
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_url = (
        f"{render_base_url.rstrip('/')}/demo-preview/{project_id}"
        f"?spec_id={spec_id}"
    )
    result_path = output_dir / "visual-qa-result.json"
    script = """
const { chromium } = require('playwright');
const [url, outputDir, resultPath] = process.argv.slice(2);
const fs = require('fs');
const path = require('path');
const viewports = [
  { name: 'mobile', width: 390, height: 1200 },
  { name: 'tablet', width: 768, height: 1200 },
  { name: 'desktop', width: 1440, height: 1200 },
];
(async () => {
  const browser = await chromium.launch({ headless: true });
  const screenshots = [];
  const blocking = [];
  const warnings = [];
  const checks = {};
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: viewport.name === 'mobile' ? 2 : 1 });
    await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
    const screenshotPath = path.join(outputDir, `${viewport.name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    screenshots.push({ viewport: viewport.name, width: viewport.width, path: screenshotPath });
    const metrics = await page.evaluate(() => {
      const text = document.body.innerText || '';
      const html = document.documentElement.outerHTML || '';
      const footer = text.includes('Created at Chromagora by human minds');
      const anchors = Array.from(document.querySelectorAll('a')).map((a) => ({ text: a.textContent || '', href: a.getAttribute('href') || '' }));
      const ctaVisible = anchors.some((a) => /quote|call|contact|estimate|request/i.test(a.text));
      return {
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        footer,
        ctaVisible,
        markers: ['{{', 'lorem ipsum', 'as an ai', 'ai-generated', 'todo', 'fixme'].filter((m) => (text + html).toLowerCase().includes(m)),
        imageCount: document.images.length,
        brokenImages: Array.from(document.images).filter((img) => img.complete && img.naturalWidth === 0).length,
        anchorCount: anchors.length,
      };
    });
    checks[viewport.name] = metrics;
    if (metrics.scrollWidth > metrics.innerWidth + 2) blocking.push(`${viewport.name}: horizontal overflow`);
    if (!metrics.footer) blocking.push(`${viewport.name}: Chromagora footer missing`);
    if (viewport.name === 'mobile' && !metrics.ctaVisible) blocking.push('mobile: CTA not visible in document');
    if (metrics.markers.length) blocking.push(`${viewport.name}: unresolved markers ${metrics.markers.join(', ')}`);
    if (metrics.brokenImages > 0) warnings.push(`${viewport.name}: ${metrics.brokenImages} broken images`);
    await page.close();
  }
  await browser.close();
  fs.writeFileSync(resultPath, JSON.stringify({ screenshots, blocking, warnings, checks }, null, 2));
})().catch((err) => { console.error(err.stack || err.message); process.exit(1); });
"""
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as tmp:
            tmp.write(script)
            tmp_path = tmp.name
        subprocess.run(
            ["node", tmp_path, preview_url, str(output_dir), str(result_path)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        data = json.loads(result_path.read_text())
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    for item in data.get("screenshots", []):
        path = Path(item["path"])
        rel = path.relative_to(PUBLIC_ASSET_ROOT)
        item["storage_bucket"] = "demo-rendered-screenshots"
        item["storage_path"] = rel.as_posix()
        item["public_url"] = f"/demo-assets/{rel.as_posix()}"
        item.pop("path", None)
    return data
