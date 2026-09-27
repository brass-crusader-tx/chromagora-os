# TSUNAMI UI Genesis JitPack trigger

Private Genesis source head: `eaa96d5700329110f0d05fde79e28c5879b96997`.

This commit is an immutable build-transport trigger for the byte-identical public mirror. The mirrored build-critical source is bound by `tsunami-builder/MIRROR-MANIFEST.json`; JitPack is expected to build `tsunami-builder/ui-shell` through the repository `jitpack.yml`.

Rebuild request: sequence 30 · 2026-09-27T00:52:00Z.

This rebuild deliberately restores the manifest-bound TSUNAMI Sans v5.1 generator so the exact-source Android shell is byte-reproducible while the next type revision continues separately. The mirror contract was revalidated across all 58 build/support files with zero mismatches against the private Genesis head.

After this file is committed, use the resulting commit SHA (or its canonical 10-character prefix) as the JitPack version:

- APK: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/chromagora-os-<VERSION>.apk`
- AndroidTest APK: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/chromagora-os-<VERSION>-androidTest.apk`
- Build log: `https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/<VERSION>/build.log`
