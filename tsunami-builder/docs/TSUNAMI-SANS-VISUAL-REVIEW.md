# TSUNAMI Sans — visual review log

## 2026-09-26 · v5.1 exact-source legibility refinement

The active Genesis branch remains **TSUNAMI Sans v5.1 / Version 5.100**, but the outlines have received one deliberately narrow refinement after a fresh independent regeneration and full-resolution visual inspection. The exact generator reconstructed from the repository before editing was verified as Git blob `43ae1290ae3063a717cddb0272080dc0c27d3b7f`; the refined generator committed to the branch is Git blob **`ea17b0e4e51e40a6ac9a0a8845ac83b53c620ae2`**.

The new pass addresses three remaining workhorse-glyph problems visible in the current UI-size specimen rather than changing the family wholesale:

- lowercase **f** now has a restrained geometric shoulder and flat baseline instead of the hook that could read as a dagger at small UI sizes;
- lowercase **r** has a smaller, more open shoulder, removing the decorative flourish while preserving differentiation from `n`;
- lowercase **t** loses its curved foot entirely and becomes a plain stem/crossbar construction, restoring the terminal philosophy already stated by the design brief.

The family/version contract, 176-glyph coverage, ambiguity controls, deterministic timestamps, five explicit weight masters, GPOS kerning, Western-European coverage, and restrained `0` diagonal remain unchanged. The canonical manifest—not duplicated prose—is the executable source of truth. A byte-for-byte local execution of the refined generator using the pinned toolchain produced:

| Master | Weight | Bytes | SHA-256 |
|---|---:|---:|---|
| Light | 300 | 103448 | `cc9c5b0ee976bfdb16bf870f81d797b843de25ab9189ec82ee52f424f86815c5` |
| Regular | 400 | 106004 | `bf9ad008744b4ca49cf3c8c0241d5e7ba951c0817592d951313f4555c80dd741` |
| Medium | 500 | 107008 | `10e1797a3dae517c14403474b881311fe48e9c15fb100bc54a33ed417430b9b6` |
| Semibold | 600 | 107588 | `48ce7ce31ddc7094afe5a71c8524c4e40d67304c9f6f5062f7fd57fbd7dd1820` |
| Bold | 700 | 106940 | `fb92d22131ccbf2ff95e3a482e52f9d6c2fe3de6aea41f1d2b73d29fd90f7d12` |

Fresh proof records:
- `tsunami-sans-proof.png` — 162883 bytes, SHA-256 `3ab66015adfa5b5531016d957b30b029dfd5b0510ffd588acf00f6e04c940d86`
- `tsunami-sans-ui-proof.png` — 74005 bytes, SHA-256 `9c39c4b60f74749279f514eeeb8af4b29d038c07ec6a6ecf00f39530b7a1e2d2`

FontTools reopened every generated master: weight classes remain **300 / 400 / 500 / 600 / 700**, each master contains **176 glyphs**, and every master retains GPOS. Direct visual inspection of the regenerated full specimen and 12–34 px UI specimen confirms that the three edited glyphs now sit more quietly inside running text; the family is less calligraphically idiosyncratic without sacrificing its geometric identity.

**Acceptance boundary:** desktop/Pillow proofing is necessary but not sufficient. Final type acceptance still requires the exact-current-head Android shell to render v5.1 in the mandatory device screenshot matrix, including large-font, no-artwork, monochrome and squint states. No prose or manifest record substitutes for that Android raster pass.

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
