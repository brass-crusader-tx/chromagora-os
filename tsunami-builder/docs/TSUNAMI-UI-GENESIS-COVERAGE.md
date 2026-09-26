# TSUNAMI UI shell — capability coverage matrix

This matrix records where the production application's user-facing capability inventory lives in the genesis shell. It is intentionally a semantic mapping, not a screen-for-screen port.

| Production capability | Genesis home | Mock interaction/state |
|---|---|---|
| Resume / continue listening | LISTEN workspace + persistent Listening Spine | Resume row selects the object; per-item longform positions survive context changes; spine play/pause and expand respond |
| Songs | LIBRARY → Tracks lens | Sort, density, offline filter, multi-select, play, favourite, download, playlist insertion, play-next and shuffle-next; Ledger preserves optional artwork while Index becomes an artwork-free alphabetical typographic ledger; track actions reveal by long-press or overflow |
| Albums | LIBRARY → Albums lens | Ledger object opens a reversible detail depth with album contents; object-level Play/Play next resolve a track from that album rather than an unrelated list position; missing-art state is represented |
| Artists | LIBRARY → Artists lens | Artist grouping opens reversible detail depth with matching tracks and object-level playback resolves inside that artist |
| Playlists | LIBRARY → Playlists lens | Create/open/play/queue-next actions and single- or multi-track insertion mutate shared deterministic playlist state |
| Folders | LIBRARY → Folders lens | Folder objects are derived from the mutable Library-root state, open reversible matching contents and preserve ownership/provenance semantics |
| Favourites | LISTEN temporal index + track state | Favourite toggles immediately and persists in shell state |
| History / recently played | LISTEN + SIGNAL history | Temporal resume rows, local-library listening lenses (Deep cuts / Rediscover / Never heard / Most played / Unfinished) and listening statistics |
| Downloads / offline | LIBRARY filters + listening object state + Settings/Offline | Download cycles local/downloading/downloaded; offline mode toggles |
| Search | FIND workspace | Live query, bounded one-edit/adjacent-transposition typo tolerance, local/catalogue scope, track/album/artist/folder/longform filters, immediate play/object select and reversible object depth |
| Connected catalogue results | FIND | Explicit `CATALOGUE` provenance; never masquerades as owned |
| Connected services | SETTINGS → Connected services | YouTube Music, Apple Music, Amazon Music, Spotify and TIDAL are all represented; dedicated progressive workspace provides connect/disconnect, staged import progress, audit disclosure and retained imported-library state |
| Provider import | SETTINGS → Connected services | Deterministic 25% progress steps, completion audits with explicit Shorts/video-only/sample/unmatched exclusions, and retained imported-library state after disconnect |
| Podcasts | LIBRARY → Longform lens + Expanded Listening | Explicit podcast media type, episodic metadata, ±30-second transport and played/unplayed state |
| Audiobooks | LIBRARY → Longform + Expanded Listening | Explicit audiobook media type, chapter/remaining-time/resume state and bookmark behavior |
| Radio | LIBRARY → Radio lens | Distinct deterministic stations resolve different source sets (owned, connected or favourites), open reversible content depth and expose a stateful play action |
| Now Playing | Expanded Listening environment | Opens from persistent spine; back collapses to prior workspace |
| Play / pause | Listening Spine + Expanded Listening | Immediate toggle |
| Previous / next | Listening Spine / transport dock | Changes current queue item |
| Scrubbing / seeking | Expanded Listening time ruler | Draggable progress state |
| Queue | Expanded Listening → QUEUE mode | Play-next/shuffle-next insertion, remove and move up/down mutate one shared queue |
| Shuffle | Expanded Listening transport | Toggle with textual state redundancy |
| Repeat | Expanded Listening transport | Off → All → One cycle |
| Lyrics | Expanded Listening → LYRICS + SETTINGS → Lyrics & timing | Timed mock lines; follow-playback, word/line timing, global delay, fallback/backdrop and reorderable source-priority state are interactive; missing-lyrics scenario remains explicit |
| Visualizer | Expanded Listening → VISUAL | Deterministic generated bars; reduced-motion safe |
| Output / device routing | Expanded Listening → OUTPUT | This device / headphones / cast mock route selection |
| Sleep timer | Expanded Listening power tools | Off / 15 / 30 / 60 min cycle |
| Bookmark / timestamp | Longform listening mode | Adds/removes mock bookmark at current position |
| Share timestamp | Expanded Listening | Mock confirmation state; no OS/network dependency |
| Signal / audio-path info | SIGNAL → Summary / Audio | Truth-labelled mock source, route, sample-rate/bit-depth, DSP/ReplayGain, integrity counters and gapless-probe state |
| Quality / fidelity info | SIGNAL + Expanded Listening secondary metadata | Explicit source/output fields rather than decorative badges |
| Library health | SIGNAL → Library | Missing/zero-byte/undecodable/orphan counts plus interactive lyrics audit/fetch, SHA-256 duplicate scan, FLAC integrity scan, ReplayGain/local-analysis and format summaries |
| Diagnostics | SIGNAL → Logs | Deterministic logs/status, copy/export/clear actions and simulated fault/recovery state |
| Listening analytics | SIGNAL → History | Mock completion/skip/listening totals, TSUNAMI Replay period/export/share-card actions, time-of-day metrics and library-activity history |
| Appearance | SETTINGS → Appearance / Presentation | Stateful light/dark, high-contrast palette, 48/56dp authored control targets, haptic intensity, density and reduced-motion controls plus artwork visibility/geometry, metadata density, orientation policy and one-handed player state |
| Library roots / profiles | SETTINGS → Library roots / Library profiles | Add/remove mock roots, preserve at least one root, switch active local/offline-first profile; folder, extension, genre and playlist-path exclusions have an explicit progressive-disclosure home |
| Library section customization | SETTINGS → Library sections | Non-anchor lenses can be reordered and hidden; the Library index reflects both immediately while Tracks remains a visible fallback anchor |
| Library alternate views | LIBRARY → Ledger / Index | Ledger preserves artwork-bearing information density; Index becomes a typographic, alphabetically grouped, artwork-free ownership surface with the same play/selection/queue affordances and a fast letter index |
| Metadata presentation | SETTINGS → Metadata presentation | Cycled template changes actual Library-row metadata; album-artist policy and car-display presentation are explicit |
| Playback preferences | SETTINGS → Playback | Stateful gapless and 0/3/6/12-second crossfade controls; longform resume behavior is represented by persisted position |
| Playback speed / pitch | SETTINGS → Playback / Audio processing | Default speed cycles through 1×/1.25×/1.5×/2×; preserve-pitch state is explicit and Signal reflects speed |
| ReplayGain | SETTINGS → Audio processing / SIGNAL | Off/Track/Album cycles; current mock policy is reflected in Signal |
| DSP / audio processing | SETTINGS → Audio processing / 10-band equalizer / SIGNAL | Opt-in bypass, preamp, bass, treble, 10-band EQ, mono and stereo-width mock state; Signal never claims processing when bypassed |
| Shuffle intelligence | SETTINGS → Shuffle behavior + queue transport | Balanced/Discovery/Album-aware modes alter deterministic mock next/queue placement; artist/album/genre/mood spacing, novelty/familiarity, compatible-key, genre-blend, seasonal and saved-preset state are represented |
| Audio preferences | SETTINGS → Playback / SIGNAL | Source/Lossless/Data-saver preference cycles explicitly; output route is stateful in Expanded Listening |
| Visualizer preferences | SETTINGS → Visualizer + Expanded Listening → VISUAL | Mode/sensitivity/monochrome/reduced-motion settings alter deterministic rendered geometry |
| Player controls / gestures | SETTINGS → Controls & gestures | One-handed player, per-view orientation locks, mini-player extras applied to the persistent Listening Spine, full-player actions applied to Expanded Listening, Android-notification action selection, horizontal + vertical track gestures, long-press mapping, and headset mappings are stateful mock controls |
| External playback surfaces | SETTINGS → Controls & gestures | Android notification actions, two-slot Quick Settings transport, home-screen widget layout, Wear transport enablement and Wear secondary action are explicit mock contracts without registering platform services |
| Context-aware queue rules | SETTINGS → Context rules | Enable/disable/add/remove deterministic rules with time-window and queue-scope metadata |
| Quick actions / listening sessions | SETTINGS → Quick actions & sessions | Quick-action list mutates; a Focus session starts/ends without disrupting playback |
| Custom library sections | SETTINGS → Custom library sections | Saved query views can be added/removed as persistent prototype state |
| Smart shelves / saved rules | SETTINGS → Custom library sections | Production smart-shelf intent is represented as named, query-backed persistent library views rather than a legacy shelf UI |
| Output processing profiles | SETTINGS → Output profiles | Route-bound processing profiles can be saved/applied/removed and update the mock output route |
| Advanced transition controls | SETTINGS → Audio processing | Crossfade curve/policy, pause/stop/skip fades, offload/resampling policy, pitch, clipping and longform rewind controls are stateful |
| Advanced DSP capability | SETTINGS → Audio processing | Compressor, limiter, AGC, channel balance, reverse stereo, crossfeed and reverb have explicit mock homes without claiming real signal processing |
| Download preferences | SETTINGS → Offline | Offline mode, Wi-Fi-only policy, mobile-data online visibility and quality preference are stateful |
| Privacy / history controls | SETTINGS → Privacy | Listening-history toggle and clear-history mock confirmation |
| Scrobbling / history import | SETTINGS → Listening services | ListenBrainz/Last.fm toggles, threshold cycling and deterministic history-import preview without credentials/network access |
| Backup / portability | SETTINGS → Backup & portability | Backup/restore, longform-progress import/export, rotating-backup policy, device-migration package preparation, APK-share handoff and library-state history are interactive mock flows |
| Advanced controls | SETTINGS → Advanced | Standard/Advanced experience level controls progressive disclosure; diagnostics and technical settings live in dedicated sub-environments rather than the root list |
| About / build | SETTINGS → Advanced | Isolated-shell identity and backend-free status remain available without becoming a dashboard destination |
| Onboarding | First-run mock route / launch scenario | Local-folder and demo-library choices advance into the shell; service connection opens the isolated Settings flow without real permissions |
| Empty state | Scenario launch extra | Empty-library workspace remains navigable and offers mock import/add path |
| Loading state | Scenario launch extra | Bounded deterministic loading state, then resolves |
| Buffering state | Listening Spine + Expanded Listening + scenario fixture | Playback identity remains visible; transport and status state say BUFFERING explicitly and resolve deterministically |
| Partial connected-source state | FIND + scenario fixture | Connected-source degradation is named while local/indexed search remains usable |
| Search empty / search failure | FIND + deterministic scenario fixtures | Empty queries and connected-search failure retain query/navigation context; failure exposes explicit retry and owned-library fallback without pretending the provider succeeded |
| Queue empty | Expanded Listening + deterministic scenario fixture | Player does not claim a current track or playing state; listening environment gives direct Library/Find recovery routes while preserving app topology |
| Provider connecting / provider failure | SETTINGS → Connected services + deterministic fixtures | Transient connection and failure states are textual, provider-specific and recoverable; retry clears transient failure before ordinary connect/import state resumes |
| Download active / download failure | SETTINGS → Offline + deterministic fixtures | Active-transfer count and transfer failure are explicit; retry preserves queued/offline state and never fabricates successful completion |
| Unavailable media | Track ledger + listening transport + scenario fixture | Unavailable state is textual, play/seek/offline acquisition are disabled, and navigation/management context remains visible |
| Error state | Scenario launch extra + SIGNAL Diagnostics | Error is explicit, retry responds |
| Disconnected service | SETTINGS → Connected services + FIND catalogue | Provenance remains visible; reconnect control responds |
| Missing artwork | Library/listening mock object | Deliberately neutral gray content field with only a structural rule; TSUNAMI identity must remain in typography/geometry/navigation rather than the placeholder |
| Very long metadata | Long-title fixture | Wraps/truncates by role; full title remains accessible in expanded object |
| Giant font scale | Emulator verification scenario | The library workspace is captured at both 1.50× and 2.00× Android font scale and retained in the visual evidence matrix |
| High contrast / large controls | Accessibility launch scenario | High-contrast neutrals and selected-state colors are supplied by the design system; authored icon/text controls raise minimum targets from 48dp to 56dp |
| Long list / large library | LIBRARY synthetic rows | Lazy list + density/alphabetical index model represents 40/4k/40k behavior; artwork-free Index mode is separately captured and visually distinguished from Ledger |
| Back navigation | Entire shell | Android back collapses Expanded Listening or closes Settings before leaving the primary workspace |
| Light/dark mode | Entire shell | Same structural hierarchy in both palettes |
| Reduced motion | SETTINGS → Appearance | Holds the generated visual field static and keeps the shell independent of animation for wayfinding |

## Production-only platform capabilities intentionally not connected

The shell does **not** touch MediaStore, local folders, production databases, authentication, provider APIs, download engines, Media3 playback services, real signal telemetry, notifications, Quick Settings tiles, widgets, Wear, or production deep links. Their user-facing affordances are represented with deterministic mock state where relevant; integration is deliberately absent so the experiential prototype cannot mutate production data.


## Deliberately retired legacy presentation knobs

Capability inventory does not require perpetuating every legacy customization parameter. The production UI exposes several presentation knobs whose principal effect is to restyle the old interface rather than enable a distinct listening, organization, accessibility, or media-management task. Genesis therefore does **not** recreate arbitrary accent hue/saturation/brightness, artwork-derived chrome, card-opacity controls, universal corner-radius controls, fixed grid-column counts, an app-specific font-scale slider, or a continuous animation-speed scalar.

Those omissions are architectural, not accidental:

- functional color roles are authored and contrast-gated instead of user-tinting the entire hierarchy;
- artwork is content and cannot become the chrome color system;
- container geometry follows semantic boundaries rather than a global roundness preference;
- responsive window topology replaces fixed grid-column selection;
- Android/system font scaling is exercised at 150% and 200% rather than multiplying typography inside the app;
- reduced motion is an explicit accessibility state, while ordinary transitions retain short topology-explaining timing rather than exposing an arbitrary animation multiplier.

The relevant underlying needs—theme choice, high contrast, large controls, density, artwork visibility, responsive layout, one-handed reachability and reduced motion—remain represented in the Genesis architecture.
