#!/usr/bin/env python
"""Run a local Demo Factory golden-path smoke test.

The default `--mock` path uses an in-memory Supabase-compatible stub so it does
not require the remote Supabase schema to be available.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4


ROOT = Path(__file__).resolve().parents[1]
for rel in ["apps/api", "apps/workers", "packages/schemas", "packages/config", "packages/shared"]:
    sys.path.insert(0, str(ROOT / rel))


class SupabaseSmoke:
    def __init__(self):
        self.tables: dict[str, list[dict]] = {}

    def table(self, name: str):
        self.tables.setdefault(name, [])
        return QuerySmoke(self, name)


class QuerySmoke:
    def __init__(self, sb: SupabaseSmoke, table_name: str):
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


def run_smoke(*, mock: bool, real_crawl: bool) -> int:
    if mock:
        os.environ["DEMO_FACTORY_MODEL_PROVIDER"] = "mock"
        if not real_crawl:
            os.environ["DEMO_FACTORY_CRAWLER_PROVIDER"] = "mock"
            os.environ["DEMO_FACTORY_DISABLE_SCREENSHOTS"] = "true"
        os.environ["DEMO_FACTORY_VISUAL_QA_REQUIRED"] = "false"
        os.environ.pop("DEMO_FACTORY_RENDER_BASE_URL", None)
        os.environ.pop("DEMO_FACTORY_PUBLIC_BASE_URL", None)

    from chromagora_api.services.demo_factory_importer import import_demo_csv
    from chromagora_workers.demo_factory import model_gateway
    from chromagora_workers.demo_factory.batch_processor import (
        get_next_row,
        mark_row_failed_retryable,
        mark_row_published,
        mark_row_running,
        maybe_complete_batch,
        update_batch_counts,
    )
    from chromagora_workers.demo_factory.orchestrator import process_project

    sb = SupabaseSmoke()
    model_gateway._get_supabase = lambda: sb
    tenant_id = uuid4()
    fixture_path = ROOT / "fixtures" / "demo_factory" / "golden-path-3.csv"
    result = import_demo_csv(
        csv_bytes=fixture_path.read_bytes(),
        source_filename=fixture_path.name,
        tenant_id=tenant_id,
        sb=sb,
    )
    batch_id = result["batch"]["id"]
    sb.table("demo_site_batches").update({"status": "running"}).eq("id", batch_id).execute()

    processed = 0
    while True:
        row = get_next_row(sb, batch_id)
        if not row:
            update_batch_counts(sb, batch_id)
            maybe_complete_batch(sb, batch_id)
            break
        mark_row_running(sb, row["id"])
        try:
            process_project(UUID(row["project_id"]), sb=sb)
            mark_row_published(sb, row["id"])
            processed += 1
        except Exception as exc:
            mark_row_failed_retryable(sb, row["id"], str(exc))
            print(f"FAILED row={row.get('row_number')} project={row.get('project_id')} error={exc}")
        update_batch_counts(sb, batch_id)

    batch = sb.tables["demo_site_batches"][0]
    rows = sb.tables["demo_site_batch_rows"]
    projects = sb.tables["demo_site_projects"]
    specs = sb.tables.get("demo_site_specs", [])
    deployments = sb.tables.get("demo_site_deployments", [])
    qa_reports = sb.tables.get("demo_site_qa_reports", [])
    print(f"batch={batch_id} status={batch.get('status')} processed={processed}/{len(rows)}")
    print(f"rows={[(row['row_number'], row['status']) for row in rows]}")
    print(f"projects={[(project['business_name'], project['status'], '/demo/' + project['demo_slug']) for project in projects]}")
    print(f"specs={len(specs)} deployments={len(deployments)} qa_reports={len(qa_reports)}")

    failed = [row for row in rows if row.get("status") != "published"]
    if failed or len(specs) != len(rows) or len(deployments) != len(rows) or not qa_reports:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo Factory golden-path smoke test")
    parser.add_argument("--mock", action="store_true", help="Use mock model/crawler defaults")
    parser.add_argument("--real-crawl", action="store_true", help="Use the real crawler while keeping model calls mockable")
    args = parser.parse_args()
    return run_smoke(mock=args.mock or not args.real_crawl, real_crawl=args.real_crawl)


if __name__ == "__main__":
    raise SystemExit(main())
