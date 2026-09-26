#!/usr/bin/env python3
"""Fetch the exact TSUNAMI UI Genesis APK pair from the public JitPack mirror.

This is a transport/build fallback for environments where the private repository's GitHub Actions
cannot allocate a job and the local Codespaces broker is unavailable. It does not trust a mutable
branch name: it resolves the public mirror branch to a commit, verifies every manifest-listed blob
against the current private worktree's Git object IDs and byte sizes, triggers/polls JitPack for
that immutable mirror commit, downloads both APKs, validates their ZIP structure, and emits a
source-contract manifest under dist/.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dist"
PUBLIC_REPO="https://github.com/brass-crusader-tx/chromagora-os.git"
PUBLIC_OWNER="brass-crusader-tx"
PUBLIC_ARTIFACT="chromagora-os"
PUBLIC_BRANCH="build/tsunami-ui-genesis-20260925"
MIRROR_MANIFEST_PATH="tsunami-builder/MIRROR-MANIFEST.json"
JITPACK="https://jitpack.io"
GROUP_PATH="com/github/brass-crusader-tx/chromagora-os"


class BuildError(RuntimeError):
    pass


def run(cmd:list[str], *, capture:bool=False)->subprocess.CompletedProcess[str]:
    cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=capture)
    if cp.returncode:
        tail=((cp.stdout or "")+(cp.stderr or ""))[-6000:]
        raise BuildError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{tail}")
    return cp


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def http_bytes(url:str, *, timeout:float=60)->bytes:
    req=Request(url,headers={"User-Agent":"TSUNAMI-UI-Genesis-builder/1.0"})
    with urlopen(req,timeout=timeout) as r:
        if r.status != 200:
            raise BuildError(f"HTTP {r.status}: {url}")
        return r.read()


def resolve_mirror_head()->str:
    cp=run(["git","ls-remote",PUBLIC_REPO,f"refs/heads/{PUBLIC_BRANCH}"],capture=True)
    row=cp.stdout.strip().split()
    if len(row)!=2 or len(row[0])!=40:
        raise BuildError(f"unable to resolve public mirror branch: {cp.stdout!r}")
    return row[0]


def manifest_for(mirror_sha:str)->dict:
    url=f"https://raw.githubusercontent.com/{PUBLIC_OWNER}/chromagora-os/{mirror_sha}/{MIRROR_MANIFEST_PATH}"
    data=json.loads(http_bytes(url,timeout=30).decode("utf-8"))
    if data.get("mirror_branch")!=PUBLIC_BRANCH:
        raise BuildError(f"unexpected mirror branch in manifest: {data.get('mirror_branch')!r}")
    return data


def current_blob(path:str)->tuple[str,int]:
    cp=run(["git","ls-tree","HEAD","--",path],capture=True)
    fields=cp.stdout.strip().split()
    if len(fields)<4:
        raise BuildError(f"current source path is not tracked: {path}")
    blob=fields[2]
    size=int(run(["git","cat-file","-s",blob],capture=True).stdout.strip())
    return blob,size


def verify_source_contract(manifest:dict)->dict:
    mismatches=[]
    entries=list(manifest.get("files") or [])+list(manifest.get("support_files") or [])
    if not entries:
        raise BuildError("mirror manifest contains no contract entries")
    for item in entries:
        path=str(item["path"])
        expected_sha=str(item["git_blob_sha"])
        expected_bytes=int(item["bytes"])
        try:
            actual_sha,actual_bytes=current_blob(path)
        except Exception as exc:
            mismatches.append({"path":path,"error":str(exc)})
            continue
        if actual_sha!=expected_sha or actual_bytes!=expected_bytes:
            mismatches.append({
                "path":path,
                "expected_sha":expected_sha,
                "actual_sha":actual_sha,
                "expected_bytes":expected_bytes,
                "actual_bytes":actual_bytes,
            })
    if mismatches:
        raise BuildError("public mirror is stale against current build-critical source: "+json.dumps(mismatches[:8],sort_keys=True))
    return {"entries":len(entries),"mismatches":0}


def api_build(version:str)->dict|None:
    url=f"{JITPACK}/api/builds/com.github.brass-crusader-tx/{PUBLIC_ARTIFACT}/{version}"
    try:
        data=json.loads(http_bytes(url,timeout=30).decode("utf-8"))
    except HTTPError as exc:
        if exc.code==404:
            return None
        raise
    except (URLError,TimeoutError,json.JSONDecodeError):
        return None
    return data


def api_status(version:str)->tuple[str|None,str|None]:
    data=api_build(version)
    if not data:
        return None,None
    node=data.get("com.github.brass-crusader-tx",{}).get(PUBLIC_ARTIFACT,{})
    value=node.get(version)
    status=value if isinstance(value,str) else None
    if status is None:
        for key in ("status","outcome","state"):
            value=data.get(key)
            if isinstance(value,str):
                status=value
                break
    commit=data.get("commit")
    return status,(commit if isinstance(commit,str) else None)


def trigger_and_wait(mirror_sha:str, timeout_s:int)->str:
    # JitPack documents short commit hashes as canonical ad-hoc versions, but current
    # deployments also accept full SHAs. Probe both while keeping the source contract
    # bound to the full 40-character mirror commit.
    versions=(mirror_sha,mirror_sha[:10])
    deadline=time.monotonic()+timeout_s
    last={}
    while time.monotonic()<deadline:
        for version in versions:
            pom=f"{JITPACK}/{GROUP_PATH}/{version}/{PUBLIC_ARTIFACT}-{version}.pom"
            try:
                http_bytes(pom,timeout=90)
                print(f"JITPACK_VERSION={version}",flush=True)
                return version
            except HTTPError as exc:
                if exc.code not in {401,404,409,500,502,503,504}:
                    raise
            except (URLError,TimeoutError):
                pass

            status,commit=api_status(version)
            marker=(status,commit)
            if marker!=last.get(version):
                print(f"JITPACK_STATUS version={version} status={status or 'pending'} commit={commit or 'unknown'}",flush=True)
                last[version]=marker
            normalized=(status or "").lower()
            if commit and not mirror_sha.startswith(commit) and not commit.startswith(mirror_sha):
                raise BuildError(f"JitPack version {version} resolved unexpected commit {commit}; expected {mirror_sha}")
            if normalized in {"ok","success","successful","built"}:
                print(f"JITPACK_VERSION={version}",flush=True)
                return version
            if normalized in {"error","failed","failure"}:
                log=f"{JITPACK}/{GROUP_PATH}/{version}/build.log"
                try:
                    detail=http_bytes(log,timeout=30).decode("utf-8","replace")[-12000:]
                except Exception:
                    detail="(build log unavailable)"
                raise BuildError(f"JitPack build failed for {version} ({mirror_sha})\n{detail}")
        time.sleep(8)
    raise BuildError(f"JitPack did not produce build {mirror_sha} (full or short version) within {timeout_s}s")


def validate_apk(path:Path)->None:
    if not path.is_file() or path.stat().st_size<100_000:
        raise BuildError(f"APK is missing or implausibly small: {path}")
    with zipfile.ZipFile(path) as zf:
        names=set(zf.namelist())
        if "AndroidManifest.xml" not in names:
            raise BuildError(f"{path.name}: AndroidManifest.xml missing")
        if not any(n=="classes.dex" or (n.startswith("classes") and n.endswith(".dex")) for n in names):
            raise BuildError(f"{path.name}: no DEX payload")


def download_artifacts(version:str)->tuple[Path,Path]:
    OUT.mkdir(parents=True,exist_ok=True)
    base=f"{JITPACK}/{GROUP_PATH}/{version}/{PUBLIC_ARTIFACT}-{version}"
    pairs=[
        (f"{base}.apk",OUT/"TSUNAMI-UI-Genesis-debug.apk"),
        (f"{base}-androidTest.apk",OUT/"TSUNAMI-UI-Genesis-debug-androidTest.apk"),
    ]
    for url,dest in pairs:
        tmp=dest.with_suffix(dest.suffix+".tmp")
        tmp.write_bytes(http_bytes(url,timeout=180))
        validate_apk(tmp)
        tmp.replace(dest)
    return pairs[0][1],pairs[1][1]


def main()->int:
    timeout_s=int(os.environ.get("TSUNAMI_JITPACK_TIMEOUT","1200"))
    source_head=run(["git","rev-parse","HEAD"],capture=True).stdout.strip()
    dirty=run([
        "git","status","--porcelain","--untracked-files=all","--",
        "ui-shell","brand","docs/TSUNAMI-UI-GENESIS-RESEARCH.md",
        "docs/TSUNAMI-UI-GENESIS-COVERAGE.md","docs/TSUNAMI-SANS-v5.1-MANIFEST.json",
        "tools/ui_shell_gate.py","tools/ui_shell_static_check.py",
    ],capture=True).stdout.strip()
    if dirty:
        raise BuildError("refusing JitPack artifact binding from dirty build-critical source")

    mirror_sha=resolve_mirror_head()
    manifest=manifest_for(mirror_sha)
    contract=verify_source_contract(manifest)
    print(f"MIRROR_CONTRACT=PASS entries={contract['entries']} mirror={mirror_sha}")
    jitpack_version=trigger_and_wait(mirror_sha,timeout_s)
    app,test=download_artifacts(jitpack_version)
    evidence={
        "status":"BUILT",
        "backend":"jitpack-public-mirror",
        "source_head":source_head,
        "mirror_manifest_source_head":manifest.get("source_head"),
        "source_contract_match":True,
        "source_contract_entries":contract["entries"],
        "mirror_repository":"brass-crusader-tx/chromagora-os",
        "mirror_branch":PUBLIC_BRANCH,
        "mirror_commit":mirror_sha,
        "jitpack_version":jitpack_version,
        "app_apk":str(app.relative_to(ROOT)),
        "app_bytes":app.stat().st_size,
        "app_sha256":sha256(app),
        "test_apk":str(test.relative_to(ROOT)),
        "test_apk_bytes":test.stat().st_size,
        "test_apk_sha256":sha256(test),
    }
    (OUT/"jitpack-build.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","backend":"jitpack-public-mirror","error":str(exc)}),file=sys.stderr)
        raise SystemExit(2)
