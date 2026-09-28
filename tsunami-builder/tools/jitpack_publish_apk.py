#!/usr/bin/env python3
"""Install the exact UI Genesis APK pair into JitPack's local Maven repository.

This is a build-transport adapter only. It never modifies mirrored TSUNAMI source.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
dist = root / "dist"
main_apk = dist / "TSUNAMI-UI-Genesis-debug.apk"
test_apk = dist / "TSUNAMI-UI-Genesis-debug-androidTest.apk"
for p in (main_apk, test_apk):
    if not p.is_file() or p.stat().st_size == 0:
        raise SystemExit(f"missing build artifact: {p}")

group = os.environ.get("GROUP", "com.github.brass-crusader-tx")
artifact = os.environ.get("ARTIFACT", "chromagora-os")
version = os.environ.get("VERSION") or os.environ.get("GIT_COMMIT")
if not version:
    raise SystemExit("VERSION/GIT_COMMIT is required")

m2 = Path.home() / ".m2" / "repository" / Path(*group.split(".")) / artifact / version
m2.mkdir(parents=True, exist_ok=True)
main_dst = m2 / f"{artifact}-{version}.apk"
test_dst = m2 / f"{artifact}-{version}-androidTest.apk"
shutil.copy2(main_apk, main_dst)
shutil.copy2(test_apk, test_dst)

project = ET.Element("project", {"xmlns": "http://maven.apache.org/POM/4.0.0"})
for tag, value in (
    ("modelVersion", "4.0.0"),
    ("groupId", group),
    ("artifactId", artifact),
    ("version", version),
    ("packaging", "apk"),
    ("name", "TSUNAMI UI Genesis"),
    ("description", "Backend-free TSUNAMI UI Genesis shell APK"),
):
    ET.SubElement(project, tag).text = value
pom = m2 / f"{artifact}-{version}.pom"
ET.ElementTree(project).write(pom, encoding="utf-8", xml_declaration=True)

for p in (main_dst, test_dst, pom):
    sha = hashlib.sha1(p.read_bytes()).hexdigest()
    (p.with_name(p.name + ".sha1")).write_text(sha + "\n", encoding="ascii")

print(f"JITPACK_MAVEN_INSTALL=PASS group={group} artifact={artifact} version={version}")
print(f"MAIN_APK={main_dst} bytes={main_dst.stat().st_size} sha256={hashlib.sha256(main_dst.read_bytes()).hexdigest()}")
print(f"TEST_APK={test_dst} bytes={test_dst.stat().st_size} sha256={hashlib.sha256(test_dst.read_bytes()).hexdigest()}")
