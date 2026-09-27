# TSUNAMI UI Genesis JitPack trigger

Private Genesis source head: `58b4cfe22cdeb5de99157f6032fc61b4992c7d3c`.

Exact byte-identical public build snapshot: `87fee85018a915e15618131beb79add40cdb5119`.

A fresh connector-side audit compared all **58/58** rows in `tsunami-builder/MIRROR-MANIFEST.json` against both the private Genesis tree at `58b4cfe22cdeb5de99157f6032fc61b4992c7d3c` and the nested public mirror at `87fee85018a915e15618131beb79add40cdb5119`: **0 Git blob SHA mismatches** and **0 byte-size mismatches**. The manifest's `source_head` equals the private head exactly.

The private head deliberately restores the manifest-bound TSUNAMI Sans v5.1 generator after an unmanifested v5.2 experiment changed font geometry without regenerating the canonical TTF/proof hash contract. This keeps the build lane reproducible instead of accepting unverified type output.

JitPack executes the nested `tsunami-builder/` tree at this immutable public commit, so this is the current non-GitHub-Actions construction target.

- [Trigger POM](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/87fee85018/chromagora-os-87fee85018.pom)
- [Build API](https://jitpack.io/api/builds/com.github.brass-crusader-tx/chromagora-os/87fee85018)
- [App APK](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/87fee85018/chromagora-os-87fee85018.apk)
- [AndroidTest APK](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/87fee85018/chromagora-os-87fee85018-androidTest.apk)
- [Build log](https://jitpack.io/com/github/brass-crusader-tx/chromagora-os/87fee85018/build.log)

The target is immutable and source-bound to private Genesis head `58b4cfe22cdeb5de99157f6032fc61b4992c7d3c`. A later documentation-only branch commit may move the mirror branch pointer; acceptance still binds any APK pair to this immutable commit and to the manifest's private source head.
