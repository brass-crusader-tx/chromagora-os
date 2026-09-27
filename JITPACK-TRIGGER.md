# TSUNAMI UI Genesis JitPack trigger

Private Genesis source head: `b4a5468567332145d338049a6885ecf7356f8a21`.

This commit is an immutable build-transport trigger for the byte-identical public mirror. The mirrored build-critical source is bound by `tsunami-builder/MIRROR-MANIFEST.json`; JitPack is expected to build `tsunami-builder/ui-shell` through the repository `jitpack.yml`.

Rebuild request: sequence 31 · 2026-09-27T01:10:00Z.

This rebuild advances the exact-source mirror by the single build-critical delta after the prior manifest-bound head: the UI model now includes the INFO listening mode and explicit lyrics tool panels. All other manifest-listed UI Genesis build/support files remain byte-identical to the prior verified mirror contract.

After this file is committed, use the resulting commit SHA (or its canonical 10-character prefix) as the JitPack version:

- APK: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/chromagora-os-<VERSION>.apk`
- AndroidTest APK: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/chromagora-os-<VERSION>-androidTest.apk`
- Build log: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/build.log`
