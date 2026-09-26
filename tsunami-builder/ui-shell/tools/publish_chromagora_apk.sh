#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SHELL_ROOT="$ROOT/ui-shell"
DIST="$ROOT/dist"
BUILT="$DIST/TSUNAMI-UI-Genesis-debug.apk"
CODESPACE_MANIFEST="$DIST/codespace-build.json"
# The live Chromagora gateway serves from the primary TSUNAMI worktree, not necessarily
# from the current linked worktree. Resolve Git's common directory so Genesis worktrees
# publish to the same stable portal path as the primary checkout.
GIT_COMMON_DIR="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
if [[ -n "$GIT_COMMON_DIR" && "$(basename "$GIT_COMMON_DIR")" == ".git" ]]; then
  PORTAL_REPO_ROOT="$(cd "$GIT_COMMON_DIR/.." && pwd -P)"
else
  PORTAL_REPO_ROOT="$ROOT"
fi
TARGET="${TSUNAMI_PORTAL_APK_TARGET:-$PORTAL_REPO_ROOT/dist/TSUNAMI-UI-Shell-Rebrand-v1-debug.apk}"
MANIFEST="${TARGET}.json"
BUILD_BACKEND=""

mkdir -p "$DIST"
START_HEAD="$(git -C "$ROOT" rev-parse HEAD)"

# First prove the current source contract. A stale or dirty APK is never silently republished.
python3 "$ROOT/tools/ui_shell_static_check.py"
python3 "$SHELL_ROOT/tools/source_verify.py"
python3 "$SHELL_ROOT/tools/accessibility_verify.py"
if [[ -n "$(git -C "$ROOT" status --porcelain --untracked-files=all -- ui-shell brand docs/TSUNAMI-UI-GENESIS-RESEARCH.md docs/TSUNAMI-UI-GENESIS-COVERAGE.md tools/ui_shell_gate.py tools/ui_shell_static_check.py tools/ui_shell_codespace_build.py)" ]]; then
  echo "ERROR: refusing portal publish from dirty UI Genesis source." >&2
  exit 2
fi

host_build() {
  bash "$SHELL_ROOT/tools/build_host.sh"
}

codespace_build() {
  python3 "$ROOT/tools/ui_shell_codespace_build.py"
}

if [[ "${TSUNAMI_FORCE_CODESPACE_BUILD:-0}" == "1" ]]; then
  echo "Publishing through Codespaces because TSUNAMI_FORCE_CODESPACE_BUILD=1"
  codespace_build
  BUILD_BACKEND="github-codespaces"
else
  echo "Attempting canonical host build first"
  if host_build; then
    BUILD_BACKEND="host"
  else
    echo "Host build unavailable; falling back to the repository Codespaces builder" >&2
    rm -f "$BUILT"
    codespace_build
    BUILD_BACKEND="github-codespaces"
  fi
fi

test -s "$BUILT" || {
  echo "ERROR: current-head UI Genesis APK was not produced at $BUILT" >&2
  exit 3
}

SOURCE_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
if [[ "$SOURCE_HEAD" != "$START_HEAD" ]]; then
  echo "ERROR: Genesis HEAD changed during build ($START_HEAD -> $SOURCE_HEAD); refusing publication." >&2
  exit 3
fi
if [[ -n "$(git -C "$ROOT" status --porcelain --untracked-files=all -- ui-shell brand docs/TSUNAMI-UI-GENESIS-RESEARCH.md docs/TSUNAMI-UI-GENESIS-COVERAGE.md tools/ui_shell_gate.py tools/ui_shell_static_check.py tools/ui_shell_codespace_build.py)" ]]; then
  echo "ERROR: UI Genesis source changed during build; refusing publication." >&2
  exit 3
fi
if [[ "$BUILD_BACKEND" == "github-codespaces" ]]; then
  test -s "$CODESPACE_MANIFEST" || {
    echo "ERROR: Codespace build manifest missing: $CODESPACE_MANIFEST" >&2
    exit 3
  }
  python3 - "$CODESPACE_MANIFEST" "$SOURCE_HEAD" "$BUILT" <<'PY'
import hashlib, json, pathlib, sys
manifest_path=pathlib.Path(sys.argv[1])
expected_head=sys.argv[2]
apk_path=pathlib.Path(sys.argv[3])
payload=json.loads(manifest_path.read_text(encoding="utf-8"))
assert payload.get("status")=="BUILT", payload
assert payload.get("commit")==expected_head, (payload.get("commit"), expected_head)
assert payload.get("source_dirty") is False, payload
assert payload.get("hash_match") is True, payload
actual=hashlib.sha256(apk_path.read_bytes()).hexdigest()
assert payload.get("sha256")==actual, (payload.get("sha256"), actual)
print("CODESPACE_MANIFEST_BINDING=PASS")
PY
fi

python3 - "$BUILT" <<'PY'
import sys, zipfile
p=sys.argv[1]
with zipfile.ZipFile(p) as z:
    names=set(z.namelist())
    assert "AndroidManifest.xml" in names, "APK missing AndroidManifest.xml"
    assert "classes.dex" in names, "APK missing classes.dex"
    dex=[n for n in names if n.startswith("classes") and n.endswith(".dex")]
    assert dex, "APK contains no DEX payload"
print("APK_ZIP_STRUCTURE=PASS")
PY

mkdir -p "$(dirname "$TARGET")"
tmp="$TARGET.tmp.$$"
cp "$BUILT" "$tmp"
chmod 0644 "$tmp"
mv -f "$tmp" "$TARGET"

hash_file() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else sha256sum "$1" | awk '{print $1}'
  fi
}
bytes_file() {
  if stat -f%z "$1" >/dev/null 2>&1; then stat -f%z "$1"
  else stat -c%s "$1"
  fi
}

SHA="$(hash_file "$TARGET")"
BYTES="$(bytes_file "$TARGET")"
SOURCE_BRANCH="$(git -C "$ROOT" branch --show-current)"
BUILT_SHA="$(hash_file "$BUILT")"
[[ "$SHA" == "$BUILT_SHA" ]] || {
  echo "ERROR: portal APK hash diverged from built APK" >&2
  exit 4
}

python3 - "$MANIFEST" "$TARGET" "$BYTES" "$SHA" "$SOURCE_HEAD" "$SOURCE_BRANCH" "$BUILD_BACKEND" <<'PY'
import json, pathlib, sys, datetime
manifest,target,bytes_,sha,head,branch,backend=sys.argv[1:]
payload={
    "artifact":"TSUNAMI UI Genesis",
    "package":"com.tsunami.shell",
    "portal_path":target,
    "bytes":int(bytes_),
    "sha256":sha,
    "source_head":head,
    "source_branch":branch,
    "build_backend":backend,
    "published_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "backend_free":True,
}
pathlib.Path(manifest).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(payload,sort_keys=True))
PY

printf 'PORTAL_APK=%s\nPORTAL_APK_BYTES=%s\nPORTAL_APK_SHA256=%s\nPORTAL_APK_SOURCE_HEAD=%s\nPORTAL_APK_BUILD_BACKEND=%s\nPORTAL_APK_MANIFEST=%s\n' \
  "$TARGET" "$BYTES" "$SHA" "$SOURCE_HEAD" "$BUILD_BACKEND" "$MANIFEST"
