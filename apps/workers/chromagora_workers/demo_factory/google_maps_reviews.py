"""Google Maps review sourcing for Demo Factory.

This is evidence plumbing, not copy generation. A Google Maps review is usable
only when the scraped business profile links back to the same website domain
as the project being built.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def find_google_maps_reviews(evidence_bundle: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
    if not _enabled():
        return []
    expected_domain = _normalize_domain(
        evidence_bundle.get("source_domain") or evidence_bundle.get("source_url") or ""
    )
    business_name = str(evidence_bundle.get("business_name") or "").strip()
    if not expected_domain or not business_name:
        return []

    limit = limit or int(os.getenv("DEMO_FACTORY_REVIEW_SOURCE_LIMIT", "5"))
    query = _build_maps_query(evidence_bundle, business_name, expected_domain)
    timeout_seconds = int(os.getenv("DEMO_FACTORY_GOOGLE_MAPS_TIMEOUT_SECONDS", "75"))
    script_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as script:
            script.write(_MAPS_SCRAPER_SCRIPT)
            script_path = script.name
        completed = subprocess.run(
            ["node", script_path, query, expected_domain, str(limit)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        result = json.loads(completed.stdout or "{}")
    except Exception:
        return []
    finally:
        if script_path:
            try:
                os.unlink(script_path)
            except Exception:
                pass

    if not result.get("websiteMatched"):
        return []

    source_url = result.get("profileUrl") or f"https://www.google.com/maps/search/{query}"
    reviews: list[dict[str, Any]] = []
    for review in result.get("reviews") or []:
        text = str(review.get("reviewText") or "").strip()
        if len(text) < 25:
            continue
        reviews.append(
            {
                "source_name": "google_maps",
                "source_url": source_url,
                "reviewer_name": review.get("reviewerName"),
                "rating": review.get("rating"),
                "review_text": text[:700],
                "identity_match_signals": {
                    "business_name_match": True,
                    "phone_match": False,
                    "website_match": True,
                    "location_service_area_match": bool(evidence_bundle.get("location_service_area_candidates")),
                    "category_match": bool(evidence_bundle.get("service_candidates")),
                },
                "confidence_score": 0.85,
                "provenance": "google_maps_domain_verified",
            }
        )
        if len(reviews) >= limit:
            break
    return reviews


def _enabled() -> bool:
    raw = os.getenv("DEMO_FACTORY_GOOGLE_MAPS_REVIEWS_ENABLED", "true").lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if os.getenv("DEMO_FACTORY_MODEL_PROVIDER", "").lower() == "mock":
        return False
    if os.getenv("DEMO_FACTORY_CRAWLER_PROVIDER", "").lower() == "mock":
        return False
    return True


def _build_maps_query(evidence_bundle: dict[str, Any], business_name: str, expected_domain: str) -> str:
    location = ""
    locations = evidence_bundle.get("location_service_area_candidates") or []
    if locations:
        location = str(locations[0])
    return " ".join(part for part in [business_name, location, expected_domain] if part).strip()


def _normalize_domain(value: str) -> str:
    text = value.strip().lower()
    if not text:
        return ""
    if "://" not in text:
        text = f"https://{text}"
    parsed = urlparse(text)
    return parsed.netloc.lower().removeprefix("www.")


_MAPS_SCRAPER_SCRIPT = r"""
const { chromium } = require("playwright");

const [query, expectedDomain, rawLimit] = process.argv.slice(2);
const limit = Number.parseInt(rawLimit || "5", 10);

function unwrapUrl(href) {
  try {
    const url = new URL(href);
    const nested = url.searchParams.get("url") || url.searchParams.get("q");
    if (nested && /^https?:\/\//i.test(nested)) return nested;
    return href;
  } catch (_) {
    return href;
  }
}

function hostFor(href) {
  try {
    return new URL(unwrapUrl(href)).hostname.toLowerCase().replace(/^www\./, "");
  } catch (_) {
    return "";
  }
}

function sameDomain(host, expected) {
  return host === expected || host.endsWith(`.${expected}`);
}

function ratingFromLabel(label) {
  const match = String(label || "").match(/([0-9.]+)\s*(?:star|stars)/i);
  return match ? Number.parseFloat(match[1]) : null;
}

(async () => {
  const output = { websiteMatched: false, profileUrl: null, websiteCandidates: [], reviews: [] };
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
  });

  await page.goto(`https://www.google.com/maps/search/${encodeURIComponent(query)}`, {
    waitUntil: "domcontentloaded",
    timeout: 45000
  });
  await page.waitForTimeout(2500);

  for (const label of ["Accept all", "I agree", "Accept"]) {
    const button = page.getByRole("button", { name: label }).first();
    if (await button.count().catch(() => 0)) {
      await button.click({ timeout: 2500 }).catch(() => {});
      await page.waitForTimeout(1000);
      break;
    }
  }

  const firstPlace = page.locator('a[href*="/maps/place/"]').first();
  if (await firstPlace.count().catch(() => 0)) {
    await firstPlace.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(4500);
  }

  output.profileUrl = page.url();
  const anchors = await page.$$eval("a[href]", (nodes) => nodes.map((node) => ({
    href: node.href,
    text: (node.textContent || "").trim(),
    aria: node.getAttribute("aria-label") || "",
    item: node.getAttribute("data-item-id") || ""
  })));
  const explicit = anchors.filter((anchor) => {
    const haystack = `${anchor.text} ${anchor.aria} ${anchor.item}`.toLowerCase();
    return haystack.includes("website") || haystack.includes("authority");
  });
  const pool = explicit.length ? explicit : anchors;
  output.websiteCandidates = pool
    .map((anchor) => unwrapUrl(anchor.href))
    .filter((href) => {
      const host = hostFor(href);
      return host && !host.includes("google.") && !host.includes("gstatic.");
    })
    .slice(0, 12);
  output.websiteMatched = output.websiteCandidates.some((href) => sameDomain(hostFor(href), expectedDomain));
  if (!output.websiteMatched) {
    console.log(JSON.stringify(output));
    await browser.close();
    return;
  }

  const reviewsTab = page.locator('button:has-text("Reviews"), div[role="tab"]:has-text("Reviews")').first();
  if (await reviewsTab.count().catch(() => 0)) {
    await reviewsTab.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(2500);
  }
  for (let i = 0; i < 4; i += 1) {
    await page.mouse.wheel(0, 1800);
    await page.waitForTimeout(500);
  }

  output.reviews = await page.$$eval("[data-review-id], .jftiEf", (nodes, maxReviews) => {
    function clean(value) {
      return String(value || "").replace(/\s+/g, " ").trim();
    }
    function firstText(root, selectors) {
      for (const selector of selectors) {
        const node = root.querySelector(selector);
        const text = clean(node && (node.innerText || node.textContent));
        if (text) return text;
      }
      return "";
    }
    return nodes.map((node) => {
      const ratingLabel = Array.from(node.querySelectorAll("[aria-label]"))
        .map((item) => item.getAttribute("aria-label") || "")
        .find((label) => /star/i.test(label)) || "";
      const ratingMatch = ratingLabel.match(/([0-9.]+)\s*(?:star|stars)/i);
      return {
        reviewerName: firstText(node, [".d4r55", ".WNxzHc", "[data-reviewer-name]"]),
        rating: ratingMatch ? Number.parseFloat(ratingMatch[1]) : null,
        reviewText: firstText(node, [".wiI7pd", ".MyEned", "[lang]"]),
      };
    }).filter((review) => review.reviewText && review.reviewText.length >= 25).slice(0, maxReviews);
  }, limit).catch(() => []);

  console.log(JSON.stringify(output));
  await browser.close();
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
"""
