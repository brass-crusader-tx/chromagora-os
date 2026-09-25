#!/usr/bin/env bash
set -euo pipefail
PKG=com.tsunami.shell
ACT=.MainActivity
OUT=build/verification
rm -rf "$OUT"
mkdir -p "$OUT"
APK="${TSUNAMI_UI_SHELL_APK:-app/build/outputs/apk/debug/app-debug.apk}"
restore_device() {
  adb shell settings put system font_scale 1.0 >/dev/null 2>&1 || true
  adb shell settings put system user_rotation 0 >/dev/null 2>&1 || true
  adb shell settings put system accelerometer_rotation 1 >/dev/null 2>&1 || true
  adb shell wm size reset >/dev/null 2>&1 || true
  adb shell wm density reset >/dev/null 2>&1 || true
}
trap restore_device EXIT
test -s "$APK" || { echo "APK missing: $APK" >&2; exit 2; }
adb install -r "$APK" >/dev/null
adb logcat -c || true
capture() {
  local name="$1" screen="$2" scenario="$3" theme="$4" mode="${5:-}" page="${6:-}"
  adb shell am force-stop "$PKG"
  if [[ -n "$mode" || -n "$page" ]]; then
    adb shell am start -W -n "$PKG/$ACT" --es screen "$screen" --es scenario "$scenario" --es theme "$theme" --es mode "$mode" --es page "$page" >/dev/null
  else
    adb shell am start -W -n "$PKG/$ACT" --es screen "$screen" --es scenario "$scenario" --es theme "$theme" >/dev/null
  fi
  sleep 1
  adb exec-out screencap -p > "$OUT/$name.png"
}
capture 01-listen-light listen default light
capture 02-library-no-artwork library no-artwork light
capture 03-find-light find default light
capture 04-signal-error signal error light
capture 05-player-missing-lyrics player missing-lyrics light lyrics
capture 06-player-longform player longform light queue
capture 36-player-podcast player podcast light queue
capture 07-settings-dark settings default dark
capture 08-onboarding-light listen onboarding light
capture 09-player-dark-queue player default dark queue
capture 10-player-lyrics player default light lyrics
capture 11-player-output player default light output
capture 12-player-visual player default light visual
capture 13-listen-empty listen empty light
capture 14-listen-loading listen loading light
capture 15-library-40 library small-list light
capture 16-library-4k library long-list light
capture 17-library-40k library huge-list light
capture 27-listen-buffering listen buffering light
capture 28-library-unavailable library unavailable light
capture 29-find-partial find partial light
capture 30-settings-audio settings default light "" audio
capture 31-settings-controls settings default light "" controls
capture 37-settings-external-controls settings default light "" external-controls
capture 38-find-empty find search-empty light
capture 39-find-error find search-error light
capture 40-player-queue-empty player queue-empty light queue
capture 41-settings-provider-connecting settings provider-connecting light "" services
capture 42-settings-provider-error settings provider-error light "" services
capture 43-settings-downloads-active settings downloads-active light
capture 44-settings-downloads-error settings downloads-error light
capture 45-library-index library library-index light
capture 32-settings-backup settings default dark "" backup
capture 35-settings-services settings default light "" services
capture 33-listen-no-artwork listen no-artwork light
capture 34-player-no-artwork player no-artwork dark queue

adb shell settings put system font_scale 1.50
capture 18-library-font-150 library long-title light
adb shell settings put system font_scale 2.00
capture 19-library-font-200 library long-title light
adb shell settings put system font_scale 1.0
capture 20-listen-accessibility listen accessibility light

adb shell settings put system accelerometer_rotation 0
adb shell settings put system user_rotation 1
sleep 1
capture 21-library-landscape library long-list light
adb shell settings put system user_rotation 0
adb shell settings put system accelerometer_rotation 1

adb shell wm size 1200x900
adb shell wm density 240
sleep 2
capture 22-library-medium library long-list light
capture 23-player-medium player default dark queue

adb shell wm size 1600x1200
adb shell wm density 240
sleep 2
capture 24-listen-expanded listen default light
capture 25-library-expanded library huge-list light
capture 26-player-expanded player default dark lyrics

adb shell wm size reset
adb shell wm density reset
sleep 2
adb logcat -d -t 1200 > "$OUT/logcat-tail.txt" || true
for f in "$OUT"/*.png; do test "$(wc -c < "$f")" -gt 10000 || { echo "capture too small: $f"; exit 1; }; done
BASE_COUNT="$(find "$OUT" -maxdepth 1 -name '[0-9][0-9]-*.png' ! -name '*-mono.png' ! -name '*-squint.png' | wc -l | tr -d ' ')"
[[ "$BASE_COUNT" == "45" ]] || { echo "expected exactly 45 base captures, found $BASE_COUNT" >&2; exit 1; }
printf 'captures=%s\n' "$BASE_COUNT" | tee "$OUT/capture-summary.txt"
