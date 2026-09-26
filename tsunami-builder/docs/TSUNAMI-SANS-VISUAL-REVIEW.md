# TSUNAMI Sans — visual review log

## 2026-09-26 · v4.8 current source

The checked-in generator is now **TSUNAMI Sans v4.8**. This supersedes the v4.5 proof pass recorded below. Subsequent type-specific revisions deliberately changed construction rather than merely changing metadata: the C/G aperture model was reopened as weight increases, cap/x-height optical overshoot was made explicit, and the difficult geometric control pairs retained separate constructions instead of collapsing toward mathematical circles or uniform stroke expansion.

Current canonical generator facts, cross-checked against the build gate:

- family: **TSUNAMI Sans**
- version metadata: **Version 4.800**
- masters: Light 300 / Regular 400 / Medium 500 / Semibold 600 / Bold 700
- stem targets: 42 / 68 / 86 / 102 / 120
- cap height / x-height: 710 / 500, with explicit cap and x-height overshoot
- fixed OpenType timestamp for byte-reproducible masters
- Western-European and operational-symbol coverage
- GPOS kerning
- ambiguity checks for the UI control pairs (I/l/1, O/0, rn/m, S/s, G/C, e/c)
- Android build gates regenerate the fonts and reject metadata, coverage, ambiguity, kerning or canonical-hash drift

### Canonical v4.8 master hashes

| Master | Weight | SHA-256 |
|---|---:|---|
| Light | 300 | `845348eb5eed0a11551122e11f882c4f1c04b2f002c6651cb659f2e00dfc78e3` |
| Regular | 400 | `036bdedd69bc1565d140faec9cb17d3c27d55cef5e435c8d89068943953711a8` |
| Medium | 500 | `47b778217bc8f55f2777080454c3236571e16961caef708cbe967d98d322b3d7` |
| Semibold | 600 | `812a1cf08101cc1abd5f29c6094ab2f6117e93a3d3471c31da298eaa48175a5d` |
| Bold | 700 | `f7c0197e54b1c352469fac1e54baf9518453eab106ee09111d5ae183c4ae8013` |

The canonical v4.8 manifest pins both the five generated master hashes **and** the two proof-image hashes/byte sizes against generator blob `1759a3ee680ef51d914d507d3ee2e93ec371f82f`. During the 2026-09-26 Mac acceptance pass, the preceding manifest was found not to reproduce from that current source. Fresh executions with the pinned FontTools 4.63.0 / Shapely 2.1.2 / Pillow 12.3.0 toolchain produced byte-identical outputs under Python 3.12.14, 3.13.12 and 3.14.7 on macOS 15.7.5 x86_64. The current five masters are 102868 / 105204 / 106020 / 107108 / 106912 bytes and the proofs are:
- `tsunami-sans-proof.png` — 159128 bytes, SHA-256 `4b64248e1243a22997819d4e9a13671320ca55b51a46b2cd3b2d1c85b2212e88`
- `tsunami-sans-ui-proof.png` — 70419 bytes, SHA-256 `14a9002e5021c48368c104680249bb0a7df8816e30fba4fec9af608cbd757986`

This is a canonical **Mac-host** byte contract. Cross-platform byte identity is not asserted without executed Linux evidence; the Codespaces diagnostic could not run because the account had exhausted its Codespaces usage/budget.

The canonical Android gate and host build now read `docs/TSUNAMI-SANS-v4.8-MANIFEST.json` instead of duplicating stale hash literals; source verification rejects any pipeline that ceases to bind to that manifest.

**Acceptance boundary remains unchanged:** desktop/Pillow proofing validates construction and obvious raster defects, but final type acceptance still requires the current v4.8 masters to be rendered by Android on the exact current-head shell and inspected at actual UI sizes. The Mac Android runner is available; the final current-head rebuild/device pass is required after this manifest reconciliation.

## 2026-09-25 · v4.5 historical proof pass
The v4.4 generator was executed independently from the Android build graph and both emitted specimens were inspected at full resolution. That pass removed the early malformed forms, but a second inspection at UI scale still exposed three weaknesses: Regular/Medium were too anaemic for small Android labels, the lowercase `e` aperture remained too occluded, and `t` retained a gratuitous foot that read as calligraphic rather than geometric.

v4.5 changes construction rather than merely metadata:

- stem targets are rebalanced to 42 / 68 / 86 / 102 / 120 for Light through Bold, preserving Light restraint while strengthening the workhorse UI weights;
- lowercase `e` receives a substantially more open right aperture and a longer crossbar;
- lowercase `t` is simplified to a straight geometric stem and crossbar;
- side bearings remain restrained and minimally weight-dependent so body/UI text does not look artificially tracked;
- `O/0`, `I/l/1`, `rn/m`, `S/s`, `G/C`, and `e/c` remain explicit proof pairs;
- Western-European coverage, operational punctuation and GPOS kerning remain present.

A fresh local execution of the **current GitHub generator source** produced five valid TTFs. FontTools reopened every master and verified family name **TSUNAMI Sans**, version **4.500**, 176 glyphs / 175 mapped characters per master, weight classes 300 / 400 / 500 / 600 / 700, complete required UI/Western-European coverage, and a GPOS table in every master. The generator now fixes the OpenType head timestamp, and two independent executions produced byte-identical TTF hashes.

### Fresh v4.5 generated-font hashes

| Master | Weight | SHA-256 |
|---|---:|---|
| Light | 300 | `7accf1a077d9692caa0c0cee66199d6e473294ed650e72ebed5f88432a61215b` |
| Regular | 400 | `222d6d3b776b05c7be5f7bd6429f44d524a7b2e02091f540d708860d736f79da` |
| Medium | 500 | `a571e7f708512d3b7c1c9fd1fbdd59a43306c30c377c3b3a49ef29aed32ab6d8` |
| Semibold | 600 | `2a11482f1b26ee6013b93f362ea9612e7ec3258aca39328f6a76edb8e268cb4f` |
| Bold | 700 | `220b830dad37b338ebdcb33d2df278878d950d655841553c66995ebdc21286fa` |

The current expanded specimens remain generated artifacts rather than checked-in binary source. A fresh execution of the current generator produced:

- `ui-shell/tools/proofs/tsunami-sans-proof.png` — 1700×1510, SHA-256 `868a874159173f21009ca250a0523c6f6f0c4c66678c883bc57a8aa51ca7aaf6`
- `ui-shell/tools/proofs/tsunami-sans-ui-proof.png` — 1280×1260, SHA-256 `b76b2792f0038471e58739e1e2464a6c3f7ba156c4448e020d91a56bcf5de5fa`

The generator source used for this review was independently reconstructed from the connected repository and verified byte-for-byte with Git blob id `954b6b614e70a18b4d08dc5518725f277e9788dd` before execution. The five TTFs reproduced the canonical hashes above exactly. The main proof also reproduced its recorded hash exactly; the UI-size PNG was regenerated as `b76b2792…`, superseding the stale hash previously recorded for that bitmap. Font-file hashes, rather than raster-proof PNG hashes, are now pinned by the canonical host and CI gates.

These expanded v4.5 desktop/Pillow proofs have been inspected directly and are materially more coherent at small and intermediate sizes than the prior pass. The expanded specimens include body copy, all-caps labels, deliberately long metadata, song/artist hierarchy, numerals/timestamps, punctuation, accented text and mixed weights. Android renderer inspection remains mandatory before final type acceptance; the desktop proof is necessary evidence, not a substitute for device rendering.
