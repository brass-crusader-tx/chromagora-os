from __future__ import annotations

import json

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError


class SupabaseMock:
    def __init__(self):
        self.tables: dict[str, list[dict]] = {}

    def table(self, name: str):
        self.tables.setdefault(name, [])
        return QueryMock(self, name)


class QueryMock:
    def __init__(self, sb: SupabaseMock, table_name: str):
        self.sb = sb
        self.table_name = table_name
        self.filters: list[tuple[str, object]] = []
        self.in_filters: list[tuple[str, set]] = []
        self.order_col: str | None = None
        self.order_desc = False
        self.limit_count: int | None = None
        self.insert_payload = None
        self.update_payload = None

    def select(self, *_args):
        return self

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self.insert_payload = payload
        return self

    def update(self, payload):
        self.update_payload = payload
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def in_(self, column, values):
        self.in_filters.append((column, set(values)))
        return self

    def order(self, column, desc=False):
        self.order_col = column
        self.order_desc = desc
        return self

    def limit(self, count):
        self.limit_count = count
        return self

    def is_(self, column, value):
        if value == "null":
            self.filters.append((column, None))
        return self

    def execute(self):
        rows = self.sb.tables[self.table_name]
        if self.insert_payload is not None:
            payloads = self.insert_payload if isinstance(self.insert_payload, list) else [self.insert_payload]
            inserted = []
            for payload in payloads:
                row = dict(payload)
                row.setdefault("id", str(uuid4()))
                rows.append(row)
                inserted.append(row)
            return type("Resp", (), {"data": inserted})()

        matched = self._matched_rows(rows)
        if self.update_payload is not None:
            for row in matched:
                row.update(self.update_payload)
            return type("Resp", (), {"data": [dict(row) for row in matched]})()

        result = [dict(row) for row in matched]
        if self.order_col:
            result.sort(key=lambda row: (row.get(self.order_col) is None, row.get(self.order_col)), reverse=self.order_desc)
        if self.limit_count is not None:
            result = result[: self.limit_count]
        return type("Resp", (), {"data": result})()

    def _matched_rows(self, rows):
        result = rows
        for column, value in self.filters:
            result = [row for row in result if row.get(column) == value]
        for column, values in self.in_filters:
            result = [row for row in result if row.get(column) in values]
        return result


def test_csv_rows_rank_order_slug_and_unknown_columns_preserved():
    from chromagora_api.services.demo_factory_importer import normalize_csv_rows

    csv_bytes = (
        "Rank,Business Name,Website URL,Demo URL / Slug,Scoring Notes,Unknown Column\n"
        "2,Acme Roofing,acme-roofing.com,https://acme.demo.chromagora.com,roofing lead,keep me\n"
        "1,Beta Lawn,https://www.betalawn.com/path,,lawn lead,also keep\n"
    ).encode()

    rows = normalize_csv_rows(csv_bytes)

    assert [row.business_name for row in rows] == ["Beta Lawn", "Acme Roofing"]
    assert rows[0].row_number == 1
    assert rows[0].website_domain == "betalawn.com"
    assert rows[1].demo_slug == "acme"
    assert rows[1].raw_row_json["Unknown Column"] == "keep me"


def test_import_demo_csv_creates_batch_rows_and_projects():
    from chromagora_api.services.demo_factory_importer import import_demo_csv

    sb = SupabaseMock()
    tenant_id = uuid4()
    result = import_demo_csv(
        csv_bytes=b"Rank,Business Name,Website Domain\n1,Acme Roofing,acme.com\n",
        source_filename="leads.csv",
        tenant_id=tenant_id,
        sb=sb,
    )

    assert result["batch"]["source_filename"] == "leads.csv"
    assert len(sb.tables["demo_site_batches"]) == 1
    assert len(sb.tables["demo_site_batch_rows"]) == 1
    assert len(sb.tables["demo_site_projects"]) == 1
    assert sb.tables["demo_site_batch_rows"][0]["project_id"] == sb.tables["demo_site_projects"][0]["id"]


def test_import_demo_link_drop_creates_one_row_batch_and_project():
    from chromagora_api.services.demo_link_drop_importer import DemoLinkDropInput, import_demo_link_drop

    sb = SupabaseMock()
    tenant_id = uuid4()
    result = import_demo_link_drop(
        payload=DemoLinkDropInput(
            website_url="example.com/?utm_source=test&ref=keep",
            suggested_demo_cta="Text a photo for a quote",
            demo_angle="Make the estimate path obvious",
        ),
        tenant_id=tenant_id,
        sb=sb,
    )

    assert result["projects_created"] == 1
    assert result["batch"]["metadata_json"]["intake_type"] == "link_drop"
    assert result["batch"]["metadata_json"]["source_url"] == "https://example.com?ref=keep"
    assert len(sb.tables["demo_site_batch_rows"]) == 1
    assert len(sb.tables["demo_site_projects"]) == 1
    project = sb.tables["demo_site_projects"][0]
    assert project["source_url"] == "https://example.com?ref=keep"
    assert project["normalized_domain"] == "example.com"
    assert project["input_row_json"]["_intake_type"] == "link_drop"
    assert result["project_url"] == f"/demo-factory/projects/{project['id']}"


@pytest.mark.parametrize(
    "url",
    [
        "localhost:3000",
        "http://127.0.0.1",
        "http://10.0.0.5",
        "http://172.16.0.1",
        "http://192.168.1.10",
        "file:///tmp/site.html",
        "javascript:alert(1)",
        "data:text/html,hello",
    ],
)
def test_import_demo_link_drop_rejects_private_or_invalid_url(url):
    from chromagora_api.services.demo_link_drop_importer import DemoLinkDropInput, import_demo_link_drop

    with pytest.raises(ValueError):
        import_demo_link_drop(
            payload=DemoLinkDropInput(website_url=url),
            tenant_id=uuid4(),
            sb=SupabaseMock(),
        )


def test_import_demo_link_drop_preserves_operator_notes():
    from chromagora_api.services.demo_link_drop_importer import DemoLinkDropInput, import_demo_link_drop

    sb = SupabaseMock()
    result = import_demo_link_drop(
        payload=DemoLinkDropInput(
            website_url="https://example.org",
            business_name="Cedar Plumbing",
            suggested_demo_cta="Request a plumbing callback",
            demo_angle="Reduce callback friction",
            before_after_slider_angle="Reveal a cleaner callback path",
            backend_hook="Follow up missed calls",
            verify_before_build=False,
            auto_start=False,
        ),
        tenant_id=uuid4(),
        sb=sb,
    )

    row = result["rows"][0]
    assert row["business_name"] == "Cedar Plumbing"
    assert row["raw_row_json"]["Suggested Demo CTA"] == "Request a plumbing callback"
    assert row["raw_row_json"]["Demo Angle"] == "Reduce callback friction"
    assert row["raw_row_json"]["Before/After Slider Angle"] == "Reveal a cleaner callback path"
    assert row["raw_row_json"]["Backend Hook"] == "Follow up missed calls"
    assert result["batch"]["metadata_json"]["auto_start"] is False
    assert sb.tables["demo_site_projects"][0]["verify_before_build"] is False


def test_link_drop_slug_dedupes_against_existing_projects():
    from chromagora_api.services.demo_link_drop_importer import DemoLinkDropInput, import_demo_link_drop

    sb = SupabaseMock()
    tenant_id = uuid4()
    sb.tables["demo_site_projects"] = [
        {"id": str(uuid4()), "tenant_id": str(tenant_id), "demo_slug": "acme-roofing"},
        {"id": str(uuid4()), "tenant_id": str(tenant_id), "demo_slug": "acme-roofing-2"},
    ]
    import_demo_link_drop(
        payload=DemoLinkDropInput(website_url="https://acme-roofing.com", business_name="Acme Roofing"),
        tenant_id=tenant_id,
        sb=sb,
    )

    assert sb.tables["demo_site_projects"][-1]["demo_slug"] == "acme-roofing-3"


def test_get_next_row_respects_retryable_order():
    from chromagora_workers.demo_factory.batch_processor import get_next_row

    sb = SupabaseMock()
    batch_id = str(uuid4())
    sb.tables["demo_site_batch_rows"] = [
        {"id": "1", "batch_id": batch_id, "row_number": 1, "status": "published"},
        {"id": "2", "batch_id": batch_id, "row_number": 2, "status": "failed_retryable"},
        {"id": "3", "batch_id": batch_id, "row_number": 3, "status": "queued"},
    ]

    assert get_next_row(sb, batch_id)["id"] == "2"


def test_recover_stale_running_rows_marks_retryable():
    from chromagora_workers.demo_factory.batch_processor import recover_stale_running_rows

    sb = SupabaseMock()
    project_id = str(uuid4())
    sb.tables["demo_site_batch_rows"] = [
        {
            "id": "row-1",
            "project_id": project_id,
            "status": "running",
            "started_at": "2026-01-01T00:00:00+00:00",
        }
    ]
    sb.tables["demo_site_projects"] = [{"id": project_id, "status": "crawling"}]

    assert recover_stale_running_rows(sb, older_than_minutes=5) == 1
    assert sb.tables["demo_site_batch_rows"][0]["status"] == "failed_retryable"
    assert sb.tables["demo_site_projects"][0]["status"] == "failed_retryable"


def test_maybe_complete_batch_emits_event():
    from chromagora_workers.demo_factory.batch_processor import maybe_complete_batch

    sb = SupabaseMock()
    tenant_id = str(uuid4())
    batch_id = str(uuid4())
    sb.tables["demo_site_batches"] = [{"id": batch_id, "tenant_id": tenant_id, "status": "running"}]
    sb.tables["demo_site_batch_rows"] = [
        {"id": "1", "batch_id": batch_id, "row_number": 1, "status": "published"},
        {"id": "2", "batch_id": batch_id, "row_number": 2, "status": "failed_terminal"},
    ]

    assert maybe_complete_batch(sb, batch_id) is True
    assert sb.tables["demo_site_batches"][0]["status"] == "completed"
    assert sb.tables["events"][0]["event_type"] == "demo_site.batch_completed"


def test_worker_marks_terminal_after_max_attempts(monkeypatch):
    from chromagora_workers import demo_factory_worker

    sb = SupabaseMock()
    tenant_id = str(uuid4())
    batch_id = str(uuid4())
    project_id = str(uuid4())
    sb.tables["demo_site_batches"] = [{"id": batch_id, "tenant_id": tenant_id, "status": "running"}]
    sb.tables["demo_site_batch_rows"] = [
        {
            "id": "row-1",
            "batch_id": batch_id,
            "project_id": project_id,
            "row_number": 1,
            "status": "failed_retryable",
            "attempt_count": 2,
        }
    ]
    sb.tables["demo_site_projects"] = [{"id": project_id, "tenant_id": tenant_id, "status": "queued"}]
    monkeypatch.setenv("DEMO_FACTORY_MAX_ROW_ATTEMPTS", "3")
    monkeypatch.setattr(demo_factory_worker, "_get_supabase", lambda: sb)
    monkeypatch.setattr(demo_factory_worker, "process_project", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    result = demo_factory_worker.run_batch_cycle(auto_start=False)

    assert result["status"] == "failed_terminal"
    assert sb.tables["demo_site_batch_rows"][0]["attempt_count"] == 3
    assert sb.tables["demo_site_batch_rows"][0]["status"] == "failed_terminal"


def test_site_spec_validates_section_types():
    from chromagora_schemas.demo_factory import (
        BeforeAfterRevealConfig,
        BrandConfig,
        CTAConfig,
        SitePageSpec,
        SiteSectionSpec,
        SiteSpec,
    )

    project_id = uuid4()
    spec = SiteSpec(
        project_id=project_id,
        business_name="Acme",
        business_vertical="Roofing",
        brand=BrandConfig(),
        pages=[SitePageSpec(title="Home", sections=[SiteSectionSpec(type="hero", section_id="hero")])],
        primary_cta=CTAConfig(label="Call", href="#contact"),
    )
    assert spec.pages[0].sections[0].type == "hero"
    reveal = BeforeAfterRevealConfig(
        enabled=True,
        before_image_url="/old-desktop.png",
        before_desktop_image_url="/old-desktop.png",
        before_mobile_image_url="/old-mobile.png",
    )
    assert reveal.before_mobile_image_url == "/old-mobile.png"

    with pytest.raises(ValidationError):
        SiteSectionSpec(type="generated_react", section_id="bad")


def test_review_identity_scoring():
    from chromagora_schemas.demo_factory import score_review_identity_match

    score = score_review_identity_match(
        {
            "business_name_match": True,
            "phone_match": True,
            "website_match": False,
            "location_service_area_match": True,
            "category_match": False,
        }
    )
    assert score == pytest.approx(0.70)


def test_crawler_extracts_business_site_testimonials():
    from chromagora_workers.demo_factory.site_crawler import DemoHTMLParser, _extract_testimonial_candidates

    parser = DemoHTMLParser()
    parser.feed(
        """
        <html>
          <head><title>Testimonials</title></head>
          <body>
            <h1>What Clients Say</h1>
            <p>They did an excellent job and were professional, on time, and easy to work with.</p>
            <p>Jordan Smith</p>
          </body>
        </html>
        """
    )

    candidates = _extract_testimonial_candidates(
        parser.page,
        "https://example.com/testimonials",
        "reviews",
        "Example Lawn",
    )

    assert candidates
    assert candidates[0]["source_name"] == "business_site"
    assert candidates[0]["source_url"] == "https://example.com/testimonials"
    assert candidates[0]["identity_match_signals"]["website_match"] is True


def test_crawler_treats_provider_secret_as_brightdata(monkeypatch):
    from chromagora_workers.demo_factory import site_crawler

    monkeypatch.setenv("DEMO_FACTORY_CRAWLER_PROVIDER", "brd_secret_value")
    monkeypatch.delenv("DEMO_FACTORY_BRIGHTDATA_API_KEY", raising=False)

    assert site_crawler._crawler_provider() == "brightdata"
    assert site_crawler._brightdata_api_key() == "brd_secret_value"


def test_review_agent_uses_grounded_site_testimonials(monkeypatch):
    from chromagora_workers.demo_factory.agents import review_evidence_agent

    monkeypatch.setattr(
        review_evidence_agent,
        "call_agent_model",
        lambda *_args, **_kwargs: {"mock": True, "content": {}},
    )

    block = review_evidence_agent.run_review_evidence_agent(
        project_id=uuid4(),
        evidence_bundle={
            "business_name": "Example Lawn",
            "source_domain": "example.com",
            "review_source_candidates": [
                {
                    "source_name": "business_site",
                    "source_url": "https://example.com/testimonials",
                    "reviewer_name": "Jordan Smith",
                    "review_text": "They did an excellent job and were professional, on time, and easy to work with.",
                    "identity_match_signals": {
                        "business_name_match": True,
                        "website_match": True,
                    },
                    "confidence_score": 0.8,
                }
            ],
        },
    )

    assert block.omit_review_section is False
    assert len(block.selected_reviews) == 1
    assert block.selected_reviews[0].source_url == "https://example.com/testimonials"


def test_google_maps_reviews_require_matching_profile_website(monkeypatch):
    from chromagora_workers.demo_factory import google_maps_reviews

    def fake_run(*_args, **_kwargs):
        return type(
            "Completed",
            (),
            {
                "stdout": json.dumps(
                    {
                        "websiteMatched": True,
                        "profileUrl": "https://www.google.com/maps/place/Example",
                        "websiteCandidates": ["https://example.com"],
                        "reviews": [
                            {
                                "reviewerName": "Taylor",
                                "rating": 5,
                                "reviewText": "Great service and a professional crew from start to finish.",
                            }
                        ],
                    }
                )
            },
        )()

    monkeypatch.delenv("DEMO_FACTORY_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("DEMO_FACTORY_CRAWLER_PROVIDER", raising=False)
    monkeypatch.setenv("DEMO_FACTORY_GOOGLE_MAPS_REVIEWS_ENABLED", "true")
    monkeypatch.setattr(google_maps_reviews.subprocess, "run", fake_run)

    reviews = google_maps_reviews.find_google_maps_reviews(
        {
            "business_name": "Example Lawn",
            "source_domain": "example.com",
            "service_candidates": ["Lawn Care"],
        }
    )

    assert len(reviews) == 1
    assert reviews[0]["source_name"] == "google_maps"
    assert reviews[0]["identity_match_signals"]["website_match"] is True


def test_supervisor_timeout_and_rate_limit_handling():
    from chromagora_workers.demo_factory.supervisor import classify_stage_timeout, handle_rate_limit

    assert classify_stage_timeout("visual_qa", 899) == "ok"
    assert classify_stage_timeout("visual_qa", 900) == "soft_timeout"
    assert classify_stage_timeout("visual_qa", 1800) == "hard_timeout"

    sb = SupabaseMock()
    tenant_id = uuid4()
    project_id = str(uuid4())
    batch_id = str(uuid4())
    sb.tables["demo_site_projects"] = [{"id": project_id, "tenant_id": str(tenant_id), "status": "qa"}]
    sb.tables["demo_site_batches"] = [{"id": batch_id, "tenant_id": str(tenant_id), "status": "running"}]

    result = handle_rate_limit(
        sb=sb,
        tenant_id=tenant_id,
        project_id=project_id,
        batch_id=batch_id,
        stage="brand_synthesis",
        cooldown_seconds=120,
    )

    assert result["status"] == "waiting_rate_limit"
    assert sb.tables["demo_site_projects"][0]["status"] == "waiting_rate_limit"
    assert sb.tables["demo_site_batches"][0]["status"] == "paused"
    assert sb.tables["demo_factory_supervisor_events"][0]["event_type"] == "provider_rate_limited"


def test_model_gateway_mock_mode(monkeypatch):
    from chromagora_workers.demo_factory import model_gateway

    sb = SupabaseMock()
    tenant_id = str(uuid4())
    project_id = uuid4()
    sb.tables["demo_site_projects"] = [{"id": str(project_id), "tenant_id": tenant_id, "batch_id": None}]
    monkeypatch.setenv("DEMO_FACTORY_MODEL_PROVIDER", "mock")
    monkeypatch.setattr(model_gateway, "_get_supabase", lambda: sb)

    result = model_gateway.call_agent_model(
        "brand_synthesis",
        project_id,
        "brand_synthesis",
        "system",
        {"business_name": "Acme"},
        {},
        temperature=0,
        max_tokens=100,
        timeout_seconds=30,
    )

    assert result["mock"] is True
    assert sb.tables["demo_model_calls"][0]["status"] == "succeeded"


def test_model_gateway_nvidia_provider(monkeypatch):
    from chromagora_workers.demo_factory import model_gateway

    sb = SupabaseMock()
    tenant_id = str(uuid4())
    project_id = uuid4()
    captured = {}
    sb.tables["demo_site_projects"] = [{"id": str(project_id), "tenant_id": tenant_id, "batch_id": None}]
    monkeypatch.setenv("DEMO_FACTORY_MODEL_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia-key")
    monkeypatch.setenv("DEMO_FACTORY_PRIMARY_MODEL", "minimaxai/minimax-m3")
    monkeypatch.delenv("DEMO_FACTORY_FALLBACK_MODEL", raising=False)
    monkeypatch.setattr(model_gateway, "_get_supabase", lambda: sb)

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({"ok": True})}}]}

    class FakeClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, url, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr(model_gateway.httpx, "Client", FakeClient)

    result = model_gateway.call_agent_model(
        "brand_synthesis",
        project_id,
        "brand_synthesis",
        "system",
        {"business_name": "Acme"},
        {"type": "object"},
        temperature=0,
        max_tokens=100,
        timeout_seconds=30,
    )

    assert result == {"ok": True}
    assert captured["url"] == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert captured["payload"]["model"] == "minimaxai/minimax-m3"
    assert captured["headers"]["Authorization"] == "Bearer test-nvidia-key"
    assert sb.tables["demo_model_calls"][0]["model"] == "minimaxai/minimax-m3"
    assert sb.tables["demo_model_calls"][0]["status"] == "succeeded"


def test_mocked_pipeline_creates_spec_qa_and_deployment(monkeypatch):
    from chromagora_api.services.demo_factory_importer import import_demo_csv
    from chromagora_workers.demo_factory import model_gateway
    from chromagora_workers.demo_factory.orchestrator import process_project

    sb = SupabaseMock()
    tenant_id = uuid4()
    import_demo_csv(
        csv_bytes=b"Rank,Business Name,Website Domain,Suggested Demo CTA\n1,Acme Roofing,acme.com,Request a roof quote\n",
        source_filename="leads.csv",
        tenant_id=tenant_id,
        sb=sb,
    )
    project = sb.tables["demo_site_projects"][0]
    monkeypatch.setenv("DEMO_FACTORY_MODEL_PROVIDER", "mock")
    monkeypatch.setenv("DEMO_FACTORY_CRAWLER_PROVIDER", "mock")
    monkeypatch.setenv("DEMO_FACTORY_VISUAL_QA_REQUIRED", "false")
    monkeypatch.delenv("DEMO_FACTORY_RENDER_BASE_URL", raising=False)
    monkeypatch.delenv("DEMO_FACTORY_PUBLIC_BASE_URL", raising=False)
    monkeypatch.setattr(model_gateway, "_get_supabase", lambda: sb)

    result = process_project(UUID(project["id"]), sb=sb)

    assert result["status"] == "published"
    assert sb.tables["demo_site_specs"][0]["status"] == "published"
    assert sb.tables["demo_site_specs"][0]["is_current"] is True
    assert sb.tables["demo_site_qa_reports"]
    assert sb.tables["demo_site_deployments"][0]["status"] == "published"
    assert sb.tables["demo_site_projects"][0]["status"] == "published"
