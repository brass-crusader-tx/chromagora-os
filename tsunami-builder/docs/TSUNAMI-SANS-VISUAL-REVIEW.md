# TSUNAMI Sans — visual review log

## 2026-09-25 · v4.8 current source

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
| Light | 300 | `41c1ba2f9e4cd988b5892e08ae76eab7d2ce40fc00d9a89e7135591ae6822f54` |
| Regular | 400 | `35fc1529ae8d3de472a5531321e1e319d0dd3b6c502e095120f346d950ef71fc` |
| Medium | 500 | `cf4ff17d02dfc3992689d3567defba11e3a1b997fec4e4b97523bc5a59a403a5` |
| Semibold | 600 | `cf142704507b95488dc53c1fa66ad7c62ba4a40dcfd4e228fe67f4fc340f56f1` |
| Bold | 700 | `17d5046a74b5b38a63378093a883cdedcb2b2baee0cc32023411bd79bdac64b4` |

The canonical host and CI gates pin those five font-file hashes. Proof PNGs are intentionally treated as regenerated review artifacts rather than canonical binary source, so this document no longer assigns current v4.8 truth to the older v4.5 bitmap hashes below.

**Acceptance boundary remains unchanged:** desktop/Pillow proofing validates construction and obvious raster defects, but final type acceptance still requires the current v4.8 masters to be rendered by Android on the same current-head shell and inspected at the actual UI sizes. That device-renderer review has not yet executed because the Android runner is still blocked before job allocation.

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

The generator source used for this review was independently reconstructed from the connected repository and verified byte-for-byte with Git blob id `954b6b614e70a18b4d08dc5518725f277e9788dd` before execution. The five TTFs reproduced the canonical hashes above exactly. The main proof also reproduced its recorded hash exactly; the UI-size PNG was regenerated as `b76b2792…`, superseding the stale hash previously recorded for that bitmap. Font-file hashes, rather than raster-proof PNG hashes, are now pinned by the canonical host and CI gates.\n\nThese expanded v4.5 desktop/Pillow proofs have been inspected directly and are materially more coherent at small and intermediate sizes than the prior pass. The expanded specimens include body copy, all-caps labels, deliberately long metadata, song/artist hierarchy, numerals/timestamps, punctuation, accented text and mixed weights. Android renderer inspection remains mandatory before final type acceptance; the desktop proof is necessary evidence, not a substitute for device rendering.
