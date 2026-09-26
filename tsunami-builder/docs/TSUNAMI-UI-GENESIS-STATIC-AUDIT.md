# TSUNAMI UI Genesis — fresh static audit evidence

Audit time: 2026-09-25 UTC  
Audited source tree (before this documentation-only refresh): `6a4ed61bea298d8f5ac6ce462fdaf9f3d9d57eb9`

This audit was rerun against the **current source tree** after the latest navigation, search, Signal, advanced-settings, playlist, longform, accessibility, font, responsive-topology and device-gate changes. The only change made after the cited source tree for this audit is this evidence-document refresh. It is intentionally a source-contract audit, not a substitute for Android compilation or device review.

## Kotlin/source graph audit

A fresh connector-side read of all **15** Kotlin source/test files under `ui-shell/app/src/` was inspected for state resolution, backend leakage, interaction-surface collapse and instrumentation coverage.

Current results:

- Kotlin source/test files: **15**
- unresolved `ShellState` member references: **0**
- `ShellState` members discovered: **337**
- Compose instrumentation tests discovered: **29**
- explicit `.clickable` interaction sites: **20**
- `.combinedClickable` interaction sites: **1**
- `TextCommand` invocations: **77**
- `HitIcon` invocations: **33**
- Settings `ActionRow` invocations: **112**
- Settings `ToggleRow` invocations: **47**
- Android manifest `<uses-permission>` declarations: **0**
- production I/O anchors in executable Kotlin code: **0**
- stock Material icon identity anchors: **0**
- Material Card composition anchors: **0**

The state-reference contract was checked in two bounded passes so every current UI/test file could be resolved against the same `ShellState` member inventory. Both passes returned an empty unresolved set. A separate settings-route audit resolved all 20 progressively disclosed destinations against every `settingsExpanded = "…"` assignment: **0 unreachable routes and 0 missing render routes**. A direct empty-handler scan found **0 dead click handlers**.

Fresh connector-side counting on the cited source tree reproduced the current interaction inventory exactly: **20** explicit `.clickable` sites, **1** `.combinedClickable` site, **78** `TextCommand` invocations, **33** `HitIcon` invocations, **115** Settings `ActionRow` invocations, **48** Settings `ToggleRow` invocations, **344** discovered `ShellState` properties/functions, **304** distinct UI `state.*` references, **0 unresolved state references**, and **29** instrumentation tests. The aggregate authored-action count is **295**, so the source gate now protects the total interaction surface while allowing ad-hoc clickables to migrate into the focus-visible primitives. The same pass found **0** direct production-runtime imports among the checked shell source files. The source gate now additionally enforces `LISTENING_ACTION_SURFACES=PASS`: stable transport, listening modes, object actions, quick actions, mini-player extras and notification actions cannot silently collapse back into overlapping command sets. A fresh action-surface audit also confirms the current listening action architecture separates stable transport, listening modes, object actions, quick actions, and mini-player extras instead of rendering duplicate controls. It also confirms that the newly added player/notification action customization remains state-driven inside the shell rather than importing production playback or notification services.

The 29 checked-in interaction tests currently cover:

1. rotation preserving Library and listening context;
2. primary navigation and listening-context preservation;
3. expanded transport, timestamp, lyrics and output interaction;
4. library multi-select mutation;
5. folder-object counts and contents following fixture truth;
6. reversible library object depth;
7. pre-typing search intent;
8. bounded typo/transposition tolerance;
9. reversible search object depth;
10. library-centric Listen lenses;
11. folder search object navigation;
12. interactive Signal depth;
13. playback settings state;
14. playlist insertion visibility;
15. consequential history-clear confirmation before mutation;
16. progressive advanced settings;
17. lyric timing/presentation state;
18. library exclusion controls;
19. library section visibility + metadata template effects;
20. migrated production-capability homes;
21. provider import audit surviving disconnect/reconnect;
22. audiobook/podcast longform separation;
23. full-player object actions driving the listening core;
24. mini-player action customization changing the persistent Listening Spine;
25. unavailable-media inspection without falsely entering playback;
26. customized play/pause honoring unavailable-media state;
27. removing the current queue item advancing locally and stopping cleanly when the queue empties;
28. removing the current queue item advancing locally and stopping cleanly when the queue empties;
29. library/search state response.


## Build-stack audit

Fresh build-file inspection still resolves to one coherent isolated Android toolchain:

- Android Gradle Plugin: **9.2.1**
- AGP 9 built-in Kotlin line: **2.2.10**
- separate `org.jetbrains.kotlin.android` plugin: **absent**
- Compose compiler plugin: **2.2.10**
- Gradle bootstrap: **9.4.1**
- compileSdk / targetSdk: **36 / 36**
- Compose UI line: **1.11.4**
- Java/JVM target: **17**

The shell manifest continues to declare **no Android permissions**, preserving the prototype's backend-free boundary. The static gate now also asserts exact SVG ↔ Compose parity for the measured 1000 × 820 TSUNAMI master mark: outer/inner arch geometry, terminal cut, sweep angles and 289-unit body circle must remain synchronized.

## TSUNAMI Sans source contract

The current generator source still carries the required deterministic family contract:

- family: **TSUNAMI Sans**
- generator version: **4.700**
- five declared masters: **Light 300 / Regular 400 / Medium 500 / Semibold 600 / Bold 700**
- deterministic font timestamp anchor: **3873139200**
- OpenType GPOS feature generation: **present**

The current v4.7 master hashes are pinned consistently by the host/canonical verification paths; an accidental generator drift therefore fails before Android packaging. Android text rasterization is still part of the mandatory device gate.

## Visual verification contract

The current deterministic capture contract contains **37 named base states**. A fresh source-side comparison found **37 capture invocations and 37 expected visual-sanity states with no missing or extra names**. The matrix includes compact/medium/expanded responsive layouts, portrait and landscape, light/dark, 40/4k/40k libraries, 1.5× and 2.0× font scale, empty/loading/buffering/unavailable/partial states, settings depth including connected-service import state, queue/lyrics/output/visual player modes, and explicit no-artwork captures, plus separate audiobook and podcast listening environments, and a dedicated external-playback-controls Settings capture. The visual verifier additionally requires unique critical topology groups, monochrome derivatives, blurred squint derivatives, both orientations, and a contact sheet.


This fresh audit provides concrete current-head evidence that the isolated shell source graph has not regressed into unresolved mock-state references, production data access, permission creep, generic Material identity, or a collapsed interaction/test surface while feature depth increased. Settings rows now merge descendant semantics into one coherent control node, and track-ledger rows expose keyboard/D-pad focus with a visible structural indicator rather than relying on color alone.

## What this does **not** establish

It does not replace the still-required Android-capable verification:

1. clean current-head Gradle dependency resolution and compilation;
2. debug APK assembly;
3. installation of `com.tsunami.shell`;
4. Compose instrumentation execution;
5. device/emulator launch and back-stack exercise;
6. the deterministic visual-state capture matrix;
7. Android rendering inspection of TSUNAMI Sans;
8. monochrome, artwork-removed and squint review;
9. crash/logcat scan;
10. final APK and evidence-bundle hashes.

Repository GitHub Actions remains a pre-job infrastructure blocker: the dispatcher returns `startup_failure` before a job is allocated, so that infrastructure state cannot be treated as either an Android pass or Android failure. The current audit therefore deliberately stops short of claiming APK availability or Android-renderer validation.

## Current provider-complete structural refresh — 2026-09-25 18:02 UTC

At Genesis head `ecb22ae8b4411a13167d2fb3dc74289817830feb`, a fresh connector-side lexical/state audit covered all **15 Kotlin source/test files**. Results: **344** discovered `ShellState` members, **304** distinct `state.*` UI references, **0 unresolved references**, **29** instrumentation tests, **20** direct `.clickable` call sites, **1** `.combinedClickable`, **78** `TextCommand` invocations and **33** `HitIcon` invocations. The scan found no delimiter/string/comment corruption, TODO/FIXME marker, empty direct click handler, Material-component identity import, or production-backend anchor.

The capability inventory also now represents every provider family present in production provider contracts: **YouTube Music, Apple Music, Amazon Music, Spotify and TIDAL**. `providerImportAuditPreservesLibraryAcrossDisconnect` asserts all five names in the progressive Connected Services environment before exercising the YouTube Music import/audit/disconnect flow.

The public builder mirror is bound to the same private head by manifest commit `bd90f89fed4e8bca6adc1cd873ea908d7b861400`; verification of all **48 mirror-contract blobs** (40 UI shell + 8 support) reports no missing or divergent SHA/size pairs.


## Current-head acceptance-contract reconciliation — 2026-09-25 18:1x UTC

Fresh authenticated inspection at Genesis head `8bc602209d568ba23a81bb76c5de05919dc855d7` supersedes the historical counts above where the shell has subsequently grown. The current isolated tree contains **15** Kotlin source/test files, **33** Compose instrumentation tests, **20** direct `.clickable` sites, **1** `.combinedClickable`, **82** `TextCommand` invocations, **34** `HitIcon` invocations, **116** Settings `ActionRow` invocations and **48** Settings `ToggleRow` invocations, for **301** authored interaction sites under the source gate's counting model. The current capture harness contains **44 / 44 unique base state names**, and the image verifier's expected-state set resolves to the same 44 names.

The additional acceptance states beyond the earlier 37-state snapshot are deliberately adversarial rather than decorative: empty and failed search journeys, an empty player queue, provider connecting/error states, and active/error download states. The source verifier now floors instrumentation at **33 tests** and requires exact **44-state** capture/verifier parity. These updated counts are source-contract evidence only; they do not replace Android compilation, device execution or human visual review.


## Artwork-independent Library Index refresh — 2026-09-25 18:27 UTC

At Genesis head `7319d053fbe330769efc089288a500b8cb8ddb2f`, the current source graph contains **15** Kotlin source/test files, **34** Compose instrumentation tests, **352** resolved `ShellState` members and **0 unresolved `state.*` references** in a fresh authenticated source scan. The current deterministic visual contract is **45 unique base states** with exact capture/verifier set parity; state `45-library-index` exercises a structural, artwork-free typographic Index rather than merely replacing covers with placeholders.

The Library view control was also reconciled to one canonical two-option surface—`Ledger` and `Index`—after a transient implementation overlap was detected during the source audit. Instrumentation now verifies that the Index removes artwork semantics while preserving the track itself, and that returning to Ledger restores artwork. The source verifier floors instrumentation at **34 tests**, pins the Index implementation anchors, and the image gate requires the 40-item Ledger and Index captures to differ.

This remains source-level evidence; Android compilation/device rendering remains outstanding.


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

## Current source/brand refresh — 2026-09-25 15:16 EDT

A fresh authenticated scan at pre-documentation source head `be6cfd6c2ae3be5af88f7e666d2da59e2230c23c` reread all **15** Kotlin source/test files. The scan found **0** delimiter/string/comment failures, **0** TODO/FIXME/HACK markers, **0** empty handlers, and **0** forbidden production/backend or generic-Material identity anchors. The authored interaction inventory remains **20** direct `.clickable` sites, **84** `TextCommand` invocations, **34** `HitIcon` invocations, and **37** Compose instrumentation tests.

All **20** Settings destinations referenced by `settingsExpanded` resolve to both a rendered page and a title; missing render routes: **0**; missing title routes: **0**. The isolated manifest still declares **zero Android permissions**. The build contract remains compileSdk/targetSdk **36/36**, minSdk **26**, Compose enabled and Java/JVM **17**. The type generator identifies family **TSUNAMI Sans**, version **4.700**, with five masters at weights **300 / 400 / 500 / 600 / 700**. The capture harness still contains exactly **45** named base states and the host gate still requires physical-device instrumentation, visual sanity, crash scanning and exact 45-state evidence.

The canonical mark was also remeasured directly against the supplied 1536 px raster in the active task. Mapping the current 1000 × 820 master geometry to the supplied dark-content bounds and thresholding at luminance 128 produced **IoU 0.9834846126**, **precision 0.9963857987**, and **recall 0.9870056612**. This independently reconfirms that the checked-in vector/Compose geometry remains a close reconstruction of the supplied mark rather than a generic semicircle-plus-dot approximation.

These are source and geometry checks only. They do not substitute for current-head Android compilation, installation, instrumentation or human review of Android-rendered screenshots.



## Current 217-anchor audit + self-hosted dispatcher probe — 2026-09-25 16:0x EDT

At source head `78face894834e20ea19b29dfc0ea9ff2df2b3bcd`, a fresh authenticated source read re-ran the branch's architecture-anchor contract rather than relying on historical documentation. Across the 13 source files represented by `REQUIRED_ANCHORS`, **217 / 217 anchors are present**:

- MockModels 27 / 27
- ShellState 70 / 70
- TsunamiMark 6 / 6
- GenesisShell 7 / 7
- Listen 7 / 7
- Find 5 / 5
- Signal 8 / 8
- Onboarding 3 / 3
- Expanded Listening 15 / 15
- Library 16 / 16
- Settings 43 / 43
- Primitives 4 / 4
- Theme 6 / 6

A separate current-head lexical/cross-reference scan covered all **15** Kotlin source/test files: delimiter/lexical failures **0**, unresolved `ShellState` UI references **0**, and forbidden production/backend or generic-Material identity anchors **0**. PR #16's current diff against `main` still changes **0 production runtime files** under `app/`, `wear/`, or `control-plane/`.

The self-hosted lane was then tested as an explicit escape hatch for the hosted Actions problem. A temporary branch-push trigger was applied at commit `bb055d4416e76e7dff05aa31bd6ce877e134e306`. GitHub immediately produced the same pre-job synthetic failure—push run **36182967561** and pull-request run **36182971506**, both `BuildFailed / startup_failure`, with no job allocation. Because this establishes that the dispatcher failure occurs before either hosted or self-hosted workflow steps can execute, the self-hosted workflow was returned to explicit `workflow_dispatch` at `78face894834e20ea19b29dfc0ea9ff2df2b3bcd`.

This evidence strengthens the source-contract boundary and isolates the current infrastructure blocker, but it still does **not** substitute for current-head Gradle compilation, APK/device installation, instrumentation, Android TSUNAMI Sans raster review, the exact 45-state capture matrix, crash scan, or human visual acceptance.
