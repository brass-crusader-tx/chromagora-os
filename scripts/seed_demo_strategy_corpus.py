#!/usr/bin/env python
"""Seed distilled Demo Factory strategy packs into framework tables."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
for rel in ["apps/api", "packages/schemas", "packages/config", "packages/shared"]:
    sys.path.insert(0, str(ROOT / rel))

from chromagora_api.db.tenant import get_active_tenant_id, get_backend_supabase
from chromagora_api.services.demo_frameworks import add_framework_pattern, upsert_framework_source


PACK_NAMES = [
    "offer_strategy_pack.yaml",
    "lead_strategy_pack.yaml",
    "money_model_pack.yaml",
    "avatar_pack.yaml",
]


def main() -> int:
    sb = get_backend_supabase()
    tenant_id = get_active_tenant_id(sb)
    pack_dir = Path(os.getenv("DEMO_FACTORY_STRATEGY_PACK_DIR") or ROOT / "apps/api/chromagora_api/strategy_knowledge")
    seeded = 0
    for name in PACK_NAMES:
        pack_path = pack_dir / name
        pack = yaml.safe_load(pack_path.read_text())
        source = upsert_framework_source(
            sb=sb,
            tenant_id=tenant_id,
            source_key=pack["source_key"],
            title=pack["title"],
            source_type="distilled_private_strategy_pack",
            license_scope="local_private_reference",
            metadata_json={"source_refs": pack.get("source_refs", []), "pack_path": str(pack_path)},
        )
        for pattern in pack.get("patterns", []):
            add_framework_pattern(
                sb=sb,
                tenant_id=tenant_id,
                source_id=source.get("id"),
                pattern_key=pattern["pattern_key"],
                title=pattern["title"],
                tags=pattern.get("tags", []),
                pattern_json=pattern.get("pattern_json", {}),
            )
            seeded += 1
    print(f"seeded_patterns={seeded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
