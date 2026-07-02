"""Demo Factory public-site crawler.

The crawler is HTTP-first so the worker remains deployable with the current
dependency set. When Node Playwright is available, it also captures local
desktop/mobile screenshots into the Next.js public folder for local demos.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from uuid import UUID, uuid4

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PUBLIC_ASSET_ROOT = PROJECT_ROOT / "apps" / "web" / "public" / "demo-assets"
MAX_PAGES = int(os.getenv("DEMO_FACTORY_CRAWL_MAX_PAGES", "5"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("DEMO_FACTORY_CRAWL_HTTP_TIMEOUT_SECONDS", "20"))
USER_AGENT = "ChromagoraDemoFactory/0.1 (+https://chromagora.com)"


@dataclass
class ParsedPage:
    title: str | None = None
    meta_description: str | None = None
    text_chunks: list[str] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    images: list[tuple[str, str | None]] = field(default_factory=list)
    style_chunks: list[str] = field(default_factory=list)
    logo_candidates: list[str] = field(default_factory=list)

    @property
    def visible_text(self) -> str:
        joined = " ".join(chunk.strip() for chunk in self.text_chunks if chunk.strip())
        joined = re.sub(r"\s+", " ", html.unescape(joined)).strip()
        return joined[:18000]


class DemoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.page = ParsedPage()
        self._skip_depth = 0
        self._capture_title = False
        self._capture_style = False
        self._link_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = {key.lower(): value for key, value in attrs}
        tag = tag.lower()
        if tag in {"script", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if tag == "style":
            self._capture_style = True
            return
        if tag == "title":
            self._capture_title = True
            return
        if tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            if name in {"description", "og:description"} and attrs_dict.get("content"):
                self.page.meta_description = attrs_dict["content"]
        if tag == "a" and attrs_dict.get("href"):
            self._link_href = attrs_dict["href"]
        if tag == "img":
            src = attrs_dict.get("src") or attrs_dict.get("data-src") or attrs_dict.get("data-lazy-src")
            alt = attrs_dict.get("alt")
            if src:
                self.page.images.append((src, alt))
                combined = f"{src} {alt or ''}".lower()
                if "logo" in combined or "brand" in combined:
                    self.page.logo_candidates.append(src)
        if tag == "link":
            rel = (attrs_dict.get("rel") or "").lower()
            href = attrs_dict.get("href")
            if href and any(token in rel for token in ["icon", "apple-touch-icon"]):
                self.page.logo_candidates.append(href)

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in {"script", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "style":
            self._capture_style = False
        if tag == "title":
            self._capture_title = False
        if tag == "a":
            self._link_href = None

    def handle_data(self, data: str):
        if self._skip_depth:
            return
        if self._capture_style:
            self.page.style_chunks.append(data)
            return
        text = data.strip()
        if not text:
            return
        if self._capture_title:
            self.page.title = text[:300]
            return
        self.page.text_chunks.append(text)
        if self._link_href:
            self.page.links.append((self._link_href, text[:200]))


def crawl_site(*, sb, tenant_id: UUID, project: dict[str, Any]) -> dict[str, Any]:
    """Fetch the homepage, discover high-value pages, persist snapshots/assets."""
    if _crawler_provider() == "mock":
        return _mock_crawl_site(sb=sb, tenant_id=tenant_id, project=project)

    project_id = str(project["id"])
    source_url = _source_url(project)
    business_name = project.get("business_name") or "Local Business"
    fetched_pages: list[dict[str, Any]] = []

    with httpx.Client(
        timeout=HTTP_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    ) as client:
        homepage = _fetch_and_parse(client, source_url, "home")
        fetched_pages.append(homepage)
        for candidate_url, page_type in _discover_pages(homepage["parsed"], homepage["final_url"]):
            if len(fetched_pages) >= MAX_PAGES:
                break
            if any(_same_url(candidate_url, page["final_url"]) for page in fetched_pages):
                continue
            try:
                fetched_pages.append(_fetch_and_parse(client, candidate_url, page_type))
            except Exception:
                continue

    screenshot_assets = _capture_screenshots(
        source_url,
        tenant_id,
        project_id,
        business_name,
        sb=sb,
    )
    persisted_snapshots: list[dict[str, Any]] = []
    for page in fetched_pages:
        parsed: ParsedPage = page["parsed"]
        snapshot = {
            "id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "project_id": project_id,
            "source_url": page["source_url"],
            "final_url": page["final_url"],
            "page_type": page["page_type"],
            "http_status": page["http_status"],
            "title": parsed.title or business_name,
            "meta_description": parsed.meta_description,
            "visible_text": parsed.visible_text,
            "text_summary": _summarize_text(parsed.visible_text, business_name),
            "screenshot_bucket": "demo-source-snapshots" if page["page_type"] == "home" and screenshot_assets else None,
            "screenshot_path": screenshot_assets[0]["storage_path"] if page["page_type"] == "home" and screenshot_assets else None,
            "metadata_json": {
                "mock": False,
                "contact_candidates": _extract_contacts(parsed.visible_text),
                "service_candidates": _extract_service_candidates(parsed.visible_text),
                "location_candidates": _extract_location_candidates(parsed.visible_text),
                "image_candidates": [_absolute_url(src, page["final_url"]) for src, _alt in parsed.images[:30]],
                "logo_candidates": [_absolute_url(src, page["final_url"]) for src in parsed.logo_candidates[:10]],
                "color_candidates": _extract_colors(" ".join(parsed.style_chunks)),
                "testimonial_candidates": _extract_testimonial_candidates(
                    parsed,
                    page["final_url"],
                    page["page_type"],
                    business_name,
                ),
                "links": [
                    {"href": _absolute_url(href, page["final_url"]), "text": text}
                    for href, text in parsed.links[:80]
                ],
            },
        }
        sb.table("demo_site_source_snapshots").insert(snapshot).execute()
        persisted_snapshots.append(snapshot)

        for src, alt in parsed.images[:20]:
            sb.table("demo_site_assets").insert(
                {
                    "tenant_id": str(tenant_id),
                    "project_id": project_id,
                    "snapshot_id": snapshot["id"],
                    "asset_type": "image_candidate",
                    "source_url": _absolute_url(src, page["final_url"]),
                    "alt_text": alt,
                    "status": "candidate",
                    "metadata_json": {"page_type": page["page_type"]},
                }
            ).execute()

    for asset in screenshot_assets:
        asset["tenant_id"] = str(tenant_id)
        asset["project_id"] = project_id
        sb.table("demo_site_assets").insert(asset).execute()

    return {
        "snapshots": persisted_snapshots,
        "old_site_screenshot": screenshot_assets[0] if screenshot_assets else None,
        "page_count": len(persisted_snapshots),
    }


def _mock_crawl_site(*, sb, tenant_id: UUID, project: dict[str, Any]) -> dict[str, Any]:
    project_id = project["id"]
    source_url = _source_url(project)
    business_name = project.get("business_name") or "Local Business"
    snapshot_id = str(uuid4())
    desktop_screenshot_path = f"{tenant_id}/{project_id}/source/home-desktop.png"
    mobile_screenshot_path = f"{tenant_id}/{project_id}/source/home-mobile.png"
    snapshot = {
        "id": snapshot_id,
        "tenant_id": str(tenant_id),
        "project_id": project_id,
        "source_url": source_url,
        "final_url": source_url,
        "page_type": "home",
        "http_status": 200,
        "title": business_name,
        "meta_description": f"Public homepage snapshot for {business_name}",
        "visible_text": f"{business_name} homepage. Services, contact, gallery, and service area details.",
        "text_summary": f"Homepage evidence for {business_name}.",
        "screenshot_bucket": "demo-source-snapshots",
        "screenshot_path": desktop_screenshot_path,
        "metadata_json": {
            "mock": True,
            "contact_candidates": {},
            "service_candidates": [],
            "location_candidates": [],
            "image_candidates": [],
            "logo_candidates": [],
            "color_candidates": ["#1f2937", "#2563eb", "#f8fafc"],
            "testimonial_candidates": [],
        },
    }
    sb.table("demo_site_source_snapshots").insert(snapshot).execute()
    assets = []
    for viewport, screenshot_path in [
        ("desktop", desktop_screenshot_path),
        ("mobile", mobile_screenshot_path),
    ]:
        asset = {
            "tenant_id": str(tenant_id),
            "project_id": project_id,
            "snapshot_id": snapshot_id,
            "asset_type": "old_site_screenshot",
            "storage_bucket": "demo-source-snapshots",
            "storage_path": screenshot_path,
            "public_url": None,
            "alt_text": f"Current {viewport} website screenshot for {business_name}",
            "status": "selected",
            "metadata_json": {"viewport": viewport, "mock": True},
        }
        sb.table("demo_site_assets").insert(asset).execute()
        assets.append(asset)
    return {"snapshots": [snapshot], "old_site_screenshot": assets[0], "page_count": 1}


def _source_url(project: dict[str, Any]) -> str:
    url = project.get("source_url")
    if url:
        return url if "://" in url else f"https://{url}"
    domain = project.get("normalized_domain") or project.get("source_domain")
    if not domain:
        raise RuntimeError("Project has no source URL or domain to crawl")
    return f"https://{domain}"


def _fetch_and_parse(client: httpx.Client, url: str, page_type: str) -> dict[str, Any]:
    response = _fetch_url(client, url)
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise RuntimeError(f"Unsupported content type for {url}: {content_type}")
    parser = DemoHTMLParser()
    parser.feed(response.text[:1_500_000])
    return {
        "source_url": url,
        "final_url": str(response.url),
        "http_status": response.status_code,
        "page_type": page_type,
        "parsed": parser.page,
    }


def _fetch_url(client: httpx.Client, url: str) -> httpx.Response:
    if _crawler_provider() != "brightdata":
        return client.get(url)
    if not _brightdata_ready():
        return client.get(url)
    return _fetch_with_brightdata(url)


def _crawler_provider() -> str:
    raw = os.getenv("DEMO_FACTORY_CRAWLER_PROVIDER", "").strip()
    lowered = raw.lower()
    if lowered in {"", "http", "direct"}:
        return "http"
    if lowered in {"mock", "brightdata"}:
        return lowered
    if _looks_like_secret(raw):
        return "brightdata"
    return lowered


def _brightdata_api_key() -> str:
    provider_value = os.getenv("DEMO_FACTORY_CRAWLER_PROVIDER", "").strip()
    if _looks_like_secret(provider_value):
        return provider_value
    return (
        os.getenv("DEMO_FACTORY_BRIGHTDATA_API_KEY", "").strip()
        or os.getenv("BRIGHTDATA_API_KEY", "").strip()
    )


def _brightdata_ready() -> bool:
    return bool(_brightdata_api_key() and os.getenv("DEMO_FACTORY_BRIGHTDATA_ZONE", "").strip())


def _looks_like_secret(value: str) -> bool:
    lowered = value.lower()
    return bool(value) and lowered not in {"mock", "brightdata", "http", "direct"}


def _fetch_with_brightdata(url: str) -> httpx.Response:
    api_key = _brightdata_api_key()
    zone = os.getenv("DEMO_FACTORY_BRIGHTDATA_ZONE", "").strip()
    if not api_key:
        raise RuntimeError("Bright Data crawler selected but DEMO_FACTORY_BRIGHTDATA_API_KEY is not configured")
    if not zone:
        raise RuntimeError("Bright Data crawler selected but DEMO_FACTORY_BRIGHTDATA_ZONE is not configured")

    timeout = float(os.getenv("DEMO_FACTORY_BRIGHTDATA_TIMEOUT_SECONDS", "90"))
    with httpx.Client(timeout=timeout) as unlocker:
        response = unlocker.post(
            "https://api.brightdata.com/request",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"zone": zone, "url": url, "format": "raw"},
        )
    response.raise_for_status()
    return response


def _discover_pages(parsed: ParsedPage, base_url: str) -> list[tuple[str, str]]:
    wanted = [
        ("about", re.compile(r"\b(about|company|team)\b", re.I)),
        ("services", re.compile(r"\b(services|solutions|what we do)\b", re.I)),
        ("gallery", re.compile(r"\b(gallery|projects|portfolio|work)\b", re.I)),
        ("reviews", re.compile(r"\b(reviews?|testimonials?|customer stories|what clients say)\b", re.I)),
        ("contact", re.compile(r"\b(contact|get quote|estimate|request)\b", re.I)),
    ]
    found: list[tuple[str, str]] = []
    base_host = urlparse(base_url).netloc.lower().removeprefix("www.")
    for href, text in parsed.links:
        absolute = _absolute_url(href, base_url)
        if not absolute:
            continue
        host = urlparse(absolute).netloc.lower().removeprefix("www.")
        if host != base_host:
            continue
        haystack = f"{href} {text}"
        for page_type, pattern in wanted:
            if pattern.search(haystack) and all(existing[1] != page_type for existing in found):
                found.append((absolute, page_type))
                break
    return found


def _capture_screenshots(
    source_url: str,
    tenant_id: UUID,
    project_id: str,
    business_name: str,
    *,
    sb=None,
) -> list[dict[str, Any]]:
    if os.getenv("DEMO_FACTORY_DISABLE_SCREENSHOTS", "").lower() in {"1", "true", "yes"}:
        return []
    output_dir = PUBLIC_ASSET_ROOT / str(tenant_id) / project_id / "source"
    output_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = output_dir / "home-desktop.png"
    mobile_path = output_dir / "home-mobile.png"
    script = """
const { chromium } = require('playwright');
const [url, desktopPath, mobilePath] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1200 }, deviceScaleFactor: 1 });
  await desktop.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
  await desktop.screenshot({ path: desktopPath, fullPage: true });
  const mobile = await browser.newPage({ viewport: { width: 390, height: 1200 }, isMobile: true, deviceScaleFactor: 2 });
  await mobile.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
  await mobile.screenshot({ path: mobilePath, fullPage: true });
  await browser.close();
})().catch((err) => { console.error(err.stack || err.message); process.exit(1); });
"""
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as tmp:
            tmp.write(script)
            tmp_path = tmp.name
        subprocess.run(
            ["node", tmp_path, source_url, str(desktop_path), str(mobile_path)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=75,
        )
    except Exception as exc:
        _record_screenshot_failure(sb, tenant_id, project_id, exc)
        return []
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    assets: list[dict[str, Any]] = []
    for viewport, path in [("desktop", desktop_path), ("mobile", mobile_path)]:
        if not path.exists():
            continue
        rel = path.relative_to(PUBLIC_ASSET_ROOT)
        assets.append(
            {
                "asset_type": "old_site_screenshot",
                "storage_bucket": "demo-source-snapshots",
                "storage_path": str(rel),
                "public_url": f"/demo-assets/{rel.as_posix()}",
                "alt_text": f"Current {viewport} website screenshot for {business_name}",
                "status": "selected",
                "metadata_json": {"viewport": viewport, "mock": False, "local_public_asset": True},
            }
        )
    return assets


def _record_screenshot_failure(sb, tenant_id: UUID, project_id: str, exc: Exception) -> None:
    if sb is None:
        return
    screenshots_required = os.getenv("DEMO_FACTORY_SCREENSHOTS_REQUIRED", "").lower() in {"1", "true", "yes"}
    try:
        sb.table("demo_factory_supervisor_events").insert(
            {
                "tenant_id": str(tenant_id),
                "project_id": project_id,
                "event_type": "demo_site.screenshot_failed",
                "severity": "error" if screenshots_required else "warning",
                "stage": "crawl_site",
                "message": str(exc)[:1000],
                "payload_json": {"screenshots_required": screenshots_required},
            }
        ).execute()
    except Exception:
        pass


def _absolute_url(value: str | None, base_url: str) -> str | None:
    if not value:
        return None
    if value.startswith("data:") or value.startswith("mailto:") or value.startswith("tel:"):
        return value
    return urljoin(base_url, value)


def _same_url(a: str, b: str) -> bool:
    pa = urlparse(a)
    pb = urlparse(b)
    return (pa.scheme, pa.netloc.lower(), pa.path.rstrip("/")) == (pb.scheme, pb.netloc.lower(), pb.path.rstrip("/"))


def _summarize_text(text: str, business_name: str) -> str:
    if not text:
        return f"No visible homepage text extracted for {business_name}."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:6]).strip()
    return summary[:1200]


def _extract_contacts(text: str) -> dict[str, Any]:
    phones = sorted(set(re.findall(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text)))
    emails = sorted(set(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.I)))
    return {"phones": phones[:5], "emails": emails[:5]}


def _extract_service_candidates(text: str) -> list[str]:
    lowered = text.lower()
    known = [
        "landscaping",
        "lawn care",
        "snow removal",
        "roofing",
        "cleaning",
        "remodeling",
        "plumbing",
        "hvac",
        "painting",
        "tree service",
        "hardscaping",
        "irrigation",
        "pressure washing",
        "junk removal",
        "pest control",
    ]
    found = [label.title() for label in known if label in lowered]
    if found:
        return found[:8]
    headings = re.findall(r"\b[A-Z][A-Za-z& /-]{4,40}\b", text[:5000])
    return list(dict.fromkeys(headings))[:6]


def _extract_location_candidates(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?,\s*[A-Z]{2}\b", text)
    service_area = re.findall(r"(?:serving|service area|serve[s]?)\s+([^.!?\n]{3,120})", text, flags=re.I)
    return list(dict.fromkeys(candidates + [item.strip() for item in service_area]))[:8]


def _extract_colors(css_text: str) -> list[str]:
    colors = re.findall(r"#[0-9a-fA-F]{6}\b", css_text)
    ordered = []
    for color in colors:
        normalized = color.lower()
        if normalized not in ordered and normalized not in {"#ffffff", "#000000"}:
            ordered.append(normalized)
    return ordered[:8] or ["#1f2937", "#2563eb", "#f8fafc"]


def _extract_testimonial_candidates(
    parsed: ParsedPage,
    source_url: str,
    page_type: str,
    business_name: str,
) -> list[dict[str, Any]]:
    """Extract clearly sourced on-site testimonials from crawled text chunks."""
    review_page = page_type == "reviews" or any(
        token in (parsed.title or "").lower()
        for token in ["review", "testimonial", "customer stories", "what clients say"]
    )
    chunks = [re.sub(r"\s+", " ", chunk).strip() for chunk in parsed.text_chunks if chunk.strip()]
    candidates: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        text = _clean_testimonial_text(chunk)
        if not text or not _looks_like_testimonial(text, review_page):
            continue
        reviewer = _nearby_reviewer_name(chunks, index)
        if not review_page and reviewer is None:
            continue
        candidates.append(
            {
                "source_name": "business_site",
                "source_url": source_url,
                "reviewer_name": reviewer,
                "rating": None,
                "review_text": text,
                "identity_match_signals": {
                    "business_name_match": bool(business_name),
                    "phone_match": False,
                    "website_match": True,
                    "location_service_area_match": False,
                    "category_match": False,
                },
                "confidence_score": 0.80 if review_page else 0.70,
                "provenance": "business_site_testimonial",
            }
        )
        if len(candidates) >= 8:
            break
    return candidates


def _clean_testimonial_text(value: str) -> str | None:
    text = html.unescape(value).strip(" \t\r\n\"'")
    text = re.sub(r"\s+", " ", text)
    if len(text) < 35 or len(text) > 700:
        return None
    lowered = text.lower()
    blocked = [
        "copyright",
        "privacy policy",
        "terms of service",
        "all rights reserved",
        "request a quote",
        "book now",
        "contact us",
        "read more",
        "learn more",
        "lorem ipsum",
    ]
    if any(token in lowered for token in blocked):
        return None
    return text


def _looks_like_testimonial(text: str, review_page: bool) -> bool:
    lowered = text.lower()
    review_terms = [
        "highly recommend",
        "recommend",
        "professional",
        "excellent",
        "amazing",
        "great job",
        "pleased",
        "satisfied",
        "on time",
        "quality",
        "would use",
        "five stars",
        "5 stars",
    ]
    if any(term in lowered for term in review_terms):
        return True
    if review_page and re.search(r"\b(thank|thanks|love|happy|best|reliable|friendly)\b", lowered):
        return True
    return False


def _nearby_reviewer_name(chunks: list[str], index: int) -> str | None:
    for offset in (1, -1, 2):
        near_index = index + offset
        if near_index < 0 or near_index >= len(chunks):
            continue
        candidate = chunks[near_index].strip().strip("- ")
        if not 2 <= len(candidate) <= 80:
            continue
        if re.search(r"[@/:]|\d{3}|\b(call|click|read|review|testimonial)\b", candidate, re.I):
            continue
        if re.match(r"^[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,3}$", candidate):
            return candidate
    return None
