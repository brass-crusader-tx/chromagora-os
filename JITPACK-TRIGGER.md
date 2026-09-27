# TSUNAMI UI Genesis JitPack trigger

Private Genesis source head: `830e3b38f1c010a9077998b022f9cae62cb5345e`.

This commit is an immutable build-transport trigger for the byte-identical public mirror. The mirrored build-critical source is bound by `tsunami-builder/MIRROR-MANIFEST.json`; JitPack is expected to build `tsunami-builder/ui-shell` through the repository `jitpack.yml`.

Rebuild request: sequence 26 · 2026-09-26T23:43:00Z.

This rebuild includes the exact-source TSUNAMI Sans v5.1 f/r/t legibility refinement, with regenerated deterministic TTF/proof hashes bound in the mirrored font manifest.

After this file is committed, use the resulting commit SHA (or its canonical 10-character prefix) as the JitPack version:

- APK: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/chromagora-os-<VERSION>.apk`
- AndroidTest APK: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/chromagora-os-<VERSION>-androidTest.apk`
- Build log: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/build.log`
