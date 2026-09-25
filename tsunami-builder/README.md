# TSUNAMI UI Genesis — public build mirror

This directory is an isolated build mirror of the backend-free TSUNAMI UI Genesis shell from `brass-crusader-tx/TSUNAMI`.

The canonical source binding is recorded in `MIRROR-MANIFEST.json`. Every `ui-shell/` file in that manifest is compared by Git blob SHA; a mismatch means this mirror must not be treated as current.

## Build

From this `tsunami-builder/` directory on a host with Android SDK access:

```bash
bash ui-shell/tools/build_host.sh
```

The canonical build produces:

- `dist/TSUNAMI-UI-Genesis-debug.apk`
- `dist/TSUNAMI-UI-Genesis-debug-androidTest.apk`
- `dist/TSUNAMI-Sans-v4.7/`
- `build/reports/tsunami/ui-shell/host/build.txt`

For a connected Android device:

```bash
bash ui-shell/tools/build_host.sh --verify-device <adb-serial>
```

That path installs the shell and AndroidTest APKs, runs Compose instrumentation, captures the 36-state visual matrix, derives monochrome and squint proofs, runs visual-sanity checks, and scans the device log for shell crashes.

The GitHub-hosted workflow is intentionally `workflow_dispatch`-only while the account/platform runner allocator is failing before steps. A failed hosted run with no step list is not an Android compilation result.

Do not substitute a production TSUNAMI APK for this shell. The shell package is `com.tsunami.shell` and intentionally declares no network/media-storage permissions.
