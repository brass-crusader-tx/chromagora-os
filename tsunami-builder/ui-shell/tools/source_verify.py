#!/usr/bin/env python3
"""Static source contract for the isolated TSUNAMI UI Genesis shell.

This is intentionally narrower than Android compilation. It catches architectural regressions that
can otherwise compile successfully: accidental production I/O, generic Material identity, dead
interaction placeholders, missing state fixtures, or source corruption.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

UI = Path(__file__).resolve().parents[1]
SRC = UI / "app/src/main/java/com/tsunami/shell"
TEST = UI / "app/src/androidTest/java/com/tsunami/shell/GenesisInteractionTest.kt"
MANIFEST = UI / "app/src/main/AndroidManifest.xml"
FONT_GEN = UI / "tools/generate_tsunami_sans.py"
CAPTURE = UI / "tools/capture_verify.sh"
VISUAL_SANITY = UI / "tools/visual_sanity_verify.py"
BUILD_GRADLE = UI / "app/build.gradle.kts"
LAUNCHER_FOREGROUND = UI / "app/src/main/res/drawable/ic_tsunami_launcher_foreground.xml"
LAUNCHER_ADAPTIVE = UI / "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml"
LAUNCHER_ROUND = UI / "app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml"

REQUIRED = [
    SRC / "MainActivity.kt",
    SRC / "brand/TsunamiMark.kt",
    SRC / "components/Primitives.kt",
    SRC / "model/MockModels.kt",
    SRC / "navigation/GenesisShell.kt",
    SRC / "screens/ListenScreen.kt",
    SRC / "screens/LibraryScreen.kt",
    SRC / "screens/FindScreen.kt",
    SRC / "screens/ExpandedListening.kt",
    SRC / "screens/SignalScreen.kt",
    SRC / "screens/SettingsScreen.kt",
    SRC / "screens/OnboardingScreen.kt",
    SRC / "state/ShellState.kt",
    SRC / "theme/TsunamiTheme.kt",
    TEST,
    MANIFEST,
    FONT_GEN,
    BUILD_GRADLE,
    LAUNCHER_FOREGROUND,
    LAUNCHER_ADAPTIVE,
    LAUNCHER_ROUND,
    UI / "tools/jvm_state_gate.sh",
    UI / "tools/accessibility_verify.py",
    UI / "tools/bootstrap_gradle.sh",
    UI / "tools/build_host.sh",
    UI / "tools/publish_chromagora_apk.sh",
    CAPTURE,
    VISUAL_SANITY,
    UI.parent / "tools/ui_shell_codespace_build.py",
    UI.parent / ".github/workflows/ui-shell-genesis-selfhosted.yml",
    UI.parent / "docs/TSUNAMI-UI-GENESIS-VISUAL-REVIEW.md",
    UI.parent / "brand/tsunami-mark.svg",
    UI.parent / "brand/TSUNAMI-MARK-GEOMETRY.md",
]

FORBIDDEN_SOURCE = {
    "android.provider.MediaStore": "production MediaStore access",
    "ContentResolver": "production content-provider access",
    "okhttp": "network client",
    "retrofit": "network client",
    "java.net.": "raw network access",
    "ktor": "network client",
    "Firebase": "production service SDK",
    "OAuth": "authentication flow",
    "HttpURLConnection": "network access",
    "FileInputStream": "direct production filesystem read",
    "androidx.room": "production database",
    "androidx.compose.material.icons": "stock Material icon identity",
    "androidx.compose.material3.Card": "generic card composition",
}


FORBIDDEN_UI_TROPES = {
    "RoundedCornerShape": "generic rounded-card/pill geometry",
    "CircleShape": "generic circular control-container identity",
    ".shadow(": "decorative shadow/elevation",
    "Brush.linearGradient": "decorative gradient",
    "Brush.radialGradient": "decorative gradient",
    "Brush.sweepGradient": "decorative gradient",
    "FloatingActionButton": "floating-action-button cliché",
    "material3.Card": "generic Material card composition",
    "material3.Surface": "generic Material surface composition",
    "MaterialTheme": "un-authored Material theme identity",
}

FORBIDDEN_MANIFEST = (
    "android.permission.INTERNET",
    "android.permission.READ_MEDIA_AUDIO",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
)

REQUIRED_ANCHORS = {
    "model/MockModels.kt": [
        '"small-list"', '"long-list"', '"huge-list"', '"missing-art"', '"loading"', '"error"', '"buffering"', '"partial"', '"unavailable"', '"podcast"',
        "LibraryLens", "SearchKind", "FOLDERS", "SearchIntent", "LongformType", "ProviderImportAuditMock",
    ],
    "state/ShellState.kt": [
        "playNext(", "shuffleNext(", "moveQueue(", "toggleDownload(", "addToPlaylist(",
        "createEmptyPlaylist(", "cycleRepeat(", "cycleCrossfade(", "advanceImport(", "importAudits", "describeImportAudit(", "announceImportAudit(",
        "selectedTrackIds", "addSelectionToPlaylist(", "hiddenLibrarySections", "metadataTemplate", "if(!track.available && play)", "lyricsGlobalDelayMs", "showArtworkInPlayer", "buffering", "togglePlayback(",
        "highContrast", "largeControls", "hapticStrength", "wifiOnlyDownloads", "lyricsAutoFetch", "resumePositions", "playedLongform", "seekRelative(", "togglePlayedLongform(", "listenLens",
        "signalSection", "runGaplessProbe(", "auditLyrics(", "scanDuplicateHashes(", "exportReplay(",
        "excludedGenres", "excludedPlaylistPaths", "swipeUp", "swipeDown", "albumArtistMode", "prepareDeviceMigration(",
        "miniPlayerExtras", "fullPlayerButtons", "notificationActions", "toggleNotificationAction(", "quickSettingsActions", "toggleQuickSettingsAction(", "widgetLayout", "cycleWidgetLayout(", "wearControlsEnabled", "wearSecondaryAction", "cycleWearSecondaryAction(", "runPlayerAction(",
        "eqBandsDb", "cycleEqBand(", "lyricSourceOrder", "moveLyricSource(", "librarySectionOrder", "moveLibrarySection(",
        'fullPlayerButtons = mutableStateListOf("Favourite","Offline","Share")', 'quickActions = mutableStateListOf("Sleep timer")',
    ],
    "brand/TsunamiMark.kt": ["509.61f", "394.61f", "411.11f", "289f", "157.71088f", "-153.16145f"],
    "navigation/GenesisShell.kt": [
        "IndexRail(", "IndexStrip(", "ListeningSpine(", "AnimatedContent(", "reducedMotion", "miniPlayerExtras", "runPlayerAction(",
    ],
    "screens/ListenScreen.kt": ["Choose from your library", "Deep cuts", "Rediscover", "Never heard", "Most played", "Unfinished", 'state.settingsExpanded="services"'],
    "screens/FindScreen.kt": ["SearchKind.FOLDERS", "folderFor(", "FOLDER MATCH", "fuzzyContains(", "withinOneEditOrTranspose("],
    "screens/SignalScreen.kt": ["Summary", "Audio", "Library", "History", "Logs", "TSUNAMI Replay", "Lyrics quality & repair queue", "Playback integrity"],
    "screens/OnboardingScreen.kt": ['state.settingsExpanded="services"', "Enter with the sample library", "Index a music folder"],
    "screens/ExpandedListening.kt": [
        "PlayerMode.QUEUE", "PlayerMode.LYRICS", "PlayerMode.OUTPUT", "PlayerMode.VISUAL", "PlayerMode.OUTPUT to \"Output\"", "LongformType.AUDIOBOOK", "LongformType.PODCAST", "\"Back 30 sec\"", "\"Mark played\"",
        "TimeRuler(", "Bookmark", "invokeObjectAction(", "val contextualActions=state.quickActions.distinct()", 'label="listening-mode"', "state.reducedMotion",
    ],
    "screens/LibraryScreen.kt": [
        "LibraryLens.TRACKS", "LibraryLens.ALBUMS", "LibraryLens.ARTISTS",
        "LibraryLens.PLAYLISTS", "LibraryLens.FOLDERS", "LibraryLens.LONGFORM",
        "LibraryLens.RADIO", "animateScrollToItem", "selectionMode",
    ],
    "screens/SettingsScreen.kt": [
        '"audio"', '"visualizer"', '"shuffle"', '"library-roots"', '"library-sections"',
        '"library-profiles"', '"metadata"', '"scrobbling"', '"backup"', '"controls"',
        '"context-rules"', '"quick-actions"', '"custom-sections"', '"audio-profiles"', '"lyrics"', '"presentation"', '"services"', '"equalizer"', '"lyric-sources"', '"external-controls"',
        "ControlSettings(", "Player action surfaces", "Headset controls", "ExternalControlSettings(", "Notification transport", "Quick Settings", "Home-screen widget", "Wear transport", "ContextRuleSettings(", "QuickActionSettings(",
        "CustomSectionsSettings(", "AudioProfilesSettings(", "ServicesSettings(", "EqualizerSettings(", "LyricSourcesSettings(", "Library lens order", "Hide $section",
        "Excluded genres", "Excluded playlist paths", "Swipe up", "Swipe down", "TSUNAMI device migration", "Album artist",
    ],
    "components/Primitives.kt": ["Deliberately neutral", "drawRect(p.rule,style=Stroke", "collectIsPressedAsState", "onFocusChanged"],
    "theme/TsunamiTheme.kt": ["TsunamiFont", "R.font.tsunami_sans_light", "R.font.tsunami_sans_bold", "LightHighContrast", "DarkHighContrast", "LocalControlTarget"],
}


PRIMARY_COPY_GUARDS = {
    "screens/ListenScreen.kt": [
        "Resume first. Choose second.",
        "The shell stays navigable without inventing recommendations.",
    ],
    "screens/OnboardingScreen.kt": [
        "The prototype never asks for production permissions.",
        "Backend-free experiential shell",
    ],
    "screens/SignalScreen.kt": [
        "Technical information appears only where it changes understanding, trust, or recovery.",
    ],
    "screens/ExpandedListening.kt": [
        "TSUNAMI does not fabricate a karaoke layer.",
        "Generated from deterministic mock state",
    ],
}

def die(message: str) -> None:
    raise SystemExit(f"SOURCE_VERIFY_FAIL: {message}")

def strip_noncode(src: str) -> str:
    out: list[str] = []
    i = 0
    state = "code"
    while i < len(src):
        ch = src[i]
        nxt = src[i + 1] if i + 1 < len(src) else ""
        tri = src[i:i+3]
        if state == "code":
            if tri == '"""':
                state = "triple"; out.extend("   "); i += 3; continue
            if ch == '"':
                state = "string"; out.append(" "); i += 1; continue
            if ch == "'":
                state = "char"; out.append(" "); i += 1; continue
            if ch == "/" and nxt == "/":
                state = "line"; out.extend("  "); i += 2; continue
            if ch == "/" and nxt == "*":
                state = "block"; out.extend("  "); i += 2; continue
            out.append(ch); i += 1; continue
        if state == "string":
            if ch == "\\":
                out.extend("  "); i += 2; continue
            if ch == '"':
                state = "code"
            out.append("\n" if ch == "\n" else " "); i += 1; continue
        if state == "char":
            if ch == "\\":
                out.extend("  "); i += 2; continue
            if ch == "'":
                state = "code"
            out.append("\n" if ch == "\n" else " "); i += 1; continue
        if state == "triple":
            if tri == '"""':
                state = "code"; out.extend("   "); i += 3; continue
            out.append("\n" if ch == "\n" else " "); i += 1; continue
        if state == "line":
            if ch == "\n":
                state = "code"; out.append("\n")
            else:
                out.append(" ")
            i += 1; continue
        if state == "block":
            if ch == "*" and nxt == "/":
                state = "code"; out.extend("  "); i += 2; continue
            out.append("\n" if ch == "\n" else " "); i += 1; continue
    if state not in {"code", "line"}:
        die(f"unterminated Kotlin lexical state: {state}")
    return "".join(out)

def check_balance(path: Path, src: str) -> None:
    code = strip_noncode(src)
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    line = 1
    for ch in code:
        if ch == "\n":
            line += 1
        elif ch in "([{":
            stack.append((ch, line))
        elif ch in pairs:
            if not stack or stack[-1][0] != pairs[ch]:
                die(f"{path.relative_to(UI)} delimiter mismatch near line {line}")
            stack.pop()
    if stack:
        die(f"{path.relative_to(UI)} unclosed delimiters: {stack[-5:]}")

def main() -> int:
    missing = [str(p.relative_to(UI)) for p in REQUIRED if not p.is_file()]
    if missing:
        die("missing required files: " + ", ".join(missing))

    kotlin_files = sorted(SRC.rglob("*.kt")) + [TEST]
    source_text = {}
    for path in kotlin_files:
        src = path.read_text(encoding="utf-8")
        source_text[path] = src
        check_balance(path, src)
        code = strip_noncode(src)
        if re.search(r"fun\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*=\s*[^,\n)]*\b(?:return|break|continue)\b", code):
            die(f"illegal jump expression in default parameter in {path.relative_to(UI)}")
        if re.search(r"\.clickable\s*(?:\([^)]*\))?\s*\{\s*\}", code):
            die(f"dead clickable lambda in {path.relative_to(UI)}")
        dead_handler_patterns = {
            r"TextCommand\s*\([^\n]*,\s*\{\s*\}\s*(?:,|\))": "TextCommand",
            r"HitIcon\s*\([^\n]*,\s*\{\s*\}\s*(?:,|\))": "HitIcon",
            r"ActionRow\s*\([^\n]*\)\s*\{\s*\}": "ActionRow",
            r"ToggleRow\s*\([^\n]*\)\s*\{\s*\}": "ToggleRow",
        }
        for pattern,label in dead_handler_patterns.items():
            if re.search(pattern, code):
                die(f"dead {label} handler in {path.relative_to(UI)}")
        for needle, reason in FORBIDDEN_SOURCE.items():
            if needle.lower() in code.lower():
                die(f"{reason}: {needle} in {path.relative_to(UI)}")
        for needle, reason in FORBIDDEN_UI_TROPES.items():
            if needle in code:
                die(f"anti-tackiness regression ({reason}): {needle} in {path.relative_to(UI)}")

    manifest = MANIFEST.read_text(encoding="utf-8")
    for permission in FORBIDDEN_MANIFEST:
        if permission in manifest:
            die(f"forbidden backend-facing permission declared: {permission}")
    if "<uses-permission" in manifest:
        die("shell manifest unexpectedly declares an Android permission")
    for anchor in (
        'android:label="TSUNAMI"',
        'android:icon="@mipmap/ic_launcher"',
        'android:roundIcon="@mipmap/ic_launcher_round"',
        'android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout|density"',
    ):
        if anchor not in manifest:
            die(f"launcher/product identity missing manifest anchor: {anchor}")
    foreground = LAUNCHER_FOREGROUND.read_text(encoding="utf-8")
    adaptive = LAUNCHER_ADAPTIVE.read_text(encoding="utf-8")
    round_adaptive = LAUNCHER_ROUND.read_text(encoding="utf-8")
    for anchor in ("M0,411.11", "A509.61,509.61", "M500,242", "A289,289"):
        if anchor not in foreground:
            die(f"launcher foreground is not derived from master mark geometry: {anchor}")
    for xml in (adaptive, round_adaptive):
        if "@color/tsunami_launcher_ground" not in xml or "@drawable/ic_tsunami_launcher_foreground" not in xml:
            die("adaptive launcher icon must use authored TSUNAMI ground + foreground")

    for rel, anchors in REQUIRED_ANCHORS.items():
        src = (SRC / rel).read_text(encoding="utf-8")
        absent = [a for a in anchors if a not in src]
        if absent:
            die(f"{rel} missing architecture anchors: {absent}")

    for rel, forbidden_phrases in PRIMARY_COPY_GUARDS.items():
        src = (SRC / rel).read_text(encoding="utf-8")
        present = [phrase for phrase in forbidden_phrases if phrase in src]
        if present:
            die(f"{rel} regressed to portfolio/prototype microcopy on a primary surface: {present}")
    product_copy_forbidden=("demo ","prototype status","backend-free","experiential prototype")
    product_copy_hits={}
    for path in sorted((SRC / "screens").glob("*.kt")):
        src=path.read_text(encoding="utf-8").lower()
        found=[token for token in product_copy_forbidden if token in src]
        if found:
            product_copy_hits[str(path.relative_to(SRC))]=found
    if product_copy_hits:
        die(f"product surfaces expose development-language copy: {product_copy_hits}")
    print("PRIMARY_COPY_TONE=PASS functional_not_portfolio development_language=absent")

    # Cross-file state contract: every state.<member> used by UI compositions must resolve
    # to an actual ShellState property/function. This catches a class of refactor failures that a
    # delimiter-only source scan cannot see, while remaining independent of Android/Gradle.
    state_src = (SRC / "state/ShellState.kt").read_text(encoding="utf-8")
    state_members = set(re.findall(r"\b(?:var|val)\s+([A-Za-z_][A-Za-z0-9_]*)\b", state_src))
    state_members.update(re.findall(r"\bfun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", state_src))
    state_members.update({"fixture", "currentTrack"})
    unresolved_state: dict[str, list[str]] = {}
    for path, src in source_text.items():
        if path.name == "ShellState.kt":
            continue
        for member in re.findall(r"\bstate\.([A-Za-z_][A-Za-z0-9_]*)", src):
            # package import com.tsunami.shell.state.ShellState is not a state-object reference.
            if member == "ShellState":
                continue
            if member not in state_members:
                unresolved_state.setdefault(member, []).append(str(path.relative_to(UI)))
    if unresolved_state:
        die(f"unresolved ShellState UI references: {unresolved_state}")

    # Listening action-surface contract: stable transport, listening modes, object actions and
    # quick actions must remain separate. This prevents customization from reintroducing the
    # duplicated-control failure mode the Genesis interaction model deliberately removed.
    def literal_state_list(name: str) -> list[str]:
        match=re.search(rf"\b{name}\s*=\s*mutableStateListOf\(([^)]*)\)", state_src)
        if not match:
            die(f"missing state list {name}")
        return re.findall(r'"([^"]+)"', match.group(1))

    mini_actions=literal_state_list("miniPlayerExtras")
    full_actions=literal_state_list("fullPlayerButtons")
    quick_actions=literal_state_list("quickActions")
    notification_actions=literal_state_list("notificationActions")
    quick_settings_actions=literal_state_list("quickSettingsActions")
    stable_transport={"Previous","Play/Pause","Next","Shuffle","Repeat"}
    listening_modes={"Queue","Lyrics","Output","Visual"}
    if stable_transport & set(full_actions):
        die(f"full-player object actions overlap stable transport: {sorted(stable_transport & set(full_actions))}")
    if listening_modes & set(full_actions):
        die(f"full-player object actions overlap listening modes: {sorted(listening_modes & set(full_actions))}")
    if listening_modes & set(quick_actions):
        die(f"quick actions overlap listening modes: {sorted(listening_modes & set(quick_actions))}")
    if not {"Previous","Play/Pause","Next"}.issubset(set(notification_actions)):
        die("notification action defaults lost the stable previous/play-pause/next transport triad")
    if "Play/Pause" not in quick_settings_actions:
        die("Quick Settings defaults lost the primary play/pause transport action")
    if len(mini_actions)>2 or len(full_actions)>5 or len(notification_actions)>5 or len(quick_settings_actions)>2:
        die("customizable action-surface defaults exceed their authored capacity")
    if not set(quick_settings_actions).issubset(stable_transport | {"Favourite"}):
        die(f"Quick Settings contains unsupported action(s): {quick_settings_actions}")
    print("LISTENING_ACTION_SURFACES=PASS stable_transport modes object_actions quick_actions notification quick_settings widget wear=separated")
    test_src=TEST.read_text(encoding="utf-8")
    if "externalPlaybackSurfacesHaveExplicitMockContracts" not in test_src:
        die("external playback surfaces lost their instrumentation contract")
    print("EXTERNAL_PLAYBACK_SURFACES=PASS notification quick_settings widget wear")

    all_src = "\n".join(source_text.values())
    direct_clickables = len(re.findall(r"\.clickable\b", all_src))
    combined_clickables = len(re.findall(r"\.combinedClickable\b", all_src))
    text_commands = len(re.findall(r"\bTextCommand\s*\(", all_src))
    hit_icons = len(re.findall(r"\bHitIcon\s*\(", all_src))
    settings_actions = len(re.findall(r"\bActionRow\s*\(", all_src))
    settings_toggles = len(re.findall(r"\bToggleRow\s*\(", all_src))
    counts = {
        "kotlin_files": len(kotlin_files),
        "clickable": direct_clickables,
        "combined_clickable": combined_clickables,
        "text_commands": text_commands,
        "hit_icons": hit_icons,
        "settings_actions": settings_actions,
        "settings_toggles": settings_toggles,
        "authored_actions": direct_clickables + combined_clickables + text_commands + hit_icons + settings_actions + settings_toggles,
        "instrumentation_tests": len(re.findall(r"@Test\s+fun\s+[A-Za-z0-9_]+", TEST.read_text(encoding="utf-8"))),
    }
    floors = {
        "kotlin_files": 15,
        # Direct clickables legitimately decrease when ad-hoc actions are migrated
        # into focus-visible authored primitives; guard the aggregate interaction
        # surface rather than forcing a historical implementation detail.
        "clickable": 18,
        "combined_clickable": 1,
        "text_commands": 69,
        "hit_icons": 28,
        "settings_actions": 100,
        "settings_toggles": 45,
        "authored_actions": 280,
        "instrumentation_tests": 27,
    }
    collapsed = {name: (counts[name], minimum) for name, minimum in floors.items() if counts[name] < minimum}
    if collapsed:
        die(f"interaction/test surface unexpectedly collapsed: {collapsed}; current={counts}")

    font_src = FONT_GEN.read_text(encoding="utf-8")
    for anchor in ("TSUNAMI Sans", "WEIGHTS=[('Light',300", "'Bold',700", "addOpenTypeFeaturesFromString", "Version 4.700", "FONT_TIMESTAMP=3873139200"):
        if anchor not in font_src:
            die(f"font generator missing anchor: {anchor}")

    build_src = BUILD_GRADLE.read_text(encoding="utf-8")
    root_build_src = (UI / "build.gradle.kts").read_text(encoding="utf-8")
    for anchor in ('compileSdk = 36', 'targetSdk = 36', 'androidx.compose.ui:ui:1.11.4', 'org.jetbrains.kotlin.plugin.compose'):
        if anchor not in build_src:
            die(f"Android build contract missing anchor: {anchor}")
    if 'org.jetbrains.kotlin.android' in build_src or 'org.jetbrains.kotlin.android' in root_build_src:
        die("AGP 9 shell must not apply the incompatible kotlin-android plugin")
    for anchor in ('id("com.android.application") version "9.2.1"', 'id("org.jetbrains.kotlin.plugin.compose") version "2.2.10"'):
        if anchor not in root_build_src:
            die(f"AGP 9 built-in Kotlin toolchain missing anchor: {anchor}")
    bootstrap=(UI / "tools/bootstrap_gradle.sh").read_text(encoding="utf-8")
    for anchor in ('GRADLE_VERSION="9.4.1"', 'GRADLE_SHA256="2ab2958f2a1e51120c326cad6f385153bb11ee93b3c216c5fccebfdfbb7ec6cb"', 'services.gradle.org/distributions'):
        if anchor not in bootstrap:
            die(f"Gradle bootstrap missing reproducibility anchor: {anchor}")
    host_build=(UI / "tools/build_host.sh").read_text(encoding="utf-8")
    if 'bootstrap_gradle.sh" --print-gradle' not in host_build:
        die("host build must resolve Gradle through the checksum-verified bootstrap")
    for anchor in (
        'JDK 17 or newer',
        '/usr/libexec/java_home -v 17',
        'build-tools/36.0.0',
        '"platform-tools" "platforms;android-36" "build-tools;36.0.0"',
    ):
        if anchor not in host_build:
            die(f"host build provisioning contract missing anchor: {anchor}")
    portal_publish=(UI / "tools/publish_chromagora_apk.sh").read_text(encoding="utf-8")
    for anchor in (
        'tools/source_verify.py',
        'tools/accessibility_verify.py',
        'tools/ui_shell_codespace_build.py',
        'APK_ZIP_STRUCTURE=PASS',
        'PORTAL_APK_SHA256=',
        'PORTAL_APK_SOURCE_HEAD=',
        'build_backend',
        '--untracked-files=all',
        'START_HEAD=',
        'Genesis HEAD changed during build',
        'UI Genesis source changed during build',
    ):
        if anchor not in portal_publish:
            die(f"Chromagora publish path missing safety anchor: {anchor}")
    codespace_build=(UI.parent / "tools/ui_shell_codespace_build.py").read_text(encoding="utf-8")
    for anchor in (
        'TSUNAMI Builder',
        'snapshot_hash_match',
        'test_apk_hash_match',
        'remote_source_verify',
        'remote_accessibility_verify',
        'if len(base_captures) != 37:',
        '--untracked-files=all',
    ):
        if anchor not in codespace_build:
            die(f"Codespaces fallback missing verification anchor: {anchor}")
    visual_sanity=VISUAL_SANITY.read_text(encoding="utf-8")
    capture_script=CAPTURE.read_text(encoding="utf-8")
    capture_names=[]
    for line in capture_script.splitlines():
        line=line.strip()
        if line.startswith("capture "):
            fields=line.split()
            if len(fields)<2:
                die(f"malformed visual capture row: {line}")
            capture_names.append(fields[1])
    expected_match=re.search(r"EXPECTED\s*=\s*\{(?P<body>[\s\S]*?)\n\}",visual_sanity)
    if not expected_match:
        die("visual sanity EXPECTED state set could not be parsed")
    expected_names=set(re.findall(r'"([0-9][0-9]-[^"]+)"',expected_match.group("body")))
    if len(capture_names)!=37 or len(set(capture_names))!=37 or len(expected_names)!=37:
        die(f"visual matrix cardinality drift capture={len(capture_names)} unique={len(set(capture_names))} expected={len(expected_names)}")
    if set(capture_names)!=expected_names:
        die(
            "visual capture/verifier state drift "
            f"capture_only={sorted(set(capture_names)-expected_names)} "
            f"verifier_only={sorted(expected_names-set(capture_names))}"
        )
    print("VISUAL_MATRIX_PARITY=PASS states=37 names=exact")
    for anchor in (
        "ARTWORK_IDENTITY_PAIRS",
        "squint_range < 24",
        "delta > 46",
        "hierarchy=verified",
        "artwork_identity=verified",
    ):
        if anchor not in visual_sanity:
            die(f"visual acceptance gate missing hierarchy/artwork-identity anchor: {anchor}")

    selfhosted=(UI.parent / ".github/workflows/ui-shell-genesis-selfhosted.yml").read_text(encoding="utf-8")
    for anchor in (
        'bash ui-shell/tools/build_host.sh',
        'bash ui-shell/tools/build_host.sh --verify-device "$SERIAL"',
        'VISUAL_CAPTURE=PASS states=37',
        'VISUAL_SANITY=PASS',
        'CRASH_SCAN=PASS',
        'instrumentation.txt',
        'contact-sheet.png',
    ):
        if anchor not in selfhosted:
            die(f"self-hosted Motorola acceptance workflow missing anchor: {anchor}")

    print("SOURCE_VERIFY=PASS")
    print("BACKEND_FREE_SOURCE=PASS")
    print("KOTLIN_DEFAULT_PARAMETER_JUMP_GUARD=PASS")
    print("NO_DEAD_CLICKABLES=PASS")
    print("NO_DEAD_AUTHORED_CONTROLS=PASS TextCommand HitIcon ActionRow ToggleRow")
    print(f"STATE_REFERENCE_CONTRACT=PASS members={len(state_members)}")
    print("NO_STOCK_MATERIAL_ICON_IDENTITY=PASS")
    print("ANTI_TACKINESS_SOURCE=PASS no_cards_no_pills_no_gradients_no_shadows_no_fab")
    print("BRAND_LAUNCHER_CONTRACT=PASS name=TSUNAMI adaptive=present canonicalComposeGeometry=present")
    print("BUILD_STACK_CONTRACT=PASS compileSdk=36 targetSdk=36 compose=1.11.4 agp=9.2.1 builtInKotlin=2.2.10 gradle=9.4.1")
    print("PORTAL_PUBLISH_CONTRACT=PASS host_then_codespace hash_bound atomic_manifested")
    print("VISUAL_IDENTITY_GATE_CONTRACT=PASS monochrome squint hierarchy artwork-removal")
    print("SELFHOSTED_DEVICE_GATE_CONTRACT=PASS build instrumentation visual37 crash_scan")
    print("INTERACTION_COUNTS=" + ",".join(f"{k}:{v}" for k,v in counts.items()))
    return 0

if __name__ == "__main__":
    sys.exit(main())
