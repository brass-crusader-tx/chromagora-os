# TSUNAMI UI Genesis — verification ledger

Current verification date: 2026-09-26

This ledger records concrete checks against the isolated `ui-shell` branch. It deliberately distinguishes evidence that has actually run from checks that still require an Android build environment.

## TSUNAMI Sans v4.5 — executed locally

The **current GitHub generator source** at `ui-shell/tools/generate_tsunami_sans.py` was reconstructed byte-for-byte in the local verification container and executed with fontTools 4.63.0, Shapely 2.1.2 and Pillow 12.3.0.

Fresh generation produced all five declared masters and both proof specimens. FontTools then reopened every TTF and verified:

- family name: `TSUNAMI Sans`
- version: `Version 4.500`
- OS/2 weight classes: 300, 400, 500, 600, 700
- 176 glyphs / 175 mapped characters per master
- complete required UI / Western-European character coverage
- GPOS kerning table present in every master
- no missing required UI glyphs

Fresh v4.5 SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| tsunami_sans_light.ttf | `7accf1a077d9692caa0c0cee66199d6e473294ed650e72ebed5f88432a61215b` |
| tsunami_sans_regular.ttf | `222d6d3b776b05c7be5f7bd6429f44d524a7b2e02091f540d708860d736f79da` |
| tsunami_sans_medium.ttf | `a571e7f708512d3b7c1c9fd1fbdd59a43306c30c377c3b3a49ef29aed32ab6d8` |
| tsunami_sans_semibold.ttf | `2a11482f1b26ee6013b93f362ea9612e7ec3258aca39328f6a76edb8e268cb4f` |
| tsunami_sans_bold.ttf | `220b830dad37b338ebdcb33d2df278878d950d655841553c66995ebdc21286fa` |
| tsunami-sans-proof.png | `868a874159173f21009ca250a0523c6f6f0c4c66678c883bc57a8aa51ca7aaf6` |
| tsunami-sans-ui-proof.png | `ebd5e5ef86119683b99bc01a86fa9905aff0de06576dcffff8a01e0421e9ca77` |

The current expanded v4.5 proofs were inspected at full resolution after generation. Relative to v4.4, the workhorse Regular/Medium masters are stronger at UI sizes, the lowercase `e` aperture is more open, and `t` is reduced to a cleaner geometric construction. The proof inventory includes body copy, all-caps UI labels, a deliberately long album title, song/artist hierarchy, timestamps/numerals, punctuation, accented text and a mixed-weight hierarchy. Android renderer inspection remains mandatory before final type acceptance; the desktop proof is evidence, not a substitute for device rendering.

## Mark reconstruction — rerun against supplied raster

The checked-in master SVG was rasterized at its 1000 × 820 viewBox and compared against the supplied logo reference after thresholding and normalizing both marks to their black-content bounding boxes.

Fresh measurement:

- supplied raster black-content bounds: 991 × 813 px;
- supplied arch component: 991 × 409 px;
- supplied body component: 576 × 572 px;
- vector raster black-content bounds: 1000 × 820 px;
- normalized binary intersection-over-union: **0.9834644255**.

This independently reproduces the ~0.983 fit recorded in the design rationale and confirms that the checked-in mark geometry, not a raster embed, is the production master.

## Kotlin source — static structural verification

All 15 Kotlin files in the isolated shell source tree were re-read from the current branch and checked for:

- balanced delimiter / string / comment structure
- imports required by Compose semantics, mutable float state, coroutine scrolling and drawing APIs
- no stale escaped interpolation fragments from prior edits

Current result: 15 / 15 source files passed the structural/import scan.

A newer full Kotlin/source-graph audit was executed at source head `ac6df9b2830d6487c3276014f251abb2e60a4c13` after the Android build stack and brand implementation were reconciled. It found:
- 15 Kotlin source/test files parsed with 0 lexical/delimiter failures;
- 306 `ShellState` members discovered and **0 unresolved `state.*` UI references**;
- 23 explicit `.clickable` interaction sites;
- 69 `TextCommand` call sites;
- 28 `HitIcon` call sites;
- 19 Compose instrumentation tests in the checked-in interaction suite;
- 0 forbidden production-source anchors (MediaStore/content resolver/network clients/Room/direct filesystem reads);
- 0 stock Material icon or Material Card identity anchors;
- 0 Android permissions declared by the isolated shell manifest.

A second build/manifest/brand pass over the same source found no contract discrepancy: AGP 9.2.1, built-in Kotlin/KGP 2.2.10, Compose compiler 2.2.10, Gradle 9.4.1, compileSdk/targetSdk 36, Compose 1.11.4 and JVM 17 all agree, while both the launcher vector and Compose renderer contain the canonical mark geometry. The evidence is recorded separately in `docs/TSUNAMI-UI-GENESIS-STATIC-AUDIT.md`.

The same audit verified the shell build contract at AGP 9.2.1 with AGP 9 built-in Kotlin (KGP 2.2.10), Compose compiler plugin 2.2.10, compileSdk/targetSdk 36, Compose UI/Foundation/Animation 1.11.4, UI test 1.11.4, and Kotlin/JVM 17. The separate `org.jetbrains.kotlin.android` plugin is intentionally absent.

The reconciliation also gave explicit progressive-disclosure homes to production-facing capabilities that were previously absent from the Genesis settings model: genre/playlist-path exclusions, vertical swipe mappings, album-artist policy, device-migration package preparation, APK-share handoff, and About/build identity. Their state references were re-audited after the patch with no unresolved members.

The JVM-only state gate was executed against the v4.5-era `MockModels.kt` + `ShellState.kt` using Compose runtime stubs and `kotlinc`. It passed queue insertion/reordering, selection clearing, playlist mutation, download state, provider-import progress, hidden-lens fallback, seeking, crossfade/offload/visualizer preference cycles, lyrics state, folder/extension exclusions, context rules, quick actions, sessions, audio profiles, custom sections, and exact 40 / 4,008 / 40,008 library fixtures.

Fresh output:

```
JVM_STATE_GATE=PASS queue=9 playlist=5 rules=3 profiles=3 library40k=40008
```

## Accessibility palette — recalculated from current source

The current `TsunamiTheme.kt` palette roles were independently recalculated using WCAG relative luminance. Every text/state role tested against its ground exceeds 4.5:1.

| Palette | ink | ink2 | ink3 | selected | possession | danger |
|---|---:|---:|---:|---:|---:|---:|
| Light | 16.74 | 7.49 | 4.59 | 5.56 | 4.55 | 5.82 |
| Dark | 16.62 | 10.44 | 5.95 | 8.88 | 9.77 | 7.63 |
| Light high contrast | 21.00 | 16.10 | 12.11 | 9.22 | 8.82 | 9.97 |
| Dark high contrast | 21.00 | 18.14 | 14.06 | 13.38 | 14.75 | 10.86 |

The authored control target remains 48 dp normally and 56 dp when Large controls is enabled.

## Build-stack compatibility

The isolated shell now has one internally coherent AGP 9 configuration rather than two contradictory Kotlin plugin models:

- Android Gradle Plugin 9.2.1;
- AGP 9 built-in Kotlin / KGP 2.2.10;
- no separate `org.jetbrains.kotlin.android` plugin;
- Compose compiler plugin 2.2.10;
- Gradle 9.4.1 through the checksum-pinned shell bootstrap;
- Kotlin/JVM 17;
- compileSdk 36 / targetSdk 36;
- Compose UI, Foundation, Animation, Runtime and UI-test 1.11.4;
- Activity Compose 1.13.0 and Core KTX 1.17.0.

The canonical gate and the static source verifier now enforce the same contract. The host bootstrap and Genesis workflow provision Android platform 36. This removes a prior self-contradiction in which one gate expected Kotlin Android 2.3.21 while another rejected that plugin.

## Fresh mark reconstruction check

The supplied 1536×1536 mark reference was re-measured directly from the current conversation asset at a 128 luminance threshold and compared against the current canonical geometry in `brand/tsunami-mark.svg`.

Reference components:
- arch: 134,856 dark pixels, bounding box `x=266…1256, y=343…751`;
- body: 258,700 dark pixels, bounding box `x=474…1049, y=584…1155`;
- total reference dark pixels: 393,556.

The current normalized master (outer circle center `500,509.61`, radius `509.61`; inner optical counter center `500,502.69`, radius `394.61`; terminal `y=411.11`; body center `500,531`, radius `289`) was rasterized back into reference coordinates. The resulting binary-mask comparison produced:
- intersection: 388,455 pixels;
- union: 395,946 pixels;
- IoU: **0.9810807534**;
- precision: **0.9938850439**;
- recall: **0.9870386933**.

The Compose `TsunamiMark` implementation now renders from those same canonical normalized parameters rather than an independent approximation, preventing SVG/Android brand drift.

## Fresh TSUNAMI Sans execution

The current checked-in `ui-shell/tools/generate_tsunami_sans.py` was materialized from GitHub blob `954b6b614e70a18b4d08dc5518725f277e9788dd` and executed in a clean local Python environment with the exact pinned dependencies already available: FontTools 4.63.0, Shapely 2.1.2 and Pillow 12.3.0. The reconstructed source itself was verified with `git hash-object` before execution, producing the same blob id; this closes the earlier ambiguity between source snapshots and generated evidence.

The generator completed successfully and produced five loadable TTF masters plus both proof images. A second FontTools validation pass reopened every font, checked UI/Western-European required characters, verified family/style metadata, weight classes and GPOS kerning, and confirmed **176 glyphs / 175 mapped characters with zero required-character omissions in every master**. The five TTF hashes reproduce the canonical values below exactly. The canonical Android/host gates now pin those TTF hashes explicitly so an accidental generator drift cannot masquerade as the same v4.5 family.

| Master | OS/2 weight | Glyphs | cmap | Bytes | SHA-256 |
|---|---:|---:|---:|---:|---|
| Light | 300 | 176 | 175 | 103,232 | `7accf1a077d9692caa0c0cee66199d6e473294ed650e72ebed5f88432a61215b` |
| Regular | 400 | 176 | 175 | 105,676 | `222d6d3b776b05c7be5f7bd6429f44d524a7b2e02091f540d708860d736f79da` |
| Medium | 500 | 176 | 175 | 106,440 | `a571e7f708512d3b7c1c9fd1fbdd59a43306c30c377c3b3a49ef29aed32ab6d8` |
| Semibold | 600 | 176 | 175 | 107,640 | `2a11482f1b26ee6013b93f362ea9612e7ec3258aca39328f6a76edb8e268cb4f` |
| Bold | 700 | 176 | 175 | 107,716 | `220b830dad37b338ebdcb33d2df278878d950d655841553c66995ebdc21286fa` |

Proof evidence:
- `tsunami-sans-proof.png`: 1700×1510, 162,619 bytes, SHA-256 `868a874159173f21009ca250a0523c6f6f0c4c66678c883bc57a8aa51ca7aaf6`;
- `tsunami-sans-ui-proof.png`: 1280×1260, 72,145 bytes, SHA-256 `b76b2792f0038471e58739e1e2464a6c3f7ba156c4448e020d91a56bcf5de5fa`.

Both proofs were visually inspected after generation at display scale. The family remains legible at the UI specimens included by the generator, preserves differentiated `I/l/1`, `O/0`, `rn/m`, `c/e` and `v/y` control pairs, and the five weights remain recognizably one family rather than naïve binary emboldening. This evidence is font-generation evidence only; Android rasterization remains part of the final device gate.

## GitHub Actions dispatcher isolation

A controlled dispatcher probe was executed after the normal Genesis workflow continued to report `startup_failure` with zero jobs. A brand-new workflow path, `.github/workflows/ui-shell-dispatcher-probe.yml`, contained a single `ubuntu-latest` job whose only step echoed `DISPATCHER_PROBE=PASS`. Both events at head `15c209659944e22ede3bdfe1a8eeb8cf3aaef2b2` were nevertheless routed to the same synthetic workflow registration:

- push run `36123906261`;
- pull-request run `36123911560`;
- workflow id `340225603`;
- workflow path `BuildFailed`;
- empty workflow name;
- conclusion `startup_failure`;
- zero jobs created.

The probe workflow was removed immediately after reproduction. This is concrete evidence that the current CI blocker occurs before runner allocation or any Gradle/Android/Kotlin command can execute; it is not application build evidence. Repository issue #20 records the dispatcher defect and its remediation criteria.

## Current source-tree refresh — 2026-09-25 10:45 UTC

A fresh connector-side audit was rerun after the latest UI Genesis source changes at source commit `ae285280807d8a7e6d13a4e26218410e31ccd8b6`. All 15 Kotlin source/test files were reread; delimiter/string/comment structure, unfinished markers, empty click handlers and direct production-coupling anchors were checked again.

Fresh inventory:
- Kotlin source/test files: **15**;
- `ShellState` properties/functions discovered: **306**;
- unresolved state-reference contract: **0** (the checked-in source verifier enforces this before any Android build);
- explicit `.clickable` sites: **23**;
- `TextCommand` invocations: **69**;
- `HitIcon` invocations: **28**;
- Settings `ActionRow` invocations: **107**;
- Settings `ToggleRow` invocations: **49**;
- Compose instrumentation tests: **19**;
- static audit findings across the 15 files: **0** unfinished/TODO markers, **0** empty click handlers, **0** direct production runtime anchors in the checked executable Kotlin.

The source-tree snapshot above is therefore the latest static evidence boundary. This refresh is not Android compilation evidence and does not alter the executable acceptance boundary below.

## Android verification status

The repository workflow still terminates as GitHub Actions `startup_failure` before any job is created. The affected run exposes zero jobs and no downloadable logs. The same infrastructure failure predates this branch, so it is not evidence of a shell compile failure; equally, it is not a substitute for a successful build.

Still required before final completion:

1. clean Gradle assemble of the current branch;
2. installation of the resulting `com.tsunami.shell` APK;
3. Compose instrumentation suite;
4. the thirty-seven-state device/emulator capture matrix;
5. crash-log scan;
6. monochrome and squint review derivatives;
7. visual review and any resulting corrective pass;
8. final APK hash + packaged verification evidence.

No final-completion claim should be made until those items have actually run.


## Fresh current-state JVM gate — 2026-09-25 10:59 UTC

The current `MockModels.kt` and `ShellState.kt` were reconstructed in the local verification container and their Git blob identities were checked before execution:

- `MockModels.kt`: Git blob `af52a3e83e56b34985d91bb99109ac35d989eef9`; local SHA-256 `96778ebf878a2fc3453634560e046811436351372394db9bb14e47d96064268d`
- `ShellState.kt`: Git blob `790e682a031682d80e826b84d2320787f6373c10`; local SHA-256 `1befb4905eb266a2649df186e3e31d8fa40cbac323470d5e39e21fa9b6ba1d81`

The local `git hash-object` values exactly matched the current GitHub blobs, so this run exercised the checked-in state/model source rather than a hand-edited approximation.

That rerun uncovered a defect in the **verification harness** itself: the state test first forced `shuffleMode = "Album-aware"` and later asserted that one `cycleShuffleMode()` call should produce `Discovery`. The implementation correctly cycles `Album-aware → Balanced`, so the assertion was stale. The gate was corrected in commit `061443d5845d2560fdc8366b44405fe2449455c1` to reset the fixture to `Balanced` before testing `Balanced → Discovery`.

After that correction, the current state gate compiled with `kotlinc-jvm 1.9.0` on Java 21 and passed the full behavior program:

```
JVM_STATE_GATE=PASS queue=9 playlist=5 rules=3 profiles=3 shuffle=Discovery accessibility=true/true library40k=40008
```

This fresh run covers current queue insertion, shuffle behavior, selection mutation, playlist insertion, downloads, provider-import progress, hidden-lens fallback, seeking, longform resume, transition/offload/visualizer state, lyrics state, library exclusions, accessibility state, swipe mappings, album-artist mode, migration state, shuffle intelligence, download/scrobble policy, path remapping, context rules, quick actions, sessions, audio profiles, custom sections, buffering recovery, unavailable-track guarding, partial-state fixtures, and the exact 40 / 4,008 / 40,008 library-scale fixtures.

This is executable JVM evidence for the shell's deterministic state machine. It still does not substitute for Compose/Android compilation, rendering, installation, instrumentation or device review.

## Cross-repository runner-allocation isolation

The Android build was also mirrored byte-for-byte into public repository `brass-crusader-tx/chromagora-os` on isolated branch `build/tsunami-ui-genesis-20260925`. A fresh tree comparison found **30 / 30 mirrored Android project/source files with identical Git blob SHA values** between the current Genesis branch and the public mirror; mismatches: **0**.

The public mirror still could not obtain a hosted runner. Most importantly, run `36126858910` at mirror commit `ec361b2a82689dce39fd4cab37a1ce802ef1c86e` requested three jobs containing only one native echo statement each:

- Windows job `108044862982`
- macOS job `108044863184`
- Ubuntu job `108044863189`

All three concluded `failure` with `steps=[]` before user code executed. A prior no-action Ubuntu probe, run `36126525118` / job `108043798723`, failed identically. The normal mirrored Android builder runs `36125974081` and `36126524905` also failed before steps.

Consequently the outstanding Android-build absence is now isolated beyond the private TSUNAMI repository, Android tooling, Gradle, checkout actions, third-party actions and any one hosted OS image. The failure is at hosted-runner allocation / account-or-platform Actions infrastructure. This diagnosis is evidence about the build environment only; the final APK/device acceptance gate remains outstanding.


## TSUNAMI Sans v4.6 optical-correction rerun — 2026-09-25

The current v4.5 proof was regenerated outside Android and then deliberately stress-inspected across all five masters at large size for the difficult set:

`S s G C R a e g r t k y 2 3 5 6 8 & ? @`

That pass exposed three concrete optical defects that were still visible despite the earlier v4.5 improvements:

1. `C/G` apertures constricted too aggressively as weight increased;
2. the single-storey `a` used a full-height attached stem that became congested in Bold;
3. `e/g/t` required cleaner aperture/descender/crossbar behavior in the heavy masters.

The generator was revised and rerun as **TSUNAMI Sans v4.6**. The second proof pass showed materially cleaner heavy-weight `C/G` openings, a clearer single-storey `a`, a less congested `e`, a more deliberate `g` descender and a narrower/lifted `t` crossbar.

Fresh generated master evidence:

| Master | OS/2 weight | Bytes | SHA-256 |
|---|---:|---:|---|
| Light | 300 | 103,452 | `68eecf46511fb29ab878e686832c9eb058b714f36e037f7f156613b61a325dd0` |
| Regular | 400 | 105,928 | `50849f038028506f792c43cdfa047bc3c8c970c650184be21a1883e7acf3aef8` |
| Medium | 500 | 106,728 | `300d635dd38a558c5b487cfe37836272c25d7ebaeda05f94e7f90d0fe05e485a` |
| Semibold | 600 | 107,956 | `7ba723c4b2526c6e13d08860a678ef36d7119a8d3ef7cd13b9cdfc560b80a2dd` |
| Bold | 700 | 107,952 | `cc21c29996dad398d588d339f553b9ece8c79cde69531af9370d780beb8d5b18` |

Every generated master was reopened with fontTools and passed:

- family name exactly `TSUNAMI Sans`;
- version exactly `Version 4.600`;
- weight classes exactly 300 / 400 / 500 / 600 / 700;
- complete required UI + Western-European character repertoire;
- GPOS kerning present;
- explicit non-collision checks for `I/l`, `l/1`, `O/0`, `c/e`, and `v/y`.

Fresh executable result: `FONT_VALIDATION=PASS`.

The canonical gate was updated to pin the v4.6 hashes, family/version metadata and ambiguous-pair outline guards. This closes the earlier discrepancy where a visually improved generator could drift while still satisfying only cmap/weight checks. Android rasterization remains outstanding until the build infrastructure can allocate a runner.


## Accessibility semantic pass — 2026-09-25

A fresh audit of custom interactive surfaces found that several direct `.clickable` compositions relied on readable text but did not expose an explicit semantic role/state contract. The affected surfaces included the compact primary index, library object rows, pre-query search intents, queue rows, lyric seek rows, output routes, onboarding choices, the recovery action, and listening-environment entry.

Those surfaces were corrected so the authored UI remains accessible without substituting stock Material controls:

- primary destinations identify as tabs and preserve selected state;
- Settings, onboarding, recovery, library objects and listening-environment entry identify as buttons;
- disabled pre-query catalogue intent exposes disabled semantics while offline;
- queue rows announce item/title/artist and current-playing state;
- lyric rows announce seek intent and current lyric;
- output rows announce route/detail and active state;
- the existing custom time ruler retains adjustable `setProgress` semantics;
- settings toggles continue to expose switch roles plus textual state.

The accessibility gate was expanded to make those anchors mandatory. During that work, a latent verifier defect was also found: the high-contrast palettes use Compose's `Color.White` / `Color.Black` constants for their primary roles, while the verifier only parsed ARGB literals. Consequently a nominal high-contrast check could fail before actually evaluating the intended colors. The parser now normalizes the named constants to their ARGB equivalents before computing contrast.

Fresh independent contrast recomputation from the current `TsunamiTheme.kt`:

| Palette | ink | ink2 | ink3 | selected | possession | danger |
|---|---:|---:|---:|---:|---:|---:|
| Light | 16.74 | 7.49 | 4.59 | 5.56 | 4.55 | 5.82 |
| Dark | 16.62 | 10.44 | 5.95 | 8.88 | 9.77 | 7.63 |
| Light high contrast | 21.00 | 16.10 | 12.11 | 9.22 | 8.82 | 9.97 |
| Dark high contrast | 21.00 | 18.14 | 14.06 | 13.38 | 14.75 | 10.86 |

All tested text/state roles therefore remain at or above **4.5:1** against their ground. A fresh connector-side semantic-anchor check over the seven critical source files found **0 missing anchors**.

A post-patch structural scan of all 15 Kotlin source/test files also found **0 delimiter/lexical/import issues**, and a fresh cross-file state resolution pass still found **306 ShellState members / 0 unresolved `state.*` UI references**, with the interaction inventory unchanged at 23 explicit `.clickable` sites, 69 `TextCommand` invocations, 28 `HitIcon` invocations and 19 instrumentation tests.


## Fresh TSUNAMI Sans v4.7 byte-identical execution — 2026-09-25 12:40 UTC

The **current** GitHub generator blob `51a391fecf19226b9653c084c33a4395cfc8923b` was reconstructed byte-for-byte in the local verification container and its Git blob identity was checked before execution. It then ran with the gate-pinned dependency set: FontTools 4.63.0, Shapely 2.1.2 and Pillow 12.3.0.

The regenerated proof artifacts are likewise deterministic for this source/dependency tuple: `tsunami-sans-proof.png` is 161,128 bytes / SHA-256 `766284ea44b2994f31bae0723bb5982c124288e9aed6e18b5e4a98076d627e0c`; `tsunami-sans-ui-proof.png` is 72,191 bytes / SHA-256 `ca8bd0ba8e38a545f0c629d157a20518865a93a43ac5f0a664313d15d4d45ae9`.

The generated masters reproduce the canonical v4.7 hashes exactly:

| Master | Weight | SHA-256 |
|---|---:|---|
| Light | 300 | `c295d45e732cf9d3c431c14465b4e64d0a164f6605da68a74ad207a59abe00fb` |
| Regular | 400 | `fb5803e5ed05442325bec033772bb5434b1f62740e02329d8d8c599e7d051c8b` |
| Medium | 500 | `0576bd38e1f0a34b40c22510249625abe27eda3cde39487a98d78102c5628c67` |
| Semibold | 600 | `6a196f5a93fbdbc4ccf821e12d9bb93963bb5d6263add32a90383ceb43acd914` |
| Bold | 700 | `063a6c7f56c48a78a45016cdf5b10e96a8fbf26b0ee5c30608f4a6c57af77841` |

A second FontTools pass reopened all five generated TTFs. Each reports family `TSUNAMI Sans`, version `Version 4.700`, the expected OS/2 weight class, 176 glyphs, a GPOS table, and zero omissions from the current UI/Western-European control repertoire. The two generator proofs were regenerated fresh at 1700×1510 and 1280×1260.

Both current proofs were then inspected at full resolution, followed by a dedicated large-glyph audit for `H O n o`, `S/s`, `G/C`, `R`, `a/e/g/r/t/k/y`, `I/l/1`, `O/0`, `2/3/5/6/8`, `&/?/@/%`, `rn/m`, `c/e` and `v/y`. The control pairs remain visually separable; the slashed zero is unmistakable beside O, capital I has bilateral bars while lowercase l has a terminal foot, and the current C/G/e apertures remain open across the Regular proof. The family retains its intentionally narrow geometric rhythm at the 12–34 px UI proof sizes without collapsing the hierarchy.

This is now **executed current-v4.7 font evidence**, not merely a checked-in verification contract. Android rasterization is still reserved for the physical/emulator device gate.

## Current v4.7 / Codespace verification contract — 2026-09-25

The executable source has advanced beyond the earlier v4.6 evidence above. The **current** TSUNAMI Sans generator identifies itself as `Version 4.700`; the host and canonical gates agree on the five expected master hashes:

| Master | Expected SHA-256 |
|---|---|
| Light | `c295d45e732cf9d3c431c14465b4e64d0a164f6605da68a74ad207a59abe00fb` |
| Regular | `fb5803e5ed05442325bec033772bb5434b1f62740e02329d8d8c599e7d051c8b` |
| Medium | `0576bd38e1f0a34b40c22510249625abe27eda3cde39487a98d78102c5628c67` |
| Semibold | `6a196f5a93fbdbc4ccf821e12d9bb93963bb5d6263add32a90383ceb43acd914` |
| Bold | `063a6c7f56c48a78a45016cdf5b10e96a8fbf26b0ee5c30608f4a6c57af77841` |

The canonical gate now derives the font-coverage requirement from **every quoted UI literal in the current Kotlin shell source**, in addition to the explicit Western-European/control repertoire; a glyph omitted by a newly added visible label therefore fails the font gate instead of silently falling back at runtime.

Because GitHub-hosted Actions continues to fail before runner allocation, an isolated Codespace fallback is now checked in at `tools/ui_shell_codespace_build.py`. Its contract is:

1. run the backend-free structural gate locally;
2. snapshot only UI-Genesis source/brand/research material;
3. upload it to the authenticated `TSUNAMI Builder` Codespace throwaway workspace;
4. run the shell's source and accessibility verifiers remotely;
5. require Gradle 9.4.1;
6. generate TSUNAMI Sans and assemble both the app and AndroidTest APKs;
7. emit SHA-256 values remotely, copy both APKs back, and reject either artifact if the local hash differs;
8. optionally install on an explicit—or the sole connected—physical Android device;
9. optionally run the Compose instrumentation suite and the complete 37-state physical-device capture matrix.

This fallback is **implemented but has not yet been executed in the present tool session**, because the available GitHub connector exposes repository operations but not Codespace SSH/CLI execution and no local Mac/ADB execution connector is presently exposed here. Accordingly, this section records the current executable verification path and its source-level integrity, **not** an APK build PASS. The acceptance boundary remains unchanged: current-head Android assembly, instrumentation, device captures, visual review, logcat/crash scan, and final APK/evidence hashes must actually run before completion can be certified.


## Current-head source/publish refresh — 2026-09-25 12:50 UTC

A fresh connector-side audit was rerun at Genesis head `eaa9823b48a206d3b83915a230ce9c943ab98dbe` after the latest queue-locality, v4.7 evidence, and Chromagora publication-path changes.

Current executable-source inventory:
- Kotlin source/test files: **15**;
- discovered `ShellState` members: **323**;
- unresolved `state.*` UI references: **0**;
- Compose instrumentation tests: **23**;
- explicit `.clickable` sites: **23**;
- `TextCommand` invocations: **70**;
- `HitIcon` invocations: **33**;
- Settings `ActionRow` invocations: **110**;
- Settings `ToggleRow` invocations: **47**;
- Android manifest permission declarations: **0**;
- anti-tackiness source anchors found for cards/pills/gradients/shadows/Material-icon identity: **0**.

The build contract was re-read from the current branch and remains internally aligned: AGP 9.2.1, built-in Kotlin / Compose compiler 2.2.10, Compose 1.11.4, compileSdk/targetSdk 36, JVM 17, and TSUNAMI Sans generation bound into `preBuild`.

The Chromagora preview publication path is now explicit and fail-closed. `ui-shell/tools/publish_chromagora_apk.sh`:
1. runs the current source and accessibility gates before touching the portal artifact;
2. attempts the canonical host build first;
3. falls back to `tools/ui_shell_codespace_build.py` when the host Android toolchain is unavailable;
4. rejects a missing/empty APK;
5. verifies APK ZIP structure contains the manifest and DEX payload;
6. atomically replaces the portal artifact only after a fresh build;
7. verifies the published SHA-256 exactly matches the built artifact;
8. writes a JSON sidecar containing source HEAD, source branch, package id, byte size, SHA-256, build backend and backend-free identity.

`source_verify.py` now makes those publication/Codespace safety anchors part of the source contract, including snapshot-hash and copied-APK hash verification in the Codespace fallback. This is **source-level verification of the publication path**, not evidence that the current APK has been built or published. The Android/device acceptance boundary remains unchanged.


## Master-mark raster fit and publication-path hardening — 2026-09-25

The supplied 1536×1536 logo reference was measured directly rather than judged by eye alone. At a 50% luminance threshold its black components occupy:

- arch: `x=266…1256`, `y=343…751`;
- body: `x=474…1049`, `y=584…1155`;
- total mark bounds: **991×813 px**.

The current `brand/tsunami-mark.svg` was independently rasterized into those exact 991×813 bounds and compared as a binary mask with the supplied reference:

- IoU **0.98399**;
- vector-mask precision **0.99566**;
- reference-mask recall **0.98822**;
- symmetric difference **6,329 px**, **1.61%** of the reference black area.

This materially supports the reconstruction geometry already shared by the SVG and Compose `TsunamiMark`. The brand deliverable now also includes `brand/TSUNAMI-MARK-SPEC.md`, which fixes the master circles, optical counter offset, terminal baseline, clear-space rules and small-size behavior.

A separate review of the build/publish fallback found and corrected two concrete artifact-chain defects before an APK could be trusted:

1. the Codespace builder wrote APKs under `ui-shell/dist/`, while the host builder and Chromagora publisher consumed repository-root `dist/`; the fallback would therefore build successfully and still fail publication;
2. three shell expansions in `publish_chromagora_apk.sh` had been accidentally escaped (`TSUNAMI_PORTAL_APK_TARGET`, `TARGET`, and `TSUNAMI_FORCE_CODESPACE_BUILD`), preventing the intended environment-variable behavior.

The Codespace, host and portal paths now converge on canonical repository-root `dist/`. Portal publication runs the cross-tool static gate, rejects dirty Genesis source, requires a Codespace manifest bound to the exact current HEAD, rejects `source_dirty=true`, checks the manifest APK SHA-256 against the built file, verifies ZIP/DEX structure, and only then atomically replaces the portal target. The static checker now rejects future path divergence or escaped-variable regressions. The Codespace build also invokes the checksum-pinned Gradle 9.4.1 bootstrap instead of trusting an ambient `gradle` executable.

These are source/pipeline corrections, not an Android-build PASS. Current-head assembly, install, 29-test instrumentation, the 37-state capture matrix, crash scan and human visual review remain the final acceptance boundary.


### Fresh connector-side current-head structural audit — 2026-09-25 12:58 UTC

After the artifact-chain corrections, the current Genesis branch was re-read through the authenticated repository connection rather than inferred from earlier counts. At head `58567ff2fb5a1ad60210589e8f3264cf80230537` the audit found:

- **15** Kotlin source/test files in the isolated shell;
- **323** declared `ShellState` members;
- **285** distinct `state.*` references from UI/test source;
- **0** unresolved state references;
- **23** Compose instrumentation tests;
- **18** Settings routes, with **0** unreachable routes and **0** assignments lacking a rendered route;
- **23** explicit `.clickable` surfaces;
- **70** `TextCommand` invocations;
- **33** `HitIcon` invocations;
- **110** Settings `ActionRow` invocations;
- **47** Settings `ToggleRow` invocations;
- **0** detected empty authored click/control handlers.

The deterministic visual harness now contains **37 base capture states**, spanning the core workspaces, queue/lyrics/output/visual listening modes, onboarding, empty/loading/error/buffering/partial/unavailable cases, no-artwork/missing-lyrics/audiobook/podcast states, 40/4,008/40,008-item library scales, 150%/200% text scaling, accessibility/high-contrast state, compact landscape, medium-width and expanded layouts, and deep Settings pages including explicit external-playback controls.

This is current-head structural evidence only; it does not substitute for Android compilation or screenshot inspection.


## Progressive provider-services workspace — 2026-09-25 13:4x UTC

The settings root now treats provider connectivity/import as a dedicated **Connected services** depth instead of expanding every provider, progress row and audit row inline. This preserves the root settings hierarchy while keeping connection, staged import, explicit exclusion/audit, and retained imported-library behavior fully reachable.

The deterministic acceptance matrix first advanced from 34 to 35 canonical base states with `35-settings-services`, then to **36** with `36-player-podcast`, and now to **37** with `37-settings-external-controls`, which exercises explicit Quick Settings / widget / Wear transport configuration independently of the other Settings depths. The capture script, visual-sanity expected set, host device gate, canonical gate, source contract and human visual-review protocol now agree on the same 37-state requirement.

This remains source and acceptance-contract evidence. Current-head Android assembly, instrumentation, device screenshots and human visual review still have to execute before the shell can be certified complete.


## Current-head source/acceptance refresh — 2026-09-25

A fresh connector-side audit was rerun at source head `bd875ef4d197ea08e503cf25383ef3f8bb4dc341` after synchronizing the Codespaces fallback and canonical visual matrix contracts.

Current executable-source inventory:

- Kotlin source/test files: **15**
- discovered `ShellState` members used by the UI: **337 definitions / 297 references**
- unresolved `state.*` references: **0**
- explicit `.clickable` sites: **23**
- `TextCommand` invocations: **75**
- `HitIcon` invocations: **33**
- Settings `ActionRow` invocations: **112**
- Settings `ToggleRow` invocations: **47**
- Compose instrumentation tests: **27**
- TODO/FIXME/XXX markers: **0**
- empty clickable handlers: **0**

The canonical Android gate, the Codespaces fallback, the self-hosted workflow and the source verifier now all require the same **exact 37-state** visual matrix. The Codespaces fallback had retained an obsolete 34-state count; that discrepancy is now removed, and `source_verify.py` explicitly guards the fallback's `len(base_captures) != 37` acceptance predicate.

This remains static/source-contract evidence. A current-head APK build, instrumentation run, 37-state device capture, logcat scan and human visual review are still required before final completion.



## Current-head dependency and host-build hardening — 2026-09-25 16:2x UTC

The isolated shell's declared build stack was rechecked against the current official Android/Gradle release lines before another host-build attempt:

- Android Gradle Plugin **9.2.1** is a released 9.2 patch;
- AGP 9.2's documented Gradle requirement/default is **9.4.1**;
- AGP 9.2's documented default SDK Build Tools is **36.0.0**;
- AGP 9.2's documented minimum/default JDK is **17**;
- AGP 9.2's documented Kotlin Gradle Plugin line is **2.2.10**;
- Compose UI/Foundation/Animation/Runtime **1.11.4** are released stable artifacts;
- Activity Compose **1.13.0**, Core KTX **1.17.0**, AndroidX Test Runner **1.7.0**, and ext.junit **1.3.0** are released artifacts.

The checked-in Gradle declarations therefore name real, mutually plausible release coordinates rather than speculative versions.

The canonical host builder was then hardened for the actual Mac/Android handoff path: on macOS it prefers an installed JDK 17 through `/usr/libexec/java_home -v 17`, rejects Java runtimes below 17, and now provisions API 36 **and** Build Tools 36.0.0 when either side of the Android toolchain is missing. The source verifier was extended so those host-provisioning guarantees cannot silently regress.

A fresh connector-side current-head source graph audit after these build-path changes still reports:

- Kotlin source/test files: **15**;
- discovered `ShellState` members: **337**;
- unresolved `state.*` references: **0**;
- Compose instrumentation tests: **29**;
- TODO/FIXME/XXX markers: **0**;
- empty direct click handlers: **0**;
- production I/O anchors: **0**;
- stock Material Card/FAB/icon identity anchors: **0**;
- `TextCommand` call sites: **77**;
- `HitIcon` call sites: **33**;
- Settings `ActionRow` call sites: **112**;
- Settings `ToggleRow` call sites: **47**.

This remains pre-build evidence. The executable Android acceptance boundary is unchanged: fresh current-head APK assembly, AndroidTest assembly, install, 29-test instrumentation, the 37-state device matrix, logcat/crash scan, and human visual review must actually run.


## Public build mirror parity and CI backoff — 2026-09-25 16:4x UTC

To remove private-repository checkout as a dependency from the remaining build path, the current Genesis Android project was synchronized into the public `brass-crusader-tx/chromagora-os` branch `build/tsunami-ui-genesis-20260925` under `tsunami-builder/ui-shell/`.

A fresh Git-tree comparison after synchronization found **40 / 40 UI-shell blobs byte-identical** to private Genesis source, with **0 missing and 0 divergent blobs**. The public mirror now also carries byte-identical copies of the four brand/spec files, the visual-review protocol, the Codespace/static verifiers, and the self-hosted acceptance-workflow contract required by the shell's source verifier. A checked-in `tsunami-builder/MIRROR-MANIFEST.json` binds those 40 UI-shell blobs to private Genesis head `86d025ba4a4e6401699f365aeabe6e771fe54dfc` using Git blob SHA values.

The public builder workflow was upgraded to verify that manifest with `git hash-object` before building, then run the canonical `ui-shell/tools/build_host.sh` path rather than an independent Gradle recipe. Consequently a future public build cannot silently compile a stale or structurally divergent mirror.

A fresh public builder run, **36162415943**, still failed before user code: job **108161950241** returned no step list and no downloadable job log. The simultaneous three-runner probe run **36162415914** returned Ubuntu, macOS and Windows jobs with `steps=null`. These reproduce the previously isolated hosted-runner allocation defect on the newly synchronized public source rather than exposing an Android compile failure.

Because repeated pushes were creating guaranteed pre-step failures, automatic UI-Genesis hosted/self-hosted triggers were deliberately paused; the relevant workflows remain available through `workflow_dispatch`. The obsolete public three-runner probe was removed. This reduces needless Actions requests while preserving a one-command/manual acceptance path for the moment runner dispatch is restored.


## Isolation recheck — 2026-09-25 16:4x UTC

A fresh base-to-head comparison against production `main` was run after the build-path work. At Genesis head `27c63dbedd8914b03b3756c7de2a23a9f78e0753`, the branch is ahead of base and its changed paths are confined to five top-level areas: `.github/`, `brand/`, `docs/`, `tools/`, and `ui-shell/`. The comparison found **zero** changed files under production `app/`, `wear/`, `control-plane/`, root `build.gradle.kts`, or root `settings.gradle.kts`.

This is concrete isolation evidence that the experiential shell work has not modified the production TSUNAMI Android runtime while the acceptance build remains outstanding.


## Current-source mirror and interaction audit refresh — 2026-09-25 17:1x UTC

The authenticated repository was reread at private Genesis source head `5330f7530374cfd8b5ce198e956cc6d7edd9b687` after the external-control surface work. A fresh connector-side count found **15 Kotlin source/test files**, **77 `TextCommand` call sites**, **33 `HitIcon` call sites**, **112 Settings `ActionRow` call sites**, **47 Settings `ToggleRow` call sites**, **20 explicit `.clickable` sites**, **1 `.combinedClickable` site**, and **28 instrumentation tests**. The same scan found no Material-theme/Card/FAB/stock-icon/gradient/shadow identity anchors among the prohibited tokens checked by the audit.

The settings topology was resolved independently: all **20** progressively disclosed settings destinations have an actual renderer and a reachable `settingsExpanded` assignment, with **0 missing render routes**, **0 unreachable routes**, and **0 empty authored click handlers** in the checked shell source.

The public build mirror was then resynchronized for the three executable blobs changed since its preceding snapshot (ShellState, SettingsScreen and GenesisInteractionTest), and its manifest was rebound to that private source head. A complete Git-tree comparison across every mirrored `ui-shell/` blob plus the eight support artifacts found **48 / 48 byte-identical blobs and 0 mismatches**. The resulting public mirror head is `a951f11e10c04619048baa136c3f1a874e5323af`.

This materially narrows the remaining acceptance work but does not replace it. The unresolved boundary is still Android-capable execution: current-head app/Test APK assembly, install, instrumentation, the 37-state screenshot matrix, Android TSUNAMI Sans raster inspection, crash/logcat scan, and the human artwork-removed / monochrome / squint / not-Spotify review.

## Current-head reconciliation — 2026-09-25

Fresh connector-side inspection at source head `d2232fc6e95029affc63fd73b7f364ced83acf16` found **14** main shell Kotlin files plus the Compose instrumentation source, **344** declared `ShellState` members, **304** distinct UI `state.*` references and **0 unresolved state references**. The current interaction surface contains **20** explicit `.clickable` sites, **1** `.combinedClickable` site, **78** `TextCommand` invocations, **33** `HitIcon` invocations, **115** Settings `ActionRow` invocations and **48** Settings `ToggleRow` invocations. The instrumentation source contains **29** `@Test` methods.

The deterministic visual contract is now **37** base states. A direct source comparison found **37 capture rows** in `capture_verify.sh` and **37 expected names** in `visual_sanity_verify.py`, with no missing names, extras or duplicates. The canonical gate, Codespaces fallback, host build gate and lightweight static gate have all been reconciled to the same 37-state requirement.

The latest PR run associated with this lineage again terminates as GitHub Actions `startup_failure` before any job is allocated; retrying the failed run through the Actions API is rejected because a startup-failure run has no retryable job. This remains infrastructure evidence only. It does **not** substitute for the mandatory current-head APK assembly, AndroidTest assembly, install, 29-test instrumentation execution, 37-state device capture, logcat scan, Android font raster inspection or human visual review.

## Current-head public mirror parity — 2026-09-25 17:54 UTC

The public Android-builder mirror was refreshed against private Genesis head `71f49a21681bf357cd32afcc0a04545e245a332a`. A direct Git-tree comparison of the mirror contract found **48 / 48 blobs byte-identical**: 40 files under `ui-shell/` plus the eight required brand/visual-review/build-support files, with **0 missing and 0 divergent blobs**. Public manifest commit `f18010517ac05466a99370edf11db1dabd6083f8` now names the same private head.

A fresh push-triggered builder attempt was then made from public commit `adaea32834796e6247d857948d18a04bdec7e280`: run **36170036683**, job **108187058460**. The run failed before a usable step sequence or log was materialized (`steps=null`; job-log fetch returned 404), so there is still no current-head Android assembly evidence. This refresh removes stale public-mirror source as a confounder while preserving the acceptance rule: only a real app/Test APK build, install, instrumentation, 37-state capture, logcat scan and human visual review can close the task.


## Current 44-state / 33-test acceptance boundary — 2026-09-25 18:1x UTC

The executable contract has advanced beyond the historical 37-state / 29-test references retained above for chronology. Current source at Genesis head `8bc602209d568ba23a81bb76c5de05919dc855d7` contains **33** Compose instrumentation tests and **44** unique deterministic base capture states. The capture script, image-sanity verifier, source verifier, canonical Android gate, host-device builder and Codespaces fallback all enforce the same 44-state cardinality; `source_verify.py` now floors instrumentation at 33 tests.

The seven states added after the earlier 37-state boundary are: `38-find-empty`, `39-find-error`, `40-player-queue-empty`, `41-settings-provider-connecting`, `42-settings-provider-error`, `43-settings-downloads-active`, and `44-settings-downloads-error`. They extend the acceptance surface into failure/recovery semantics rather than merely increasing screenshot volume.

The remaining completion boundary is therefore: current-head app APK + AndroidTest APK assembly, install, **33-test** instrumentation execution, **44-state** device capture, Android TSUNAMI Sans raster review, crash/logcat scan, monochrome/artwork-removed/squint review, and final artifact hashes. GitHub Actions `startup_failure` still prevents that executable evidence from being produced by the repository dispatcher itself.


## Current 45-state / 34-test acceptance boundary — 2026-09-25 18:27 UTC

The active executable contract supersedes the historical 44-state / 33-test snapshot above. Genesis now requires **34** Compose instrumentation tests and **45** unique deterministic base captures. The added state, `45-library-index`, is an artwork-free typographic Library mode; the image sanity gate requires it to render distinctly from the 40-item Ledger state, while the Compose test verifies that artwork semantics disappear in Index and return in Ledger.

The host build, canonical Android gate, Codespaces fallback, source verifier, capture harness and image verifier have been reconciled to the 45-state cardinality. Completion still requires those contracts to execute on Android-capable infrastructure: app/Test APK assembly, install, 34-test instrumentation, 45-state capture, crash/logcat scan, Android TSUNAMI Sans raster inspection, and human artwork/monochrome/squint/non-streaming-clone review.


## Current semantic-object truth / 36-test boundary — 2026-09-25 18:46 UTC

The active source contract now supersedes the 45-state / 34-test snapshot above. A fresh authenticated read at source head `b7751c4241907abb3bef9b13e261cbad0d2a2ca1` found **15** Kotlin source/test files, **352** declared `ShellState` members, **312** distinct `state.*` references and **0** unresolved references. The instrumentation source contains **36** unique `@Test` methods with **0 duplicate test names**, **0 TODO/FIXME/XXX markers**, and **0 empty direct clickable handlers** in the checked shell source.

The latest two regressions close semantic object-model defects discovered during a capability-truth audit rather than adding decorative surface area:

- mutable Library roots now propagate into the Folders lens using the same canonical path vocabulary (`/Music/Library`, `/Music/Field Recordings`, `/Audiobooks`) instead of settings and browsing maintaining divergent folder identities;
- object-level playback for Albums and Artists resolves a representative track inside the selected object, Folder playback resolves inside that folder, playlist detail preserves explicit playlist order, and the three Radio objects resolve distinct deterministic sets (owned library, connected source, or favourites) instead of all borrowing list position.

Two dedicated Compose regressions now bind those invariants: `libraryRootMutationPropagatesIntoFolderLens` and `albumObjectPlayUsesTrackFromThatAlbum`. `source_verify.py` floors the instrumentation contract at **36**, and the lightweight static gate explicitly requires both regression names.

The visual contract remains **45** unique base states. A fresh source comparison found **45 capture rows and 45 visual-sanity expected names**, with no duplicates, missing names or extras. The shell manifest still declares **zero Android permissions**. A fresh base-to-head comparison against production main found **zero** changed files under production `app/`, `wear/`, `control-plane/`, root `build.gradle.kts`, or root `settings.gradle.kts`; Genesis changes remain confined to `.github/`, `brand/`, `docs/`, `tools/`, and `ui-shell/`.

All **20** progressively disclosed Settings destinations were also re-resolved from current source: every destination has a renderer and a reachable assignment, with **0 missing render routes** and **0 orphaned pages**.

This is stronger current-head source evidence, not Android execution evidence. Completion still requires a fresh current-head app APK and AndroidTest APK, installation, **36-test** instrumentation execution, the **45-state** screenshot matrix, Android TSUNAMI Sans raster review, logcat/crash scan, monochrome/artwork-removed/squint review, and final artifact hashes. The repository's GitHub Actions dispatcher remains a pre-step infrastructure blocker; no workflow startup failure is counted as either a build pass or a build failure.


## Current progressive-settings topology / 37-test boundary — 2026-09-25 18:59 UTC

At source head `c3894b48b32c571c3b43c61fc993055934b7a765`, a fresh authenticated connector-side scan covers **15** Kotlin source/test files, **352** declared `ShellState` members, **312** distinct UI `state.*` references and **0** unresolved references. The shell exposes **20** progressive Settings routes with **0 missing/orphan route handlers**. The interaction inventory is **20** direct `.clickable` sites, **1** `.combinedClickable`, **84** `TextCommand` invocations, **34** `HitIcon` invocations, **116** Settings `ActionRow` invocations and **48** Settings `ToggleRow` invocations.

The instrumentation source now contains **37** unique `@Test` methods. The added regression, `progressiveSettingsRoutesRoundTripToStableRoot`, traverses Library profile, Custom library sections, Output profiles, Shuffle behavior, Visualizer, Listening services, Context rules and Quick actions/session depths, asserting that each route returns to the stable Settings root. Both `source_verify.py` and the lightweight static gate now require that regression; the source verifier floors the instrumentation contract at **37** tests.

The deterministic visual contract remains **45** exact base states. No Android build/install/instrumentation PASS is inferred from these source checks; current-head APK assembly, device execution, Android font raster review, the 45-state screenshot set, logcat/crash scan and human visual review still require an executable Android runner/host.

## Self-hosted runner dispatch isolation — 2026-09-25 15:10 EDT

The remaining hosted-Actions ambiguity was tested against the dedicated Mac workflow itself. The Genesis self-hosted workflow was temporarily given a branch-scoped push trigger without changing its job body; the resulting commit was `be7986a2508b6ad692ef6b839d55d89314934deb`.

GitHub created two synthetic runs for that commit:

- push run `36178091132`;
- pull-request run `36178095497`.

Both runs were again registered as workflow id `340225603`, empty workflow name, path `BuildFailed`, conclusion `startup_failure`, and completed before a single job existed. In particular, the push event never instantiated the declared `runs-on: [self-hosted]` Mac job. The temporary push trigger was then removed in commit `a9f15e1ac22c1960bd5e9eba1685b0d81c2098f0`.

This closes a further infrastructure question: the failure occurs before GitHub evaluates or allocates the requested runner class, so merely targeting the Mac self-hosted runner cannot currently bypass the dispatcher fault. It remains infrastructure evidence only; it does not count as Android build or device acceptance.



## Current manifest-bound type gate and refreshed public mirror — 2026-09-26

A fresh type/evidence audit found that the v4.8 generator and proof manifest had advanced beyond two duplicated hash tables retained in `tools/ui_shell_gate.py` and `ui-shell/tools/build_host.sh`. Those tables would have rejected the current proofed masters before Android compilation even though the generator itself was healthy. The duplication has been removed: both executable build paths now load `docs/TSUNAMI-SANS-v4.8-MANIFEST.json`, verify family/version identity, all five master SHA-256 values and byte sizes, and verify the proof-image hashes/byte sizes. `source_verify.py` additionally rejects any future build path that ceases to bind to the canonical manifest.

The current v4.8 manifest is bound to generator blob `1759a3ee680ef51d914d507d3ee2e93ec371f82f`. The 2026-09-26 Mac acceptance pass discovered that the previously recorded manifest bytes did **not** reproduce from that current source. The manifest was therefore reconciled to freshly generated outputs from the pinned FontTools 4.63.0 / Shapely 2.1.2 / Pillow 12.3.0 toolchain on macOS 15.7.5 x86_64. Python 3.12.14, 3.13.12 and 3.14.7 independently emitted identical TTF and proof-image hashes. FontTools reopened all five outputs as **TSUNAMI Sans Version 4.800**, with weight classes 300/400/500/600/700, 176 glyphs per master, required UI/Western-European coverage and GPOS. Cross-platform byte identity is not claimed without executed Linux evidence; the authenticated Codespaces diagnostic was unavailable because the account had exhausted its Codespaces usage/budget. Android text rendering remains part of the exact-current-head device pass.

The public build mirror on `brass-crusader-tx/chromagora-os:build/tsunami-ui-genesis-20260925` was then rebound byte-for-byte to private Genesis source head `11388f2ce43bb8c518a494e8044e5dba0f854e09`. Direct Git-tree comparison covered **56 build-critical blobs** (40 `ui-shell/` files + 16 support files) with **0 missing and 0 divergent blobs**; the public mirror manifest names that exact private head. This refresh also added the canonical v4.8 font manifest and root Android gate, both now required by the mirrored source verifier.

Push commit `03d38e5a42587f9a2beb140aa132214954149d60` created fresh public builder run **36246923694**, job **108417723315**. GitHub allocated the job object but failed it before a step sequence or log blob materialized (`steps=null`; job-log fetch returned 404 BlobNotFound). The simultaneous public self-hosted run **36246923706** remains queued pending a matching runner. Therefore neither event is Android compilation evidence: checkout, source verification, font generation, Gradle, Kotlin/Compose compilation, APK assembly, instrumentation and device capture still have no executed job output.

The current source-side audit also rechecked all 18 Kotlin/Kotlin-DSL files after the manifest changes: delimiter/string/comment balance and the high-risk Compose/import contracts returned **0 problems**. The shell manifest still declares no permissions, no production `com.tsunami.app.*` imports are present, and no direct network/MediaStore/ContentResolver client references were found. These checks strengthen the pre-build evidence but do not lower the executable acceptance boundary.


## Temporal Listen architecture + longform continuity hardening — 2026-09-26

At source head `f815f36b2a42c7323450a53a6e789b4a845efe8b`, LISTEN was reconciled with the design thesis instead of remaining a conventional stack of music-app sections. The compact workspace is now an explicitly typographic temporal ledger: `CURRENT THREAD / TIME` keeps the actual current playback object at `NOW`, recent context sits on dated markers, `OWNED ANCHORS / PINNED` exposes favourites that are not already in the thread, and `LIBRARY LENS / CHOOSE` changes deliberate owned-library selection. These rows deliberately render with `showArtwork=false`; LISTEN therefore retains hierarchy through TSUNAMI Sans, time markers, rules and the persistent Listening Spine rather than cover art.

The current-object row is no longer a static fixture assumption. It is tagged as `listen-current-<track-id>`, and the new instrumentation regression `listenTemporalLedgerTracksCurrentObjectWithoutArtworkDependency` asserts that the initial `Afterglow` thread contains no artwork semantic, then starts `Passage / Northbound` and requires the current temporal marker to migrate to that object.

Longform continuity was hardened at the same time. Removing the current longform item from the queue stores its position before queue mutation; marking a podcast/audiobook unplayed resets its persisted resume position (and active player position) to zero instead of leaving a contradictory “unplayed at one-third” state. The longform regression now exercises played → unplayed and requires the visible position to return to `0:00`.

Static delimiter/string/comment scans of all five touched executable/gate files returned no structural errors. The Compose instrumentation source now contains **38** unique tests. `ui-shell/tools/source_verify.py` raises its test floor to 38 and binds the temporal LISTEN anchors (`CURRENT THREAD`, `LIBRARY LENS`, `TemporalTrackRow`, `showArtwork=false`); the root static checker independently requires the new regression. The deterministic visual matrix remains **45** states, including `01-listen-light` / `33-listen-no-artwork`, whose artwork-identity pair is already enforced by the monochrome/squint visual-sanity gate.

This is exact-current-source evidence only. Completion still requires current-head app and AndroidTest APK assembly, installation, the 38-test instrumentation run, all 45 physical/emulated screenshots, Android TSUNAMI Sans raster inspection, crash/logcat scan, and human artwork-removed / monochrome / squint / non-streaming-clone review. GitHub Actions remains blocked before executable steps and is not counted as either an Android build pass or build failure.
