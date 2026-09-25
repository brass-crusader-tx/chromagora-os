# TSUNAMI master mark specification

The production mark is the geometric reconstruction used by both `brand/tsunami-mark.svg` and the Compose `TsunamiMark` primitive. The raster reference remains source evidence; it is not embedded into the product.

## Master geometry

The normalized master uses a **1000 × 820** coordinate system.

| Element | Geometry |
|---|---|
| Outer arch circle | center `(500, 509.61)`, radius `509.61` |
| Inner optical counter | center `(500, 502.69)`, radius `394.61` |
| Arch terminal baseline | `y = 411.11` |
| Inner terminal x positions | `116.16 / 883.84` |
| Body circle | center `(500, 531)`, radius `289` |
| Body diameter | `578` |

The arch is therefore not modeled as a naïve constant-width stroked semicircle. Its inner counter is displaced **6.92 units upward** relative to the outer-circle center; this is the optical correction required to preserve the supplied silhouette rather than the mathematics of a perfect concentric annulus.

The left/right terminations are flat on the same baseline. No rounding, flare, taper, gradient or water/wave metaphor is introduced.

## Reference-fit evidence

The supplied 1536 × 1536 raster reference was thresholded at 50% luminance and its two black connected components measured directly:

- arch component: `x=266…1256`, `y=343…751`;
- body component: `x=474…1049`, `y=584…1155`;
- total mark bounding box: **991 × 813 px**.

The current vector was rasterized into that exact 991 × 813 bounding box and compared as a binary mask against the supplied reference. Results:

- intersection-over-union: **0.98399**;
- vector-mask precision: **0.99566**;
- reference-mask recall: **0.98822**;
- symmetric-difference pixels: **6,329**, or **1.61%** of the reference black area.

Residual error is concentrated in antialiased/raster edge noise and the quick reference image's non-ideal boundary pixels; the vector keeps the cleaner analytic geometry.

## Clear space

Let `D = 578`, the body-circle diameter. The default exclusion zone is **D / 4 = 144.5 master units** on all sides of the mark. No text, artwork edge, divider, badge or other high-contrast object should enter that zone when the mark is used as a standalone brand signature.

In constrained navigation/toolbar contexts, the minimum exclusion zone may reduce to **D / 8 = 72.25 units**, provided the mark is the only high-contrast symbol in that local region.

## Scaling and small-size behavior

The mark must always scale **uniformly**. Independent x/y scaling is prohibited.

- **≥ 48 dp:** use the master geometry directly.
- **24–47 dp:** retain the exact geometry; prefer one-color rendering and avoid adjacent hairline rules.
- **16–23 dp:** retain the same geometry, snap the rendered bounds to whole device pixels where the platform permits, and use the highest-contrast monochrome palette role.
- **< 16 dp:** do not use the full mark as a functional icon. Use a textual TSUNAMI label or another task-specific icon instead.

No small-size alternate is allowed to thicken the arch, enlarge the body, close the terminals, or introduce an enclosing badge. The silhouette remains the same mark.

## Color

The mark is monochrome by default:

- dark mark on light ground;
- light mark on dark ground.

Inverse usage is generated from the same geometry. Album-art colors, gradients and decorative brand accents do not recolor the mark automatically.

## Implementation identity

`brand/tsunami-mark.svg` is the canonical vector source. `ui-shell/.../brand/TsunamiMark.kt` reproduces the same normalized circles, terminal baseline and arc angles and centers the result with uniform scaling, preventing caller distortion.
