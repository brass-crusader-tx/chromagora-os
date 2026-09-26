# TSUNAMI Sans — visual review log

## 2026-09-26 · v5.1 current source

The checked-in generator is now **TSUNAMI Sans v5.1**. This pass is a construction revision, not a metadata bump. The exact branch generator was reconstructed byte-for-byte from Git blob `40647ffaebca8de8e8b24baddd4346cfb79166e2`, executed twice with FontTools 4.63.0 / Shapely 2.1.2 / Pillow 12.3.0, and both executions emitted byte-identical masters and proofs. The resulting proof sheets were inspected directly before the canonical manifest was advanced.

The v5.1 revision specifically addresses the remaining UI-scale weaknesses in the prior proof: `S/s` uses a smoother asymmetric double-curve rather than two near-circular lobes; lowercase `e` retains more bowl while carrying a full-weight horizontal bar; `g` has a simpler descender hook; `r` has a shorter shoulder; `t` regains a restrained geometric foot so its baseline silhouette does not collapse into `l`; zero retains a subtler diagonal distinction from capital O; and side bearings are slightly widened to recover word rhythm as workhorse weights become firmer.

Current canonical generator facts:

- family: **TSUNAMI Sans**
- version metadata: **Version 5.100**
- masters: Light 300 / Regular 400 / Medium 500 / Semibold 600 / Bold 700
- construction stem targets: 44 / 70 / 90 / 108 / 128
- cap height / x-height: 710 / 500 with explicit overshoot
- fixed OpenType timestamp for deterministic binaries
- 176 glyphs per master with Western-European and operational-symbol coverage
- GPOS kerning
- ambiguity checks for I/l/1, O/0, rn/m, c/e and v/y
- Android/build gates regenerate the family and reject metadata, coverage, kerning, hash, byte-size or proof drift

### Canonical v5.1 master hashes

| Master | Weight | Bytes | SHA-256 |
|---|---:|---:|---|
| Light | 300 | 103600 | `43980be643894110df96e021df0ed18d71317e0877a8e5d4efd9d190c3a4979a` |
| Regular | 400 | 106172 | `995c2ee2799203e4a30ce1f2b2cb300b6f5838595f02765aa8890ff7f4adc0f9` |
| Medium | 500 | 107168 | `75e5b6b9703ef5395b534256cd494e2fa59b2e25f824ebee7dbd8af5a8cd5ac6` |
| Semibold | 600 | 107784 | `a5f2f2ce832a436daf9f984b97df90f181bea4bf6b6d47001edd4df9b8a561b6` |
| Bold | 700 | 107200 | `1fd9d193b12672d17267dea686eca88e2e490c2c949d74bf9f75a04c463b3f67` |

The proof artifacts are likewise pinned:
- `tsunami-sans-proof.png` — 164201 bytes, SHA-256 `99b9cd461eaeb1518afb4eaa63e8e9913c052d07de99dfa6527ed61e686cb789`
- `tsunami-sans-ui-proof.png` — 74390 bytes, SHA-256 `31ebdae4e3fe5228e070c43af148bb9cf6a2cdce76ca759ac511eccd10d91c4c`

The canonical contract is now `docs/TSUNAMI-SANS-v5.1-MANIFEST.json`. `tools/ui_shell_gate.py`, `ui-shell/tools/source_verify.py`, and `ui-shell/tools/build_host.sh` bind to that single manifest rather than duplicating hash tables.

The desktop/Pillow proof is materially useful because it exposes construction and UI-scale raster defects; it is not the final renderer. **Final type acceptance still requires v5.1 to render in the exact-current-head Android shell and survive the mandatory device screenshots, large-font states, no-artwork state, monochrome review and human visual pass.**

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
