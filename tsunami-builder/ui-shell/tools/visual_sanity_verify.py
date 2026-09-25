#!/usr/bin/env python3
"""Image-level sanity checks for the TSUNAMI Genesis visual-verification matrix.

This does not pretend to replace human visual review. It prevents a deceptively green capture step
from accepting blank, truncated, duplicate-size-zero, or missing mono/squint evidence.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageStat, ImageChops, ImageFilter
import hashlib

ROOT=Path(__file__).resolve().parents[1]/"build/verification"
EXPECTED={
    "01-listen-light","02-library-no-artwork","03-find-light","04-signal-error",
    "05-player-missing-lyrics","06-player-longform","36-player-podcast","07-settings-dark","08-onboarding-light",
    "09-player-dark-queue","10-player-lyrics","11-player-output","12-player-visual",
    "13-listen-empty","14-listen-loading","15-library-40","16-library-4k","17-library-40k",
    "18-library-font-150","19-library-font-200","20-listen-accessibility","21-library-landscape",
    "22-library-medium","23-player-medium","24-listen-expanded","25-library-expanded",
    "26-player-expanded","27-listen-buffering","28-library-unavailable","29-find-partial",
    "30-settings-audio","31-settings-controls","37-settings-external-controls","32-settings-backup","35-settings-services",
    "33-listen-no-artwork","34-player-no-artwork",
    "38-find-empty","39-find-error","40-player-queue-empty",
    "41-settings-provider-connecting","42-settings-provider-error",
    "43-settings-downloads-active","44-settings-downloads-error",
}

def fail(message:str)->None:
    raise SystemExit("VISUAL_SANITY_FAIL: "+message)

base={p.stem:p for p in ROOT.glob("*.png") if "-mono" not in p.stem and "-squint" not in p.stem and p.stem!="contact-sheet"}
missing=sorted(EXPECTED-set(base))
if missing: fail("missing base states: "+", ".join(missing))
if len(base)!=len(EXPECTED): fail(f"unexpected base capture count {len(base)} != {len(EXPECTED)}")

hashes={}
orientations=set()
for name,path in sorted(base.items()):
    im=Image.open(path).convert("L")
    w,h=im.size
    if w<300 or h<300: fail(f"{name} implausibly small dimensions {w}x{h}")
    orientations.add("landscape" if w>h else "portrait")
    stat=ImageStat.Stat(im)
    if stat.extrema[0][1]-stat.extrema[0][0] < 45:
        fail(f"{name} lacks luminance range")
    if stat.stddev[0] < 12:
        fail(f"{name} is suspiciously flat/blank (stddev={stat.stddev[0]:.2f})")
    hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for suffix in ("-mono.png","-squint.png"):
        derived=ROOT/(name+suffix)
        if not derived.is_file() or derived.stat().st_size<5000:
            fail(f"{name} missing usable {suffix[1:]} derivative")

if orientations!={"portrait","landscape"}:
    fail(f"verification lacks both portrait and landscape evidence: {sorted(orientations)}")

# State captures should not all accidentally be the same launch screen.
if len(set(hashes.values())) < 20:
    fail(f"insufficiently distinct base captures: {len(set(hashes.values()))} unique / {len(hashes)}")

# Critical topology/state pairs must differ individually. A global unique-count floor can still
# conceal a broken launch extra if, for example, Queue/Lyrics both capture the same player mode.
DISTINCT_GROUPS=(
    ("09-player-dark-queue","10-player-lyrics","11-player-output","12-player-visual"),
    ("01-listen-light","13-listen-empty","14-listen-loading","27-listen-buffering"),
    ("15-library-40","16-library-4k","17-library-40k"),
    ("21-library-landscape","22-library-medium","25-library-expanded"),
    ("30-settings-audio","31-settings-controls","37-settings-external-controls","32-settings-backup","35-settings-services"),
    ("03-find-light","38-find-empty","39-find-error"),
    ("41-settings-provider-connecting","42-settings-provider-error","35-settings-services"),
    ("07-settings-dark","43-settings-downloads-active","44-settings-downloads-error"),
)
for group in DISTINCT_GROUPS:
    group_hashes=[hashes[name] for name in group]
    if len(set(group_hashes)) != len(group_hashes):
        fail("critical captures collapsed to duplicates: "+", ".join(group))

# The monochrome derivative must truly discard hue, and the squint derivative must be perceptibly
# smoother than its monochrome source. These are evidence-generation checks, not aesthetic scores.
def edge_energy(image:Image.Image)->float:
    gray=image.convert("L")
    edges=gray.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).mean[0])

for name,path in sorted(base.items()):
    mono=Image.open(ROOT/(name+"-mono.png")).convert("RGB")
    extrema=ImageChops.difference(mono.getchannel("R"),mono.getchannel("G")).getextrema()
    extrema2=ImageChops.difference(mono.getchannel("G"),mono.getchannel("B")).getextrema()
    if extrema[1] != 0 or extrema2[1] != 0:
        fail(f"{name} monochrome derivative retains channel differences")
    squint=Image.open(ROOT/(name+"-squint.png")).convert("RGB")
    mono_energy=edge_energy(mono)
    squint_energy=edge_energy(squint)
    if mono_energy > 1.0 and squint_energy >= mono_energy*0.92:
        fail(f"{name} squint derivative is not materially blurred ({squint_energy:.2f} >= {mono_energy:.2f})")
    squint_gray=squint.convert("L")
    squint_stat=ImageStat.Stat(squint_gray)
    squint_range=squint_stat.extrema[0][1]-squint_stat.extrema[0][0]
    if squint_range < 24 or squint_stat.stddev[0] < 6:
        fail(f"{name} loses large-scale hierarchy under squint review (range={squint_range}, stddev={squint_stat.stddev[0]:.2f})")

# The artwork-removal scenarios intentionally change content while preserving the product's spatial
# identity. Compare blurred/monochrome structure so this check is insensitive to tiny glyph/raster
# differences but still catches an interface whose composition collapses when artwork disappears.
def mean_abs_difference(a:Image.Image,b:Image.Image)->float:
    if a.size != b.size:
        fail(f"artwork identity pair dimension mismatch: {a.size} vs {b.size}")
    return float(ImageStat.Stat(ImageChops.difference(a.convert("L"),b.convert("L"))).mean[0])

ARTWORK_IDENTITY_PAIRS=(
    ("01-listen-light","33-listen-no-artwork"),
    ("09-player-dark-queue","34-player-no-artwork"),
)
for with_art,no_art in ARTWORK_IDENTITY_PAIRS:
    a=Image.open(ROOT/(with_art+"-squint.png")).convert("RGB")
    b=Image.open(ROOT/(no_art+"-squint.png")).convert("RGB")
    delta=mean_abs_difference(a,b)
    if delta < 0.35:
        fail(f"{with_art}/{no_art} are effectively identical; no-artwork scenario may not be applied")
    if delta > 46:
        fail(f"{with_art}/{no_art} diverge too much without artwork (mean delta={delta:.2f}); artwork is carrying product identity")
    ea=edge_energy(a); eb=edge_energy(b)
    ratio=(eb/ea) if ea>0.5 else 1.0
    if ratio < 0.55 or ratio > 1.75:
        fail(f"{with_art}/{no_art} hierarchy changes excessively without artwork (edge ratio={ratio:.2f})")

sheet=ROOT/"contact-sheet.png"
if not sheet.is_file() or sheet.stat().st_size<20_000:
    fail("contact sheet missing or implausibly small")

print(f"VISUAL_SANITY=PASS states={len(base)} unique={len(set(hashes.values()))} orientations={','.join(sorted(orientations))} critical_groups=distinct mono=verified squint=verified hierarchy=verified artwork_identity=verified")
