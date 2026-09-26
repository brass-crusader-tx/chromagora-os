# TSUNAMI UI Genesis shell

A backend-free Android experiential prototype for the TSUNAMI product genesis. This project is deliberately standalone: it is **not** included as a module in the production TSUNAMI Gradle graph and declares no network, storage, microphone, media-library or production-service permissions.

## Architecture

- `model/` deterministic mock media/service objects
- `state/` mutable prototype state and interaction transitions
- `theme/` TSUNAMI Sans typography, spacing and functional color roles
- `brand/` vector mark implementation
- `components/` reusable authored primitives; no stock Material component surface defines the visual language
- `navigation/` responsive Index + Listening Spine architecture
- `screens/` listening, library, find, signal, settings and expanded listening environments
- `tools/generate_tsunami_sans.py` procedural TSUNAMI Sans v4.8 source/generator: five weight-specific geometric masters with explicit screen-legibility control glyphs
- `tools/source_verify.py` static architecture/back-end isolation/interaction contract
- `tools/accessibility_verify.py` WCAG text-contrast and 48/56dp authored-control target gate
- `tools/build_host.sh` reproducible host build entry point; optionally installs the isolated package
- `tools/capture_verify.sh` emulator screenshot/state verification harness
- `tools/visual_sanity_verify.py` non-blank/distinct/orientation/derivative sanity gate for the capture matrix

## Build

The shell uses the AGP 9 built-in Kotlin model rather than the now-incompatible `org.jetbrains.kotlin.android` plugin: AGP 9.2.1, its documented built-in Kotlin/KGP 2.2.10 line, Compose compiler plugin 2.2.10, compileSdk/targetSdk 36, Compose UI/Foundation/Animation 1.11.4, and JDK/JVM 17. Gradle 9.4.1 is resolved through the checksum-pinned bootstrap. This pairing follows the Android 9.2 compatibility table and built-in Kotlin migration guidance rather than maintaining a second, conflicting Kotlin plugin.

From the isolated project:

```bash
python3 -m pip install 'fonttools==4.63.0' 'shapely==2.1.2' 'pillow==12.3.0'
bash tools/build_host.sh
```

The host entry point runs the static source contract, regenerates and validates all five TSUNAMI Sans masters, assembles both the debug APK and instrumentation APK, records hashes, and copies the results to the repository `dist/` directory. On a development machine with an authorized device:

```bash
bash tools/build_host.sh --install <adb-serial>
```

This installs only `com.tsunami.shell`; the production application is outside this Gradle graph.

## Deterministic launch scenarios

`MainActivity` accepts ADB extras for visual QA:

- `--es screen listen|library|find|signal|settings|player`
- `--es scenario default|onboarding|empty|loading|error|partial|buffering|unavailable|missing-art|missing-lyrics|long-title|longform|podcast|small-list|long-list|huge-list|no-artwork|accessibility|search-empty|search-error|queue-empty|provider-connecting|provider-error|downloads-active|downloads-error`
- `--es theme light|dark`
- `--es mode queue|lyrics|output|visual` when `screen=player`
- `--es page audio|controls|backup|lyrics|presentation|…` when `screen=settings` for deterministic depth captures

These extras exist solely for the prototype and never touch production state.

## Chromagora preview publication

`tools/publish_chromagora_apk.sh` is the preview-publication entry point. It refuses to republish a stale binary: source and accessibility gates run first, then the script attempts the canonical host build and falls back to the persistent **TSUNAMI Builder** Codespace when the host Android toolchain is unavailable. The copied portal APK is hash-compared to the freshly built artifact and published atomically with a JSON sidecar containing the source HEAD, SHA-256, byte size, package id, backend-free flag and build backend. Codespace publication additionally requires a clean-source `codespace-build.json` bound to the exact current HEAD and APK hash.

Set `TSUNAMI_FORCE_CODESPACE_BUILD=1` to skip the host attempt. Override the destination with `TSUNAMI_PORTAL_APK_TARGET=/absolute/path.apk`.

## Verification contract

The canonical repository gate is `python3 tools/ui_shell_gate.py` from the repository root. It generates and validates all five TSUNAMI Sans weights, checks required UI glyph coverage and weight metadata, builds the isolated APK, rejects production-facing network/media permissions, runs Compose interaction tests on an Android emulator, captures forty-five deterministic visual states, including 40 / 4,008 / 40,008-item library fixtures, compact landscape, 150%/200% font scaling, a high-contrast/56dp control accessibility state, explicit medium-width rail topology, expanded three-pane layouts, no-artwork listening/player states, progressive settings depths, empty/failed search, empty queue, provider connecting/error, and active/failed download states, derives monochrome and blurred “squint” review variants, runs image-level sanity checks, scans the shell log for fatal crashes, and packages the APK, proofs, screenshots and mandatory human visual-review protocol under `build/reports/tsunami/ui-shell/`.

The shell intentionally remains backend-free. Queue, downloads, provider imports, playback routing, diagnostics, longform progress and all other consequential states are deterministic prototype state rather than adapters to production services.


## Current verification boundary

Static source/state/type/brand verification is present in-repo, but final acceptance still requires an Android-capable host to assemble the current head, install `com.tsunami.shell`, run the 38 Compose instrumentation tests, execute the 45-state capture matrix, inspect logcat, and complete the human visual-review protocol. GitHub Actions for this repository are currently terminating at `startup_failure` before jobs are created, so a workflow startup failure is not treated as either build success or build failure.


## Codespace fallback when GitHub-hosted Actions cannot start

The shell has a dedicated fallback builder that uses the repository's authenticated **TSUNAMI Builder** Codespace without joining the production Android Gradle graph:

```bash
python3 tools/ui_shell_codespace_build.py
```

That command runs the fast structural contract, snapshots only UI-Genesis source/documents, binds the transferred snapshot to a SHA-256 checked again inside the Codespace, generates TSUNAMI Sans in the remote throwaway workspace, reruns the source/accessibility contracts remotely, builds both `:app:assembleDebug` and `:app:assembleDebugAndroidTest` from `ui-shell/`, copies both APKs back to the canonical repository `dist/`, and requires each copied APK SHA-256 to match the corresponding hash emitted inside the Codespace. `codespace-build.json` also records whether the selected local source paths were dirty, so a built artifact is never silently attributed to a clean commit when the snapshot contained working-tree edits.

With an explicitly chosen connected Android device, installation plus the Compose instrumentation suite can be requested directly; the full deterministic screenshot matrix implies instrumentation and can be chained into the same evidence run:

```bash
python3 tools/ui_shell_codespace_build.py --serial <adb-serial> --instrument
python3 tools/ui_shell_codespace_build.py --serial <adb-serial> --capture-matrix

# When exactly one physical Android device is attached:
python3 tools/ui_shell_codespace_build.py --auto-device --capture-matrix
```

The device-review path restores font scale, rotation, logical display size and density even if a capture fails. A full `--capture-matrix` run also derives the monochrome and squint variants, executes the image-level visual-sanity verifier, emits a contact sheet, persists the instrumentation transcript, and packages the device evidence as `dist/TSUNAMI-UI-Genesis-device-review.zip` with its SHA-256 recorded in `codespace-build.json`. This is a development fallback only; it does not alter production TSUNAMI, `CURRENT-VERIFIED.json`, or the Chromagora graduation path.
