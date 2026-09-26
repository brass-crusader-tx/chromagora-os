# TSUNAMI UI Genesis — public build mirror

This directory is a byte-bound isolated build mirror of the backend-free TSUNAMI UI Genesis shell from `brass-crusader-tx/TSUNAMI`.

`MIRROR-MANIFEST.json` is the authority for the private source head and every mirrored build-critical Git blob. The public builder refuses to compile when any listed file diverges from that manifest.

## Build

From `tsunami-builder/` on a host with Android SDK access:

```bash
bash ui-shell/tools/build_host.sh
```

The canonical host build produces the shell APK, AndroidTest APK, TSUNAMI Sans v4.8 proof/font bundle, and hash-bound build evidence under `dist/` and `build/reports/tsunami/ui-shell/host/`.

For a connected Android device:

```bash
bash ui-shell/tools/build_host.sh --verify-device <adb-serial>
```

That path installs the shell and test APKs, runs Compose instrumentation, captures the canonical 45-state visual matrix, derives monochrome and squint evidence, runs image-level sanity checks, and scans logcat for TSUNAMI shell crashes.

The shell package is `com.tsunami.shell`. It is intentionally backend-free and declares no network/media-storage permissions. Never substitute a production TSUNAMI APK for this experiential shell.

GitHub-hosted or self-hosted workflow startup failure before checkout is infrastructure evidence only; it is not an Android compilation result.
