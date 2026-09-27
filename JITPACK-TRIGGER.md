# TSUNAMI UI Genesis JitPack trigger

Private Genesis source head: `43ace196781cd22b564466e64b5ade2d87304aed`.

Exact byte-identical public build snapshot: `0d72dca7a65122a8c0738104df6417e0957a197c`.

A fresh connector-side audit compared all **58/58** rows in `tsunami-builder/MIRROR-MANIFEST.json` against both the private Genesis tree at `43ace196781cd22b564466e64b5ade2d87304aed` and the nested public mirror at `0d72dca7a65122a8c0738104df6417e0957a197c`: **0 Git blob SHA mismatches** and **0 byte-size mismatches**. The manifest's `source_head` equals the private head exactly.

JitPack executes the nested `tsunami-builder/` tree at this immutable public commit, so this is the current non-GitHub-Actions construction target.

- [Trigger POM](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/0d72dca7a6/chromagora-os-0d72dca7a6.pom)
- [Build API](https://jitpack.io/api/builds/com.github.brass-crusader-tx/chromagora-os/0d72dca7a6)
- [App APK](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/0d72dca7a6/chromagora-os-0d72dca7a6.apk)
- [AndroidTest APK](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/0d72dca7a6/chromagora-os-0d72dca7a6-androidTest.apk)
- [Build log](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/0d72dca7a6/build.log)

The target is immutable and source-bound to private Genesis head `43ace196781cd22b564466e64b5ade2d87304aed`. A later documentation-only branch commit may move the mirror branch pointer; acceptance still binds the produced APK pair to this immutable commit and to the manifest's private source head.
