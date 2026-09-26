# TSUNAMI UI Genesis — research and design rationale

## Scope and method

The production TSUNAMI interface was treated as an inventory, not a precedent. Inspection was deliberately limited to user-facing capability names and state/workflow obligations: home/resume, owned library objects, catalogue search, playback, queue, lyrics, visualizer, output routing, downloads/offline, longform progress/bookmarks, provider connection/import, signal/quality, library health/diagnostics, appearance/playback/privacy settings, onboarding, and platform integrations. No production screen composition, spacing, navigation, colors, component shape, or density was adopted as a design reference.

The design phase combined current Android platform guidance, accessibility standards, established HCI heuristics, Media3's playback/session model, typographic engineering guidance, and deliberately non-streaming references: transit wayfinding, camera status displays, synthesizer signal flow, mixing-console transport strips, library catalogues, editorial indexes, and e-reader progress systems. The point of those references is not visual quotation; it is to recover strong ideas that streaming software often suppresses—stable landmarks, legible hierarchy, persistent state, compact command surfaces, and explicit provenance.

## Research findings that materially changed the system

### Recognition, recovery and stable landmarks

Recognition is cheaper than recall. A listener who returns after an interruption should not have to reconstruct where playback lives, what is queued, or how to get back to the object they were browsing. Consequently, TSUNAMI keeps a stable listening spine visible across primary workspaces instead of letting playback disappear into a destination-specific mini-player. Back navigation reverses spatial expansion first, then hierarchy, then primary destination; it never silently changes the playback context.

The app also distinguishes four cognitive tasks that conventional “Home” pages tend to conflate: **resume**, **choose**, **find**, and **manage**. Resume is temporal and specific; choosing is library exploration; finding is search; managing is organization/settings. They should not compete in a single shelf stack.

Music research reinforces that familiarity and current listening context are materially different inputs, not interchangeable “recommendation” signals. Familiar music has repeatedly shown different affective/reward correlates from unfamiliar music, while contemporary production recommendation research explicitly conditions ranking on the listener’s present context and recent action sequence. Genesis therefore keeps resumptive/familiar listening, deliberate library choice and catalogue discovery as separate interaction modes rather than collapsing them into one recommendation feed.

### Library versus catalogue

An owned library has memory, provenance and organization; a catalogue is a possibility space. Search results therefore expose provenance explicitly and library browsing defaults to possession-centric metadata (download state, folder, play history, duration, quality where truthful). Catalogue objects are not visually allowed to impersonate owned objects. This avoids a recurrent ambiguity in mixed local/streaming products: “is this mine, cached, merely searchable, or unavailable offline?”

### Playback as persistent context, not a page

Media3 models transport, queue, seek position, shuffle/repeat and external-session control as persistent playback state rather than screen-local state. The shell mirrors that conceptual model. Now Playing is an expanded **listening environment** grown from the persistent spine, not a detached hero screen. Queue, lyrics and output are adjacent modes of the same object. Scrubbing is a time ruler with large hit geometry, not a hairline decoration.

### Mobile reach and control placement

High-frequency transport and destination changes remain in the lower reach zone on compact phones; low-frequency diagnostic and organizational controls are not forced there. Large screens do not merely add margin: they expose parallelism—index/navigation on the left, active workspace in the center, listening context on the right when width permits.

Current Android navigation guidance explicitly cautions against carrying the same bottom navigation pattern onto large windows and recommends a rail where hand placement and spacing make it more ergonomic. That supports the Genesis topology change: compact windows use the low strip, medium windows move the stable destinations into a side rail, and expanded windows add the persistent listening context as a third pane. The navigation model is stable; only its spatial expression changes.

### Accessibility as geometry, not a retrofit

Android recommends at least 48 × 48 dp focusable touch targets for touch interfaces and 4.5:1 contrast for small text (3:1 for large text/graphics). TSUNAMI therefore decouples visible glyph size from hit geometry: terse transport marks may be visually small while their focusable area remains at least 48 dp. Selection is never color-only; it also changes rule weight, label weight, or state text. The shell supports reduced motion, light/dark themes, large-font survival, semantic roles, and strong visible focus/selection states.

WCAG 2.2’s dragging criterion is also useful beyond the web: functionality that depends on dragging should have a non-drag path when dragging is not essential. The listening time ruler consequently accepts both direct taps and dragging, exposes adjustable progress semantics to accessibility services, and never makes a precision drag the sole way to seek. Likewise, keyboard/D-pad focus is made visibly structural on navigation, settings, object ledgers, queue rows, lyrics, output routing, onboarding choices and search-intent rows rather than relying on an invisible platform focus state.

### Responsive behavior

The implementation keys layout to the app window, not the nominal device. Compact, medium and expanded presentations are structural variants. At expanded width the persistent listening spine becomes a dedicated context pane rather than an enlarged bottom bar. State is shared across width transitions, so rotation, split-screen, folding or resizing changes the composition without changing what the user was doing.

Android’s current window-size guidance treats width and height independently: medium width begins at 600 dp, expanded width at 840 dp, while a landscape phone can be medium-width but still compact-height below 480 dp. Genesis therefore does not blindly trigger a multi-pane layout from width alone; medium and expanded arrangements are height-gated so a short landscape window does not become an unusable three-pane composition. This is also why the verification matrix includes compact portrait, compact landscape, medium-window and expanded-window captures rather than a single “phone vs tablet” split.

### Typography

The supplied reference suggests a geometric grotesk with near-circular forms, open lowercase rhythm and disciplined display capitals. Literal geometry is not enough: screen type requires optical overshoot, aperture preservation, weight-specific counter correction and unmistakable ambiguous pairs. TSUNAMI Sans v4.8 therefore uses a shared geometric grammar without merely stroke-expanding one skeleton. Five masters are generated with separate stem targets; circular bowls and flat terminals establish the family resemblance, while letters whose legibility depends on aperture or direction—especially `S/s`, `C/G`, `e`, `a`, and the `I/l/1` and `O/0` pairs—receive explicit constructions rather than generic fallback geometry.

The v4.8 proof pass specifically corrected legibility failures exposed by UI-size specimens rather than by font compilation alone. The earlier lowercase `e` opened so aggressively that it drifted toward epsilon/theta at 12–18 px; the current form preserves almost the entire circular bowl, opens only the middle-right aperture, and uses an explicit crossbar. The single-storey `a` now carries its right terminal through the full x-height so the bowl does not read as a detached circle-and-stem construction. `O/0` are no longer geometrically interchangeable: zero carries a restrained internal diagonal. The proof set includes display alphabets and 12/14/16/18/22/34 px UI samples, long metadata, control pairs, Western-European accents, punctuation and mixed-weight hierarchy.

The OpenType optical-size (`opsz`) model is relevant even though the prototype uses static masters: display and text use different density/weight decisions instead of assuming one outline is ideal at every size. Light is reserved for large quiet text; Regular/Medium carry body and metadata; Semibold/Bold carry navigation, transport state and compact numerals. The masters carry an explicit 500-unit x-height and 710-unit cap-height, TSNM vendor identity, a small screen-oriented GPOS kerning set for high-impact pairs (AV/AW/AY, To/Te/Ta, Yo/Ye and related pairs), and explicit Western-European/symbol coverage rather than fallback blobs.

The current v4.8 constructions preserve open heavy-weight `C/G` apertures; use explicit `a/e/f/t/g` drawings instead of generic circular fallbacks; shape `2/3/5/6/9` with continuous optical curves; and recompose `æ/œ` from the family’s own lowercase grammar. Weight stems are 42/68/86/102/120 construction units across Light→Bold, while side bearings are deliberately tighter than the earlier exploratory masters so 12–18 px UI copy reads as text rather than artificially tracked display lettering. The verification gate regenerates all five masters, checks the 300/400/500/600/700 weight metadata, optical metadata, kerning table and required UI character map, binds the outputs to the canonical v4.8 hash manifest, verifies the specimen proof hashes, and only then proceeds to the Android build.


## Mark reconstruction

The supplied mark was measured from the actual raster reference rather than redrawn from the verbal description. Connected-component and row-boundary analysis shows a 990 × 408 px arch and a roughly 576 × 572 px body. More importantly, the arch is a clipped **near-circular annulus**, not an elliptical half-ring: the outer boundary fits a circle whose centre sits below the flat terminal cut, while the inner counter has a slightly raised centre, making the crown optically thinner than the terminals. Normalized to a 1000-unit arch width, the master uses an outer radius of 509.61, an inner radius of 394.61, a terminal cut at y=411.11, and a 289-unit circular body centered at y=531. A normalized raster comparison improved binary overlap against the supplied reference from approximately 0.932 for the earlier elliptical construction to approximately 0.983 for the measured circular reconstruction. The mark remains bilaterally symmetric even where the source raster contains antialiasing asymmetry. For launcher use the master geometry is not redrawn: it is scaled uniformly to 70 × 57.4 units inside the 108 × 108 adaptive-icon viewport, leaving approximately 19 units horizontal and 25 units vertical clear space. The launcher ground is the product neutral rather than an enclosing brand shape, so Android mask geometry—not TSUNAMI—defines the outer silhouette. The application label remains exactly **TSUNAMI**; “UI Genesis” is development nomenclature, not product naming.

## Three structural concepts explored

### Concept A — Instrument Rail

**Navigation:** a permanent edge rail with mode labels; compact phones fold the rail into a lower horizontal index.  
**Playback:** a continuous transport strip physically intersects every primary workspace.  
**Spatial metaphor:** an instrument panel—stable controls surrounding replaceable content.  
**Strengths:** extremely stable landmarks, excellent reach, strong product identity without artwork.  
**Weaknesses:** risks feeling overly technical; on small phones a literal rail consumes precious horizontal space.

### Concept B — Layered Score

**Navigation:** primary spaces are stacked planes; the active object expands forward while the prior plane remains partially legible behind it.  
**Playback:** the listening layer sits closest to the user and can be pulled forward from any plane.  
**Spatial metaphor:** sheets in a musical score, with persistent position and chronological motion.  
**Strengths:** expressive topology; back navigation is visually self-explanatory; elegant object expansion.  
**Weaknesses:** too animation-dependent, fragile under reduced-motion settings, and visually costly for dense libraries.

### Concept C — Object Ledger

**Navigation:** a typographic index of object classes and saved lenses; no conventional “Home.”  
**Playback:** current playback is a ledger row that expands in place into queue/lyrics/output.  
**Spatial metaphor:** an editorial catalogue or library finding aid.  
**Strengths:** outstanding at 4,000–40,000-track scale; artwork-independent; naturally dense and scannable.  
**Weaknesses:** pure ledger treatment can make casual resumption feel austere and under-emphasize active listening.

## Selected synthesis — Index + Listening Spine

The shell synthesizes A and C, borrowing only the spatial continuity of B.

1. **The Index** is the stable navigation/wayfinding system. Primary modes are text-first: LISTEN, LIBRARY, FIND, SIGNAL. The selection is marked by a rule and weight change, not a pill or filled card.
2. **The Listening Spine** is persistent playback state. On compact windows it occupies the lower band and incorporates transport plus the current object's identity. On expanded windows it becomes a right-side listening context pane. Expanding it produces the Now Playing environment.
3. **The workspace** is a continuous field, not a nest of cards. Boundaries are expressed with rules, typographic rhythm and whitespace. Rounded rectangles are used only when a real object or clipping boundary exists, such as artwork or a modal chooser.
4. **Depth is object-centric.** A track, album, artist, playlist, folder or longform item expands from the row/object the user selected; navigation does not gratuitously relocate the user to a disconnected destination.
5. **Provenance is first-class.** Owned, downloaded, catalogue-only, disconnected and unavailable are explicit textual/state distinctions.

## Information architecture

### Permanent visibility

- active primary destination
- current playback object when one exists
- play/pause state
- coarse position/progress
- a reliable path to expand the listening environment

### Contextual visibility

- shuffle/repeat, sleep timer, output route
- download/offline state
- library provenance and selected filters
- longform chapter/bookmark data
- search result provenance

### Progressive disclosure

- queue editing and reorder commands
- fidelity/path detail
- provider import detail
- library health/repair detail
- advanced playback and diagnostic controls

### Dedicated environments

- Library: ownership/organization at scale
- Find: query, intent, provenance and result navigation
- Signal: truthful technical/collection health and history
- Settings: intent-oriented configuration
- Expanded Listening: playback, queue, lyrics, output and longform context

## Home/start rationale

There is no storefront “Home.” **LISTEN** is a resumptive workspace. It answers, in order: “what was I doing?”, “what can I continue?”, and “what deserves attention from my own collection?” It uses a temporal/indexed ledger rather than recommendation shelves. Discovery can exist, but connected-catalogue exploration belongs in FIND where its provenance is explicit.

## Now Playing rationale

The expanded player preserves the same typographic/rule system as Library. Artwork is subordinate to metadata and time. A time ruler is the principal spatial axis; transport stays one-handed on compact phones. Queue, Lyrics and Output are text-addressable modes aligned to the same playback object, not separate icon-only pages. Longform remains one architectural family while the media model changes its secondary controls: audiobooks emphasize chapter, remaining time, persistent resume and bookmarks; podcasts emphasize episodic identity, ±30-second recovery and explicit played/unplayed state. The distinction is semantic rather than a pair of unrelated player skins.

## Search rationale

FIND is useful before typing by exposing recent intents and type scopes, not recommendation cards. During typing, results are grouped by semantic type and provenance; immediate play and object navigation remain distinct actions. Local/owned results precede connected catalogue results when both match. No result is visually presented as downloaded unless the mock state says so.

## Library scale rationale

At 40 tracks, generous rows are comfortable. At 4,000 and 40,000 tracks, the same data model changes density and adds fast alphabetical/index movement rather than introducing a new metaphor. Sorting, type filters, offline filtering and multi-select are visible as text commands. Dense mode exposes duration/year/quality/provenance in aligned columns on sufficiently wide windows.

## Settings rationale

Settings are organized around listener intent—Appearance, Library, Playback, Offline, Services, Privacy, Advanced—not engineering packages. Technical controls are progressively disclosed beneath Advanced or Signal. Each state is legible as text (`ON`, `OFF`, `CONNECTED`, `LOCAL ONLY`) in addition to any color/geometry.

## Legacy customization triage

Production capability inspection also surfaced presentation controls whose purpose was chiefly to reskin the inherited interface: arbitrary accent hue/saturation/brightness, artwork-derived highlighting, global artwork roundness/scale, card opacity, fixed grid-column counts, app-local font scaling and an animation-speed scalar. These were inventoried, then deliberately **not** carried forward as independent Genesis capabilities. They would make a supposedly authored system depend on user-applied styling parameters rather than on stable hierarchy and task structure.

The underlying user needs survive in less capricious forms: light/dark and high-contrast palettes; 48/56 dp control geometry; comfortable/dense library rhythm; explicit artwork visibility; window-responsive topology; Android font-scale survival at 150% and 200%; one-handed player arrangement; and reduced motion. In other words, Genesis preserves accessibility and control while declining to preserve legacy theming debt.

## Color system

Color is subordinate to hierarchy. Warm neutral surfaces and near-black text provide the structural field. Cobalt marks current/interactive state; ochre marks possession/download transitions; red is reserved for faults/destructive outcomes. Playback state is never communicated by hue alone. Both light and dark modes preserve the same luminance hierarchy and rule structure.

## External playback surfaces

Playback controls do not cease to be part of the product merely because Android renders them outside the main activity. Notification actions, Quick Settings transport, home-screen widgets and Wear controls therefore share the same action vocabulary as the Listening Spine rather than inventing parallel semantics. The shell represents their **configuration contract**—including authored action limits, widget density and Wear secondary action—without registering real services, tiles, widgets or a Wear data layer. This keeps the experiential prototype backend-free while still forcing the product architecture to account for the places where listening is actually resumed and controlled.

The hierarchy is deliberately asymmetric. Play/pause remains indispensable; previous/next are transport; favourite/queue/output are contextual. Quick Settings is constrained to two actions, notification transport to five, and the widget/Wear surfaces expose density or secondary-action choices rather than an unrestricted icon buffet. That limitation is a usability decision, not an implementation shortcut: transient/glanceable surfaces become less intelligible as controls proliferate.

## Motion system

Motion answers topology: an object expands from its origin, the listening spine grows into the listening environment, and mode changes slide along the same axis. Reduced motion substitutes immediate state changes plus rule/opacity changes. There are no elastic bounces, decorative parallax or arbitrary scale pops.

## TSUNAMI Sans construction summary

- Units per em: 1000
- Cap height: 710
- x-height: 500
- Ascender: 800
- Descender: -220
- Overshoot: curve-specific optical compensation rather than one global scalar
- Weights: Light 300, Regular 400, Medium 500, Semibold 600, Bold 700
- Primary control glyphs: `H O n o`
- Near-circular construction with curve-specific overshoot; apertures/counters and actual advance widths are optically corrected per weight
- Flat/clean terminals; no faux-futurist cuts or stencil gaps
- Distinct `I / l / 1`; zero carries a diagonal interior mark so it cannot collapse into capital O at diagnostic/numeric sizes
- Single-storey `a` and `g` follow the supplied geometric direction; tails/stems are tuned for word-shape readability
- Coverage: A–Z, a–z, 0–9, UI punctuation, brackets/braces, mathematical basics (including × and ÷), $, €, £, ¥, quotation marks, Western European accented Latin, Ñ/ñ, Æ/æ, Œ/œ, Ø/ø, Ð/ð, Þ/þ and ß

## Accessibility verification criteria

- Every custom tappable primitive has a minimum 48 dp hit target.
- Small text targets at least 4.5:1 foreground/background contrast; large text and non-text essential graphics target at least 3:1.
- State is redundant: color + rule/weight/text.
- Dynamic/large font layouts wrap or reflow instead of clipping fixed-height containers.
- Reduced motion disables spatial interpolation that is not essential to understanding.
- All meaningful controls expose semantic roles and labels; decorative geometry is excluded from accessibility traversal.
- Back returns through expanded listening/object depth before leaving a primary destination.

## Android build-stack rationale

The shell deliberately follows the Android Gradle Plugin 9 built-in Kotlin model instead of carrying forward the pre-AGP-9 `kotlin-android` plugin. Android's migration guidance states that AGP 9 enables Kotlin support by default and that applying `org.jetbrains.kotlin.android` alongside it is incompatible; the isolated shell therefore applies only `com.android.application` plus the Compose compiler plugin. AGP 9.2's documented compatibility line is Gradle 9.4.1, JDK 17, Build Tools 36.0.0 and Kotlin/KGP 2.2.10, which is the exact toolchain contract encoded by the shell gate. Compose UI/Foundation/Animation/Runtime 1.11.4 is a stable July 2026 release, keeping this prototype on API 36 rather than needlessly adopting the API-37 requirement of the subsequent Compose generation.

Sources:
- Android Developers, **Migrate to built-in Kotlin** — https://developer.android.com/build/migrate-to-built-in-kotlin
- Android Developers, **Android Gradle plugin 9.2 release notes** — https://developer.android.com/build/releases/agp-9-2-0-release-notes
- Android Developers, **Set up the Compose Compiler Gradle plugin** — https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler
- Android Developers, **Compose UI release notes** — https://developer.android.com/jetpack/androidx/releases/compose-ui

## Reference set

Authoritative/current references consulted during the genesis pass:

- Android Developers, **Make apps more accessible** — https://developer.android.com/guide/topics/ui/accessibility/apps
- Android Developers, **Core app quality guidelines** — https://developer.android.com/develop/adaptive-apps/quality-guidelines/core-app-quality
- Android Developers, **Adaptive layouts** — https://developer.android.com/codelabs/add-adaptive-layouts
- Android Developers, **Layouts and navigation patterns** — https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns
- Android Developers, **Use window size classes** — https://developer.android.com/develop/adaptive-apps/guides/use-window-size-classes
- Android Developers, **Accessibility API defaults in Compose** — https://developer.android.com/develop/ui/compose/accessibility/api-defaults
- Android Developers, **Predictive back in Compose** — https://developer.android.com/develop/ui/compose/system/predictive-back
- Android Developers / Media3, **The Player interface** — https://developer.android.com/media/media3/session/player
- Android Developers / Media3, **Control and advertise playback using a MediaSession** — https://developer.android.com/media/media3/session/control-playback
- Nielsen Norman Group, **10 Usability Heuristics for User Interface Design** — https://www.nngroup.com/articles/ten-usability-heuristics/
- W3C WAI, **WCAG 2.2 — Dragging Movements and Target Size** — https://www.w3.org/TR/wcag/
- Google Research, **Transformers in music recommendation** — https://research.google/blog/transformers-in-music-recommendation/
- Pereira et al., **Music and Emotions in the Brain: Familiarity Matters** — https://pmc.ncbi.nlm.nih.gov/articles/PMC3217963/
- Microsoft Typography, **OpenType optical size (`opsz`) axis** — https://learn.microsoft.com/en-us/typography/opentype/otspec182/dvaraxistag_opsz
- Apple Human Interface Guidelines, **Typography** — https://developer.apple.com/design/human-interface-guidelines/typography
