#!/usr/bin/env python3
"""Fast source-level contract checks for the isolated TSUNAMI UI Genesis shell.

This deliberately does not masquerade as Android compilation or device proof. Its job is to catch
structural regressions before Gradle: accidental production coupling, dead controls, state/API drift,
missing deterministic QA scenarios, and settings-route inconsistencies.
"""
from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui-shell"
SRC = UI / "app/src/main/java/com/tsunami/shell"
TEST = UI / "app/src/androidTest/java/com/tsunami/shell/GenesisInteractionTest.kt"
CAPTURE = UI / "tools/capture_verify.sh"
VISUAL_SANITY = UI / "tools/visual_sanity_verify.py"
MANIFEST = UI / "app/src/main/AndroidManifest.xml"
CODESPACE_BUILD = ROOT / "tools/ui_shell_codespace_build.py"
PORTAL_PUBLISH = UI / "tools/publish_chromagora_apk.sh"
MARK_SPEC = ROOT / "brand/TSUNAMI-MARK-SPEC.md"
MARK_SVG = ROOT / "brand/tsunami-mark.svg"
MARK_KT = SRC / "brand/TsunamiMark.kt"
SHELL_TOOLS = [
    UI / "tools/bootstrap_gradle.sh",
    UI / "tools/build_host.sh",
    UI / "tools/capture_verify.sh",
    UI / "tools/jvm_state_gate.sh",
    PORTAL_PUBLISH,
]
PYTHON_TOOLS = [
    ROOT / "tools/ui_shell_gate.py",
    CODESPACE_BUILD,
    UI / "tools/accessibility_verify.py",
    UI / "tools/derive_review_images.py",
    UI / "tools/generate_tsunami_sans.py",
    UI / "tools/prepare_fonts.py",
    UI / "tools/source_verify.py",
    VISUAL_SANITY,
]

REQUIRED = [
    SRC / "MainActivity.kt",
    SRC / "navigation/GenesisShell.kt",
    SRC / "screens/ListenScreen.kt",
    SRC / "screens/LibraryScreen.kt",
    SRC / "screens/FindScreen.kt",
    SRC / "screens/ExpandedListening.kt",
    SRC / "screens/SignalScreen.kt",
    SRC / "screens/SettingsScreen.kt",
    SRC / "state/ShellState.kt",
    SRC / "model/MockModels.kt",
    SRC / "components/Primitives.kt",
    SRC / "theme/TsunamiTheme.kt",
    TEST,
    CAPTURE,
    VISUAL_SANITY,
    MANIFEST,
    CODESPACE_BUILD,
    PORTAL_PUBLISH,
    MARK_SPEC,
    MARK_SVG,
    MARK_KT,
]

FORBIDDEN_IMPORT_PREFIXES = (
    "com.tsunami.app.",
    "android.provider.MediaStore",
    "androidx.media3",
    "retrofit2.",
    "okhttp3.",
)

FORBIDDEN_PERMISSIONS = (
    "android.permission.INTERNET",
    "android.permission.READ_MEDIA_AUDIO",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
)

REQUIRED_SCENARIOS = {
    "default", "empty", "loading", "error", "missing-lyrics", "longform",
    "long-title", "no-artwork", "small-list", "long-list", "huge-list",
    "buffering", "unavailable", "partial", "accessibility", "onboarding", "podcast",
}

REQUIRED_PLAYER_MODES = {"queue", "lyrics", "output", "visual"}


class CheckError(RuntimeError):
    pass


def fail(msg: str) -> None:
    raise CheckError(msg)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def kotlin_files() -> list[Path]:
    return sorted(SRC.rglob("*.kt"))


def declared_shell_state_members(source: str) -> set[str]:
    return set(re.findall(r"\b(?:var|val|fun)\s+([A-Za-z_][A-Za-z0-9_]*)", source))


def state_references(source: str) -> set[str]:
    return set(re.findall(r"\bstate\.([A-Za-z_][A-Za-z0-9_]*)", source))


def settings_routes(settings: str) -> tuple[set[str], set[str]]:
    cases = set(re.findall(r'"([^"]+)"\s*->\s*[A-Za-z_][A-Za-z0-9_]*Settings\(state\)', settings))
    assignments = set(re.findall(r'state\.settingsExpanded\s*=\s*"([^"]+)"', settings))
    return cases, assignments


def capture_rows(script: str) -> list[tuple[str, str, str, str, str, str]]:
    rows = []
    for line in script.splitlines():
        line = line.strip()
        if not line.startswith("capture "):
            continue
        try:
            parts = shlex.split(line)
        except ValueError as exc:
            fail(f"malformed capture row: {line}: {exc}")
        if len(parts) < 5:
            fail(f"malformed capture row: {line}")
        name, screen, scenario, theme = parts[1:5]
        mode = parts[5] if len(parts) > 5 else ""
        page = parts[6] if len(parts) > 6 else ""
        rows.append((name, screen, scenario, theme, mode, page))
    return rows


def main() -> int:
    for path in REQUIRED:
        read(path)

    # Tooling syntax is part of the acceptance path: a shell/python verifier that cannot parse
    # must fail before we pretend the Android gate is runnable.
    for tool in PYTHON_TOOLS:
        source = read(tool)
        try:
            compile(source, str(tool), "exec")
        except SyntaxError as exc:
            fail(f"Python tooling syntax error in {tool.relative_to(ROOT)}: {exc}")
    bash = shutil.which("bash")
    if not bash:
        fail("bash is required to validate the UI Genesis shell toolchain")
    for tool in SHELL_TOOLS:
        cp = subprocess.run([bash, "-n", str(tool)], text=True, capture_output=True)
        if cp.returncode:
            fail(f"shell tooling syntax error in {tool.relative_to(ROOT)}: {(cp.stderr or cp.stdout).strip()}")
    print(f"TOOL_SYNTAX=PASS python={len(PYTHON_TOOLS)} shell={len(SHELL_TOOLS)}")

    manifest = read(MANIFEST)
    for permission in FORBIDDEN_PERMISSIONS:
        if permission in manifest:
            fail(f"backend-free shell declares forbidden permission: {permission}")

    members = declared_shell_state_members(read(SRC / "state/ShellState.kt"))
    referenced: set[str] = set()
    all_source = []
    for path in kotlin_files():
        text = read(path)
        all_source.append(text)
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            if re.search(rf"^import\s+{re.escape(prefix)}", text, flags=re.MULTILINE):
                fail(f"production/backend coupling in {path.relative_to(ROOT)}: {prefix}")
        if "TODO(" in text or "TODO:" in text or "FIXME" in text:
            fail(f"unfinished marker in {path.relative_to(ROOT)}")
        if re.search(r"\.clickable\s*\{\s*\}", text):
            fail(f"dead clickable in {path.relative_to(ROOT)}")
        if re.search(r"HitIcon\([^\n]*,\s*\{\s*\}\s*\)", text):
            fail(f"dead HitIcon action in {path.relative_to(ROOT)}")
        for call in ("ActionRow", "ToggleRow", "TextCommand"):
            if re.search(rf"{call}\([^;\n]*\)\s*\{{\s*\}}", text):
                fail(f"dead {call} action in {path.relative_to(ROOT)}")
        referenced |= state_references(text)

    missing = sorted(referenced - members - {"ShellState"})
    if missing:
        fail("ShellState API drift; referenced but undeclared: " + ", ".join(missing))

    # Direct authored click surfaces must expose a visible focus state for keyboard,
    # D-pad and switch users. Shared TextCommand/HitIcon controls satisfy this
    # internally; this catches ad-hoc clickable/combinedClickable regressions.
    focus_gaps = []
    for path in kotlin_files():
        text = read(path)
        for needle in (".clickable", ".combinedClickable"):
            cursor = 0
            while True:
                at = text.find(needle, cursor)
                if at < 0:
                    break
                line_start = text.rfind("\n", 0, at) + 1
                line_end = text.find("\n", at)
                if line_end < 0:
                    line_end = len(text)
                line = text[line_start:line_end].strip()
                if not line.startswith("import "):
                    prefix = text[max(0, at - 700):at]
                    if ".onFocusChanged" not in prefix:
                        focus_gaps.append(
                            f"{path.relative_to(ROOT)}:{text.count(chr(10), 0, at) + 1}:{needle}"
                        )
                cursor = at + len(needle)
    if focus_gaps:
        fail("clickable surfaces without visible focus: " + ", ".join(focus_gaps))

    # Focus-state locals are intentionally explicit because focus itself changes
    # structure (rule weight/background/border) in the authored system. Catch a
    # surprisingly easy source-only regression: adding a focus-state reference
    # without its remember/mutableStateOf declaration.
    undeclared_focus = []
    for path in kotlin_files():
        text = read(path)
        identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*Focused\b", text))
        identifiers.discard("isFocused")
        declared = set(re.findall(r"\b(?:var|val)\s+([A-Za-z_][A-Za-z0-9_]*Focused)\b", text))
        missing_focus = sorted(identifiers - declared)
        if missing_focus:
            undeclared_focus.append(f"{path.relative_to(ROOT)}:{','.join(missing_focus)}")
    if undeclared_focus:
        fail("focus-state identifiers referenced without declaration: " + "; ".join(undeclared_focus))
    print("DIRECT_CLICKABLE_FOCUS=PASS focus_state_declarations=PASS")

    # No visible control may be inert. Run this independently of source_verify.py
    # because this lightweight gate is the first line of defense before Gradle.
    dead_patterns = (
        re.compile(r"\bTextCommand\s*\([^,\n]+,\s*\{\s*\}\s*[,)]"),
        re.compile(r"\bHitIcon\s*\([^,\n]+,[^,\n]+,\s*\{\s*\}\s*[,)]"),
        re.compile(r"\bActionRow\s*\([^,\n]+,[^,\n]+,\s*\{\s*\}\s*\)"),
        re.compile(r"\bToggleRow\s*\([^,\n]+,[^,\n]+,\s*\{\s*\}\s*\)"),
        re.compile(r"\.clickable\s*(?:\([^)]*\))?\s*\{\s*\}"),
    )
    dead_controls = []
    for path in kotlin_files():
        text = read(path)
        code = text
        for pattern in dead_patterns:
            for match in pattern.finditer(code):
                dead_controls.append(
                    f"{path.relative_to(ROOT)}:{code.count(chr(10), 0, match.start()) + 1}"
                )
    if dead_controls:
        fail("dead interactive controls found: " + ", ".join(dead_controls))
    print("DEAD_CONTROLS=PASS")

    settings = read(SRC / "screens/SettingsScreen.kt")
    cases, assignments = settings_routes(settings)
    root_assignments = assignments - {"root"}
    missing_routes = sorted(root_assignments - cases)
    orphan_routes = sorted(cases - root_assignments)
    if missing_routes:
        fail("settings destinations without rendered page: " + ", ".join(missing_routes))
    if orphan_routes:
        fail("settings pages unreachable from root/detail navigation: " + ", ".join(orphan_routes))

    models = read(SRC / "model/MockModels.kt")
    scenarios = set(re.findall(r'"([a-z0-9-]+)"\s*->', models))
    scenarios |= set(re.findall(r'scenario\s*==\s*"([a-z0-9-]+)"', models))
    for group in re.findall(r'scenario\s+in\s+setOf\(([^)]*)\)', models):
        scenarios |= set(re.findall(r'"([a-z0-9-]+)"', group))
    scenarios.add("default")
    # Some deterministic scenarios are presentation/topology routes rather than fixture mutations.
    activity = read(SRC / "MainActivity.kt")
    shell = read(SRC / "navigation/GenesisShell.kt")
    if 'scenario=="accessibility"' in activity:
        scenarios.add("accessibility")
    if 'scenario=="onboarding"' in shell:
        scenarios.add("onboarding")
    if not REQUIRED_SCENARIOS <= scenarios:
        fail("mock scenario coverage missing: " + ", ".join(sorted(REQUIRED_SCENARIOS - scenarios)))

    mode_literals = set(re.findall(r'"(lyrics|output|visual)"\s*->\s*PlayerMode\.', activity)) | {"queue"}
    if mode_literals != REQUIRED_PLAYER_MODES:
        fail(f"player launch modes drifted: {sorted(mode_literals)}")

    captures = capture_rows(read(CAPTURE))
    if len(captures) != 37:
        fail(f"visual matrix count drifted: {len(captures)} != 37 captures")
    capture_names = [row[0] for row in captures]
    if len(set(capture_names)) != len(capture_names):
        duplicates = sorted({name for name in capture_names if capture_names.count(name) > 1})
        fail("duplicate capture names: " + ", ".join(duplicates))
    visual_sanity = read(VISUAL_SANITY)
    expected_block = re.search(r"EXPECTED\s*=\s*\{(?P<body>[\s\S]*?)\n\}", visual_sanity)
    if not expected_block:
        fail("visual sanity verifier EXPECTED set could not be parsed")
    expected_names = set(re.findall(r'"([0-9][0-9]-[^"]+)"', expected_block.group("body")))
    actual_names = set(capture_names)
    missing_from_verifier = sorted(actual_names - expected_names)
    missing_from_capture = sorted(expected_names - actual_names)
    if missing_from_verifier or missing_from_capture:
        fail(
            "capture/verifier name drift: "
            f"missing_from_verifier={missing_from_verifier} "
            f"missing_from_capture={missing_from_capture}"
        )
    if len(expected_names) != 37:
        fail(f"visual sanity expected-state count drifted: {len(expected_names)} != 37")
    print("VISUAL_MATRIX_PARITY=PASS states=37 names=exact")
    capture_scenarios = {row[2] for row in captures}
    unknown_scenarios = sorted(capture_scenarios - REQUIRED_SCENARIOS)
    if unknown_scenarios:
        fail("capture script uses unknown scenarios: " + ", ".join(unknown_scenarios))
    unknown_modes = sorted({row[4] for row in captures if row[4]} - REQUIRED_PLAYER_MODES)
    if unknown_modes:
        fail("capture script uses unknown player modes: " + ", ".join(unknown_modes))
    unknown_pages = sorted({row[5] for row in captures if row[5]} - cases)
    if unknown_pages:
        fail("capture script uses unknown Settings pages: " + ", ".join(unknown_pages))


    codespace_source = read(CODESPACE_BUILD)
    try:
        compile(codespace_source, str(CODESPACE_BUILD), "exec")
    except SyntaxError as exc:
        fail(f"Codespace fallback syntax error: {exc}")
    for anchor in (
        'OUT = ROOT / "dist"',
        "python3 tools/source_verify.py",
        "python3 tools/accessibility_verify.py",
        "Gradle 9.4.1",
        "bash tools/bootstrap_gradle.sh --version",
        "bash tools/bootstrap_gradle.sh :app:assembleDebug :app:assembleDebugAndroidTest",
        "remote_test_apk",
        'marker("SNAPSHOT_SHA=")',
        'marker("APP_SHA=")',
        'marker("TEST_SHA=")',
        '"snapshot_hash_match": True',
        '"test_apk_hash_match": True',
        "androidx.test.runner.AndroidJUnitRunner",
        "capture_matrix",
        "review_python()",
        "derive_review_images.py",
        "visual_sanity_verify.py",
        "TSUNAMI-UI-Genesis-device-review",
        "device_review_archive_sha256",
    ):
        if anchor not in codespace_source:
            fail(f"Codespace fallback missing verification anchor: {anchor}")

    mark_spec = read(MARK_SPEC)
    for anchor in (
        "Outer arch circle",
        "Inner optical counter",
        "Body diameter",
        "0.98399",
        "Clear space",
        "Scaling and small-size behavior",
    ):
        if anchor not in mark_spec:
            fail(f"brand master-mark specification missing anchor: {anchor}")

    mark_svg = read(MARK_SVG)
    mark_kt = read(MARK_KT)
    svg_geometry = (
        'viewBox="0 0 1000 820"',
        'M0 411.11 A509.61 509.61 0 0 1 1000 411.11',
        'L883.84 411.11 A394.61 394.61 0 0 0 116.16 411.11 Z',
        '<circle fill="currentColor" cx="500" cy="531" r="289"/>',
    )
    for anchor in svg_geometry:
        if anchor not in mark_svg:
            fail(f"brand SVG geometry drifted: {anchor}")
    compose_geometry = (
        "val sourceW = 1000f",
        "val sourceH = 820f",
        "rect(500f, 509.61f, 509.61f)",
        "startAngleDegrees = 191.14456f",
        "sweepAngleDegrees = 157.71088f",
        "lineTo(sx(883.84f), sy(411.11f))",
        "rect(500f, 502.69f, 394.61f)",
        "startAngleDegrees = 346.58072f",
        "sweepAngleDegrees = -153.16145f",
        "radius = 289f * scale",
        "center = Offset(sx(500f), sy(531f))",
    )
    for anchor in compose_geometry:
        if anchor not in mark_kt:
            fail(f"Android master-mark geometry drifted: {anchor}")
    print("BRAND_GEOMETRY_PARITY=PASS svg=1000x820 compose=canonical")

    publisher = read(PORTAL_PUBLISH)
    for anchor in (
        'DIST="$ROOT/dist"',
        'BUILT="$DIST/TSUNAMI-UI-Genesis-debug.apk"',
        'CODESPACE_MANIFEST="$DIST/codespace-build.json"',
        'CODESPACE_MANIFEST_BINDING=PASS',
        'payload.get("source_dirty") is False',
        'refusing portal publish from dirty UI Genesis source',
        'APK_ZIP_STRUCTURE=PASS',
    ):
        if anchor not in publisher:
            fail(f"portal publisher missing current-head artifact binding anchor: {anchor}")
    if 'ui-shell/dist' in codespace_source or 'ui-shell/dist' in publisher:
        fail("artifact path drift: Codespace/portal path must converge on root dist/")
    slash = "\\"
    escaped_expansions = (
        slash + "${TSUNAMI_PORTAL_APK_TARGET",
        slash + "${TSUNAMI_FORCE_CODESPACE_BUILD",
        slash + "${TARGET}",
    )
    for escaped in escaped_expansions:
        if escaped in publisher:
            fail(f"portal publisher contains escaped shell expansion: {escaped}")

    tests = read(TEST)
    expected_test_contracts = (
        "transportAndExpandedListeningAreInteractive",
        "libraryMultiSelectMutatesMockState",
        "searchToleratesOneEditOrAdjacentTransposition",
        "searchObjectDepthReturnsToResults",
        "signalDepthIsInteractiveAndTruthful",
        "advancedSettingsUseProgressiveDisclosure",
        "playlistInsertionIsVisibleInLibraryObject",
        "longformSeparatesAudiobooksAndPodcasts",
        "providerImportAuditPreservesLibraryAcrossDisconnect",
        "unavailableTrackCanOpenWithoutPretendingToPlay",
    )
    for name in expected_test_contracts:
        if f"fun {name}(" not in tests:
            fail(f"missing interaction regression: {name}")

    print(f"UI_SHELL_STATIC=PASS kotlin_files={len(kotlin_files())} state_members={len(members)} state_refs={len(referenced)} settings_routes={len(cases)} captures={len(captures)} focus_visible=all_direct_clickables codespace_build=syntax+apk+test-apk+instrumentation+derived-visual-evidence portal_publish=current-head+clean-source+hash-bound")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as exc:
        print(f"UI_SHELL_STATIC=FAIL {exc}")
        raise SystemExit(2)
