#!/usr/bin/env bash
set -euo pipefail

# Reproducible host entry point for the isolated TSUNAMI UI Genesis shell.
# It deliberately never enters the production app Gradle graph.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_ROOT="$(cd "$HERE/.." && pwd)"
REPO_ROOT="$(cd "$UI_ROOT/.." && pwd)"
DIST="$REPO_ROOT/dist"
REPORT="$REPO_ROOT/build/reports/tsunami/ui-shell/host"
mkdir -p "$DIST" "$REPORT"

# Prefer a local JDK 17 on macOS when available, while accepting any runtime >= 17.
if [[ "$(uname -s)" == "Darwin" && -x /usr/libexec/java_home ]]; then
  if JAVA17_HOME="$(/usr/libexec/java_home -v 17 2>/dev/null)"; then
    export JAVA_HOME="$JAVA17_HOME"
    export PATH="$JAVA_HOME/bin:$PATH"
  fi
fi
JAVA_MAJOR="$(java -version 2>&1 | awk -F'[".]' '/version/{print $2;exit}')"
if [[ -z "$JAVA_MAJOR" || "$JAVA_MAJOR" -lt 17 ]]; then
  echo "ERROR: UI Genesis requires JDK 17 or newer; got: $(java -version 2>&1 | head -1)" >&2
  exit 2
fi
if [[ -z "${ANDROID_SDK_ROOT:-}" ]]; then
  if [[ -d "$HOME/Library/Android/sdk" ]]; then
    export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
  elif [[ -d "$HOME/Android/Sdk" ]]; then
    export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
  fi
fi
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"

if [[ -z "${ANDROID_SDK_ROOT:-}" || ! -d "$ANDROID_SDK_ROOT" ]]; then
  echo "ERROR: Android SDK not found; set ANDROID_SDK_ROOT." >&2
  exit 2
fi
printf 'sdk.dir=%s\n' "$ANDROID_SDK_ROOT" > "$UI_ROOT/local.properties"

# Match the production Android project compile SDK. Provision API 36 on hosts
# that have an Android SDK but have not yet installed the required platform.
SDKMANAGER=""
if [[ -x "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" ]]; then
  SDKMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
elif command -v sdkmanager >/dev/null 2>&1; then
  SDKMANAGER="$(command -v sdkmanager)"
fi
if [[ ! -d "$ANDROID_SDK_ROOT/platforms/android-36" || ! -d "$ANDROID_SDK_ROOT/build-tools/36.0.0" ]]; then
  if [[ -z "$SDKMANAGER" ]]; then
    echo "ERROR: Android platform/build-tools 36 are incomplete and sdkmanager is unavailable." >&2
    exit 2
  fi
  echo "Provisioning Android platform 36 and build-tools 36.0.0"
  yes | "$SDKMANAGER" --licenses >/dev/null 2>&1 || true
  "$SDKMANAGER" "platform-tools" "platforms;android-36" "build-tools;36.0.0"
fi

GRADLE_VERSION="9.4.1"
if [[ -n "${GRADLE_BIN:-}" ]]; then
  if [[ ! -x "$GRADLE_BIN" ]]; then
    echo "ERROR: GRADLE_BIN is not executable: $GRADLE_BIN" >&2
    exit 2
  fi
else
  GRADLE_BIN="$(bash "$HERE/bootstrap_gradle.sh" --print-gradle)"
fi
if ! "$GRADLE_BIN" --version 2>/dev/null | grep -q "Gradle $GRADLE_VERSION"; then
  echo "ERROR: UI Genesis requires Gradle $GRADLE_VERSION; got $("$GRADLE_BIN" --version 2>/dev/null | awk '/^Gradle /{print $2;exit}')" >&2
  exit 2
fi
CACHE_ROOT="$REPO_ROOT/build/.ui-shell-toolchain"
mkdir -p "$CACHE_ROOT"

PYTHON_HOST="${PYTHON_BIN:-python3}"
VENV="$CACHE_ROOT/venv"
if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON_HOST" -m venv "$VENV"
fi
PYTHON_BIN="$VENV/bin/python"
export TSUNAMI_FONT_PYTHON="$PYTHON_BIN"
"$PYTHON_BIN" -m pip install --disable-pip-version-check --quiet   "fonttools==4.63.0" "shapely==2.1.2" "pillow==12.3.0"

"$PYTHON_BIN" - <<'PY'
import fontTools, shapely, PIL
print("FONT_BUILD_DEPS=PASS")
PY

cd "$UI_ROOT"
"$PYTHON_BIN" tools/source_verify.py
"$PYTHON_BIN" tools/accessibility_verify.py
if command -v kotlinc >/dev/null 2>&1; then
  bash tools/jvm_state_gate.sh "$UI_ROOT" | tee "$REPORT/jvm-state-gate.txt"
else
  echo "JVM_STATE_GATE=SKIP kotlinc unavailable" | tee "$REPORT/jvm-state-gate.txt"
fi
"$PYTHON_BIN" tools/prepare_fonts.py

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from fontTools.ttLib import TTFont
fonts=sorted(Path('app/src/main/res/font').glob('tsunami_sans_*.ttf'))
assert len(fonts)==5, f"expected 5 TSUNAMI Sans masters, got {len(fonts)}"
weights=set()
for p in fonts:
    f=TTFont(p)
    try:
        family=next(n.toUnicode() for n in f['name'].names if n.nameID==1)
        version=next(n.toUnicode() for n in f['name'].names if n.nameID==5)
        assert family=='TSUNAMI Sans', (p,family)
        assert version=='Version 4.800', (p,version)
        weights.add(int(f['OS/2'].usWeightClass))
        assert 'GPOS' in f, f"{p}: missing GPOS"
    finally:
        f.close()
assert weights=={300,400,500,600,700}, weights
import hashlib
expected={
    "tsunami_sans_light.ttf":"c295d45e732cf9d3c431c14465b4e64d0a164f6605da68a74ad207a59abe00fb",
    "tsunami_sans_regular.ttf":"fb5803e5ed05442325bec033772bb5434b1f62740e02329d8d8c599e7d051c8b",
    "tsunami_sans_medium.ttf":"0576bd38e1f0a34b40c22510249625abe27eda3cde39487a98d78102c5628c67",
    "tsunami_sans_semibold.ttf":"6a196f5a93fbdbc4ccf821e12d9bb93963bb5d6263add32a90383ceb43acd914",
    "tsunami_sans_bold.ttf":"063a6c7f56c48a78a45016cdf5b10e96a8fbf26b0ee5c30608f4a6c57af77841",
}
actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fonts}
assert actual==expected, (actual, expected)
print("FONT_GENERATION=PASS")
print("FONT_CANONICAL_HASHES=PASS")
PY

FONT_DIST="$DIST/TSUNAMI-Sans-v4.8"
rm -rf "$FONT_DIST"
mkdir -p "$FONT_DIST"
cp app/src/main/res/font/tsunami_sans_*.ttf "$FONT_DIST/"
cp tools/proofs/tsunami-sans-proof.png tools/proofs/tsunami-sans-ui-proof.png "$FONT_DIST/"
cp "$REPO_ROOT/brand/tsunami-mark.svg" "$REPO_ROOT/brand/tsunami-mark-inverse.svg" "$FONT_DIST/"
{
  echo "TSUNAMI Sans v4.8"
  echo "Generated from ui-shell/tools/generate_tsunami_sans.py"
  echo "Family: TSUNAMI Sans"
  echo "Weights: 300 400 500 600 700"
} > "$FONT_DIST/README.txt"

"$GRADLE_BIN" --no-daemon --stacktrace --console=plain \
  :app:assembleDebug \
  :app:assembleDebugAndroidTest

APK="$UI_ROOT/app/build/outputs/apk/debug/app-debug.apk"
TEST_APK="$UI_ROOT/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
test -s "$APK"
test -s "$TEST_APK"

OUT_APK="$DIST/TSUNAMI-UI-Genesis-debug.apk"
OUT_TEST="$DIST/TSUNAMI-UI-Genesis-debug-androidTest.apk"
cp "$APK" "$OUT_APK"
cp "$TEST_APK" "$OUT_TEST"

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

APK_SHA="$(hash_file "$OUT_APK")"
TEST_SHA="$(hash_file "$OUT_TEST")"
{
  echo "SOURCE_SHA=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "GRADLE=$("$GRADLE_BIN" --version | awk '/^Gradle /{print $2;exit}')"
  echo "JAVA=$(java -version 2>&1 | head -1)"
  echo "JAVA_HOME=${JAVA_HOME:-}"
  echo "APK=$OUT_APK"
  echo "APK_BYTES=$(bytes_file "$OUT_APK")"
  echo "APK_SHA256=$APK_SHA"
  echo "TEST_APK=$OUT_TEST"
  echo "TEST_APK_BYTES=$(bytes_file "$OUT_TEST")"
  echo "TEST_APK_SHA256=$TEST_SHA"
  echo "HOST_BUILD=PASS"
} | tee "$REPORT/build.txt"

MODE="${1:-}"
if [[ "$MODE" == "--install" || "$MODE" == "--verify-device" ]]; then
  SERIAL="${2:-${ANDROID_SERIAL:-}}"
  ADB="${ADB_BIN:-}"
  if [[ -z "$ADB" ]]; then
    if command -v adb >/dev/null 2>&1; then ADB="$(command -v adb)"
    elif [[ -x "$ANDROID_SDK_ROOT/platform-tools/adb" ]]; then ADB="$ANDROID_SDK_ROOT/platform-tools/adb"
    fi
  fi
  if [[ -z "$ADB" || ! -x "$ADB" ]]; then
    echo "ERROR: adb not found." >&2; exit 2
  fi
  if [[ -z "$SERIAL" ]]; then
    SERIAL="$("$ADB" devices | awk 'NR>1 && $2=="device"{print $1;exit}')"
  fi
  if [[ -z "$SERIAL" ]]; then
    echo "ERROR: no authorized Android device." >&2; exit 2
  fi

  "$ADB" -s "$SERIAL" install -r "$OUT_APK"
  "$ADB" -s "$SERIAL" shell am force-stop com.tsunami.shell
  "$ADB" -s "$SERIAL" shell am start -W -n com.tsunami.shell/.MainActivity
  "$ADB" -s "$SERIAL" shell dumpsys package com.tsunami.shell | grep -E 'versionCode|versionName' | head -4 | tee "$REPORT/device-package.txt"
  echo "DEVICE_INSTALL=PASS serial=$SERIAL" | tee -a "$REPORT/build.txt"

  if [[ "$MODE" == "--verify-device" ]]; then
    "$ADB" -s "$SERIAL" install -r "$OUT_TEST"
    "$ADB" -s "$SERIAL" logcat -c || true
    "$ADB" -s "$SERIAL" shell am instrument -w       com.tsunami.shell.test/androidx.test.runner.AndroidJUnitRunner       | tee "$REPORT/instrumentation.txt"
    grep -q 'OK (' "$REPORT/instrumentation.txt" || {
      echo "ERROR: instrumentation did not report success." >&2
      exit 3
    }

    export ANDROID_SERIAL="$SERIAL"
    export PATH="$(dirname "$ADB"):$PATH"
    cd "$UI_ROOT"
    bash tools/capture_verify.sh
    "$PYTHON_BIN" tools/derive_review_images.py
    "$PYTHON_BIN" tools/visual_sanity_verify.py | tee "$REPORT/visual-sanity.txt"

    rm -rf "$REPORT/visual" "$REPORT/font-proofs"
    cp -R build/verification "$REPORT/visual"
    cp -R tools/proofs "$REPORT/font-proofs"
    cp "$REPO_ROOT/docs/TSUNAMI-UI-GENESIS-VISUAL-REVIEW.md" "$REPORT/TSUNAMI-UI-GENESIS-VISUAL-REVIEW.md"
    test "$(find "$REPORT/visual" -maxdepth 1 -name '[0-9][0-9]-*.png' ! -name '*-mono.png' ! -name '*-squint.png' | wc -l | tr -d ' ')" = "45"
    test -s "$REPORT/visual/contact-sheet.png"
    if grep -q 'FATAL EXCEPTION' "$REPORT/visual/logcat-tail.txt" && grep -q 'Process: com.tsunami.shell' "$REPORT/visual/logcat-tail.txt"; then
      echo "ERROR: shell crash signature found in device logcat." >&2
      exit 4
    fi
    {
      echo "VISUAL_CAPTURE=PASS states=45"
      echo "VISUAL_SANITY=PASS"
      echo "MONOCHROME_REVIEW_DERIVATION=PASS"
      echo "SQUINT_REVIEW_DERIVATION=PASS"
      echo "CRASH_SCAN=PASS"
      echo "DEVICE_VERIFY=PASS serial=$SERIAL"
    } | tee -a "$REPORT/build.txt"
  fi
fi
