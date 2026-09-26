# TSUNAMI mark — master geometry

The supplied 1536 × 1536 raster reference was measured directly rather than interpreted as a generic “semicircle over dot.” At a dark-pixel threshold, the arch occupies approximately **990 × 408 px** (`x=266…1255`, `y=344…751`) and the body approximately **576 × 572 px** (`x=474…1049`, `y=584…1155`). Row-by-row boundary fitting shows that the arch is not an elliptical half-ring: its visible crown is a pair of near-circular arcs clipped by a horizontal terminal line below the crown but above their geometric centres.

The production master normalizes the 990 px arch width to 1000 units while restoring exact bilateral symmetry.

- Master view box: `1000 × 820`
- Symmetry axis: `x = 500`
- Outer arch circle: `r = 509.61`, centre `(500, 509.61)`
- Outer crown: `y = 0`
- Inner optical counter: `r = 394.61`, centre `(500, 502.69)`
- Inner crown: approximately `y = 108.08`
- Flat terminal cut: `y = 411.11`
- Inner terminal positions: `x = 116.16` and `x = 883.84`
- Nominal terminal thickness: `116.16` units
- Crown thickness: approximately `108.08` units
- Circular body: `r = 289`, centre `(500, 531)`
- Body/arch diameter ratio: `0.578`
- Overall black geometry reaches approximately `y = 820`

The roughly seven-unit vertical offset between the inner and outer circle centres is intentional optical correction recovered from the reference: the crown is slightly thinner than the flat terminals. The former SVG used an elliptical outer half-arch (`rx=500, ry=410`) and materially flattened the supplied mark; that construction is superseded.

## Optical rules

The body is a true circle. The arch terminals remain flat horizontal cuts: do not round them. At sizes below 20 px, the terminal/crown weight may be increased by up to 4% and the counter opened by up to 2% if raster closing becomes visible, but the circular crown character and body/arch relationship must remain intact.

Clear space is one quarter of the body diameter (`144.5` master units) on every side. Black-on-light and white-on-dark are the canonical deployments. No enclosing badge, gradient, wave motif, shadow, water imagery, or artwork-derived color belongs to the mark.


## Implementation parity

The SVG at `brand/tsunami-mark.svg` is canonical production geometry. The Android renderer at `ui-shell/app/src/main/java/com/tsunami/shell/brand/TsunamiMark.kt` uses the same normalized circle centers/radii and analytically derived sweep angles; it must not be independently approximated.

The mark always scales uniformly inside its container. A non-1000:820 slot is letterboxed on the short axis rather than stretching the geometry. At 24 dp and above the master is used unchanged. At 16–23 dp, use the same master only where the full silhouette remains legible; below 16 dp prefer a textual/control label rather than inventing a new simplified symbol.

Positive and inverse deployments are the same vector geometry using dark-on-light or light-on-dark. Accent color is not intrinsic to the mark.
