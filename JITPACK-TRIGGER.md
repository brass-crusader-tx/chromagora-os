# TSUNAMI UI Genesis JitPack trigger

Private Genesis source head: `2fc88b9ce3ae50050ac9126eae176cc6e3a388e9`.

Exact byte-identical public build snapshot: `3d4989faeeb10a4074d8bd741bf112a5aa8d56da`.

A fresh connector-side audit compared all **58/58** rows in `tsunami-builder/MIRROR-MANIFEST.json` against both the private Genesis tree at `2fc88b9ce3ae50050ac9126eae176cc6e3a388e9` and the nested public mirror at `3d4989faeeb10a4074d8bd741bf112a5aa8d56da`: **0 Git blob SHA mismatches** and **0 byte-size mismatches**. The manifest's `source_head` equals the private head exactly.

JitPack executes the nested `tsunami-builder/` tree at this immutable public commit, so this is the current non-GitHub-Actions construction target.

- [Trigger POM](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/3d4989faee/chromagora-os-3d4989faee.pom)
- [Build API](https://jitpack.io/api/builds/com.github.brass-crusader-tx/chromagora-os/3d4989faee)
- [App APK](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/3d4989faee/chromagora-os-3d4989faee.apk)
- [AndroidTest APK](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/3d4989faee/chromagora-os-3d4989faee-androidTest.apk)
- [Build log](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/3d4989faee/build.log)

The target is immutable and source-bound to private Genesis head `2fc88b9ce3ae50050ac9126eae176cc6e3a388e9`. A later documentation-only branch commit may move the mirror branch pointer; acceptance still binds any APK pair to this immutable commit and to the manifest's private source head.
