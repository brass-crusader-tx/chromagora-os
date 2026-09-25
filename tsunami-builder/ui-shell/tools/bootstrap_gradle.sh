#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_ROOT="${TSUNAMI_GRADLE_CACHE:-${HOME}/.cache/tsunami-ui-genesis}"
GRADLE_VERSION="9.4.1"
GRADLE_SHA256="2ab2958f2a1e51120c326cad6f385153bb11ee93b3c216c5fccebfdfbb7ec6cb"
ZIP="$CACHE_ROOT/gradle-$GRADLE_VERSION-bin.zip"
DIST="$CACHE_ROOT/gradle-$GRADLE_VERSION"
URL="https://services.gradle.org/distributions/gradle-$GRADLE_VERSION-bin.zip"

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    python3 - "$1" <<'PY'
import hashlib, pathlib, sys
p=pathlib.Path(sys.argv[1])
h=hashlib.sha256()
with p.open("rb") as f:
    for chunk in iter(lambda:f.read(1024*1024),b""):
        h.update(chunk)
print(h.hexdigest())
PY
  fi
}

fetch() {
  mkdir -p "$CACHE_ROOT"
  if [[ -f "$ZIP" ]] && [[ "$(sha256_file "$ZIP")" == "$GRADLE_SHA256" ]]; then
    return
  fi
  rm -f "$ZIP.tmp" "$ZIP"
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 4 --retry-delay 2 --connect-timeout 20       --output "$ZIP.tmp" "$URL"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=4 --timeout=20 --output-document="$ZIP.tmp" "$URL"
  else
    python3 - "$URL" "$ZIP.tmp" <<'PY'
import pathlib, sys, urllib.request
url,dst=sys.argv[1:3]
with urllib.request.urlopen(url,timeout=30) as r, pathlib.Path(dst).open("wb") as out:
    while True:
        chunk=r.read(1024*1024)
        if not chunk: break
        out.write(chunk)
PY
  fi
  actual="$(sha256_file "$ZIP.tmp")"
  if [[ "$actual" != "$GRADLE_SHA256" ]]; then
    echo "Gradle checksum mismatch: expected $GRADLE_SHA256, got $actual" >&2
    rm -f "$ZIP.tmp"
    exit 3
  fi
  mv "$ZIP.tmp" "$ZIP"
}

extract() {
  [[ -x "$DIST/bin/gradle" ]] && return
  rm -rf "$DIST" "$CACHE_ROOT/.extract-$GRADLE_VERSION"
  mkdir -p "$CACHE_ROOT/.extract-$GRADLE_VERSION"
  python3 - "$ZIP" "$CACHE_ROOT/.extract-$GRADLE_VERSION" <<'PY'
import pathlib, sys, zipfile
src=pathlib.Path(sys.argv[1]); dst=pathlib.Path(sys.argv[2])
with zipfile.ZipFile(src) as z:
    for item in z.infolist():
        target=(dst/item.filename).resolve()
        if dst.resolve() not in target.parents and target != dst.resolve():
            raise SystemExit(f"unsafe ZIP member: {item.filename}")
        z.extract(item,dst)
PY
  mv "$CACHE_ROOT/.extract-$GRADLE_VERSION/gradle-$GRADLE_VERSION" "$DIST"
  rm -rf "$CACHE_ROOT/.extract-$GRADLE_VERSION"
}

fetch
extract

export PATH="$DIST/bin:$PATH"
cd "$ROOT"
if [[ "${1:-}" == "--print-gradle" ]]; then
  printf '%s\n' "$DIST/bin/gradle"
  exit 0
fi

if [[ "$#" -eq 0 ]]; then
  set -- :app:assembleDebug --console=plain --stacktrace
fi

exec "$DIST/bin/gradle" "$@"
