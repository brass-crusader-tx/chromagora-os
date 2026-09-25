# TSUNAMI UI Genesis — visual review protocol

This is the mandatory human review pass for the generated verification matrix. The automated image sanity gate proves that captures exist, are non-blank, vary across states, and have the expected derivatives; it additionally verifies that blurred monochrome states retain large-scale luminance hierarchy and that matched artwork/no-artwork states remain structurally similar rather than collapsing around content imagery. It does **not** certify aesthetic quality.

## Review set

The canonical capture matrix contains 44 base screenshots plus monochrome and blurred “squint”
derivatives. Review the contact sheet first, then the full-resolution images.

### Product topology

- `01-listen-light`: LISTEN reads as a resumptive workspace, not a streaming storefront.
- `03-find-light`: FIND is useful before typing and provenance/scope controls remain legible.
- `16-library-4k`, `17-library-40k`, `15-library-40`: one library grammar survives all three scales.
- `21-library-landscape`, `22-library-medium`, `24-listen-expanded`: compact, medium and expanded
  compositions change topology rather than merely widening margins.
- `09-player-dark-queue`, `10-player-lyrics`, `11-player-output`, `12-player-visual`: Expanded
  Listening remains one coherent environment across modes.
- `06-player-longform` and `36-player-podcast`: the same listening architecture adapts semantically—chapter/bookmark affordances for audiobooks, skip/played-state affordances for podcasts—without becoming two unrelated players.
- `31-settings-controls` and `37-settings-external-controls`: in-app gesture/headset customization and off-app notification/Quick Settings/widget/Wear contracts remain distinct progressive settings depths rather than a single overloaded control dashboard.
- `30-settings-audio`, `31-settings-controls`, `32-settings-backup`, `35-settings-services`: progressive settings retain
  the same typographic/rule grammar instead of falling back to stock settings rows.

### Required adversarial tests

**Remove the artwork:** inspect `02-library-no-artwork`, `33-listen-no-artwork` and `34-player-no-artwork`. Content slots must be deliberately neutral across browsing and active listening; the screen should still be recognizably TSUNAMI from type, rules, spacing, index behavior and state geometry. The image gate also compares the blurred `01↔33` and `09↔34` pairs, rejecting either an unchanged scenario or an excessive whole-screen structural divergence.

**Remove the color:** inspect every `*-mono.png` derivative, especially LISTEN, LIBRARY, FIND,
Expanded Listening and Settings. Selection/hierarchy must remain readable by weight, rules, position
and text—not hue alone.

**Squint:** inspect every `*-squint.png` derivative and the contact sheet. Primary navigation,
listening context, workspace body and high-priority transport should remain distinct masses.

**Not Spotify:** cover the launcher mark/name mentally and inspect LISTEN, LIBRARY and Expanded
Listening. Reject any pass that has regressed into greeting + shelves, a five-icon tab clone, or a
hero-art + slider + five-round-buttons composition.

**No designer explanation:** every primary command exposed in the matrix must be inferable from its
label/state and location without consulting the research rationale.

### Type and accessibility

- Compare `18-library-font-150` and `19-library-font-200` for clipping, overlap and lost commands.
- Inspect `20-listen-accessibility` for 56 dp controls, high-contrast state and hierarchy without color
  dependence.
- Compare the Android captures with `tsunami-sans-proof.png` and `tsunami-sans-ui-proof.png`.
  Flag malformed counters, ambiguous I/l/1 or O/0, bad punctuation, uneven color, or weight-specific
  spacing failures.
- Inspect `06-player-longform` and the long-title fixture for wrapping, chapter hierarchy, timestamps
  and resume context.
- Inspect disabled/unavailable and adverse states: `04-signal-error`, `27-listen-buffering`, `28-library-unavailable`, `29-find-partial`, `38-find-empty`, `39-find-error`, `40-player-queue-empty`, `41-settings-provider-connecting`, `42-settings-provider-error`, `43-settings-downloads-active`, and `44-settings-downloads-error`. Each recovery path must remain legible without displacing the stable navigation/transport grammar.

### De-tackification rejection criteria

Reject and revise if the screenshots show gratuitous pills/cards, decorative gradients, fake glass,
arbitrary glow/shadows, artwork-derived chrome, giant empty greetings, indiscriminate uppercase
letterspacing, visually equal weight across all regions, or album art doing the work of the design
system.

## Acceptance recording

For the final device pass, record each of the following as PASS or REVISE in the evidence bundle:

1. alignment and baseline rhythm;
2. clipping/overflow;
3. density and scanability;
4. TSUNAMI Sans Android rendering;
5. transport reachability;
6. navigation/back topology;
7. artwork independence;
8. monochrome hierarchy;
9. squint hierarchy;
10. non-streaming-clone architecture;
11. light/dark structural equivalence;
12. large-font survival;
13. missing-art/empty/loading/error/unavailable/partial-source plus empty-search, failed-search, empty-queue, provider-transition, provider-failure, active-download and failed-download states;
14. 40 / 4,008 / 40,008 library behavior;
15. settings-depth coherence, including provider connections/import audit outside the root settings surface.

A successful build is not a visual PASS. Any REVISE item requires another capture after correction.
