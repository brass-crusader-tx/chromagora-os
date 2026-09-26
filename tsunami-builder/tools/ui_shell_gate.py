#!/usr/bin/env python3
"""Canonical verification gate for the isolated TSUNAMI UI Genesis shell.

The shell is deliberately outside the production Android Gradle graph. This gate validates the
visible source tree, generates TSUNAMI Sans from source, builds the APK, runs interaction tests on
an Android emulator, captures mandatory visual states, derives monochrome/squint review images,
checks for crashes and forbidden production-facing permissions, and packages reproducible evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui-shell"
REPORT = ROOT / "build" / "reports" / "tsunami" / "ui-shell"
JVM_STATE_STATUS = "NOT_RUN"
FONT_MANIFEST = ROOT / "docs" / "TSUNAMI-SANS-v4.8-MANIFEST.json"


def load_font_manifest() -> dict:
    if not FONT_MANIFEST.is_file():
        raise RuntimeError(f"canonical TSUNAMI Sans manifest missing: {FONT_MANIFEST}")
    data = json.loads(FONT_MANIFEST.read_text(encoding="utf-8"))
    if data.get("family") != "TSUNAMI Sans" or data.get("version") != "4.800":
        raise RuntimeError(f"unexpected TSUNAMI Sans manifest identity: {data.get('family')!r} {data.get('version')!r}")
    return data


def manifest_font_hashes(data: dict) -> dict[str, str]:
    weights = data.get("weights", {})
    required = ("Light", "Regular", "Medium", "Semibold", "Bold")
    missing = [name for name in required if name not in weights]
    if missing:
        raise RuntimeError("TSUNAMI Sans manifest misses weights: " + ", ".join(missing))
    return {
        f"tsunami_sans_{name.lower()}.ttf": weights[name]["sha256"]
        for name in required
    }

REQUIRED_SOURCE = [
    "app/src/main/java/com/tsunami/shell/MainActivity.kt",
    "app/src/main/java/com/tsunami/shell/navigation/GenesisShell.kt",
    "app/src/main/java/com/tsunami/shell/screens/ExpandedListening.kt",
    "app/src/main/java/com/tsunami/shell/screens/LibraryScreen.kt",
    "app/src/main/java/com/tsunami/shell/screens/FindScreen.kt",
    "app/src/main/java/com/tsunami/shell/screens/SignalScreen.kt",
    "app/src/main/java/com/tsunami/shell/screens/SettingsScreen.kt",
    "app/src/main/java/com/tsunami/shell/components/Primitives.kt",
    "app/src/main/java/com/tsunami/shell/state/ShellState.kt",
    "tools/generate_tsunami_sans.py",
    "tools/capture_verify.sh",
    "tools/derive_review_images.py",
]

FORBIDDEN_PERMISSIONS = {
    "android.permission.INTERNET",
    "android.permission.READ_MEDIA_AUDIO",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
}


def run(cmd, *, cwd=ROOT, env=None, check=True, input_text=None, capture=False):
    cmd = [str(x) for x in cmd]
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        input=input_text,
        check=check,
        capture_output=capture,
    )


def ensure_tool_python() -> None:
    """Run the gate inside the repository-pinned Python toolchain."""
    try:
        import fontTools  # noqa: F401
        import shapely  # noqa: F401
        import PIL  # noqa: F401
        return
    except ImportError:
        pass
    venv = ROOT / "build/.ui-shell-toolchain/venv"
    python = venv / "bin/python"
    if not python.is_file():
        run([sys.executable, "-m", "venv", venv])
    run([
        python, "-m", "pip", "install", "--disable-pip-version-check", "--quiet",
        "fonttools==4.63.0", "shapely==2.1.2", "pillow==12.3.0",
    ])
    if Path(sys.prefix).resolve() != venv.resolve():
        os.execv(str(python), [str(python), str(Path(__file__).resolve())])


def gradle_command(*args: str) -> list[str]:
    """Resolve exactly Gradle 9.4.1; never inherit an arbitrary host Gradle."""
    system = shutil.which("gradle")
    if system:
        probe = subprocess.run([system, "--version"], text=True, capture_output=True)
        if probe.returncode == 0 and re.search(r"^Gradle 9\\.4\\.1$", probe.stdout, re.M):
            return [system, *args]
    bootstrap = UI / "tools/bootstrap_gradle.sh"
    if not bootstrap.is_file():
        raise RuntimeError("Gradle 9.4.1 is unavailable and the UI-shell bootstrap is missing")
    return ["bash", str(bootstrap), *args]


def verify_build_configuration() -> None:
    root_build=(UI / "build.gradle.kts").read_text(encoding="utf-8")
    app_build=(UI / "app/build.gradle.kts").read_text(encoding="utf-8")
    if 'id("com.android.application") version "9.2.1"' not in root_build:
        raise RuntimeError("UI shell must stay pinned to AGP 9.2.1")
    if 'org.jetbrains.kotlin.android' in root_build or 'org.jetbrains.kotlin.android' in app_build:
        raise RuntimeError("AGP 9 shell must use built-in Kotlin; kotlin-android must not be applied")
    if 'id("org.jetbrains.kotlin.plugin.compose") version "2.2.10"' not in root_build:
        raise RuntimeError("Compose compiler plugin must match AGP 9.2 built-in Kotlin 2.2.10")
    if 'id("org.jetbrains.kotlin.plugin.compose")' not in app_build:
        raise RuntimeError("UI shell app module must apply the Compose compiler plugin")
    if 'compileSdk = 36' not in app_build or 'targetSdk = 36' not in app_build:
        raise RuntimeError("UI shell SDK levels must remain compileSdk/targetSdk 36")
    for dep in (
        'androidx.compose.ui:ui:1.11.4',
        'androidx.compose.foundation:foundation:1.11.4',
        'androidx.compose.animation:animation:1.11.4',
        'androidx.compose.runtime:runtime:1.11.4',
        'androidx.compose.ui:ui-test-junit4:1.11.4',
    ):
        if dep not in app_build:
            raise RuntimeError(f"UI shell must stay aligned to Compose 1.11.4: {dep}")
    if "JvmTarget.JVM_17" not in app_build:
        raise RuntimeError("UI shell Kotlin bytecode target must remain JVM 17")
    if "generateTsunamiSans" not in app_build or 'tasks.named("preBuild")' not in app_build:
        raise RuntimeError("Normal Gradle builds must regenerate TSUNAMI Sans before preBuild")
    bootstrap=(UI / "tools/bootstrap_gradle.sh").read_text(encoding="utf-8")
    if 'GRADLE_VERSION="9.4.1"' not in bootstrap or '2ab2958f2a1e51120c326cad6f385153bb11ee93b3c216c5fccebfdfbb7ec6cb' not in bootstrap:
        raise RuntimeError("Gradle bootstrap must remain pinned to the verified Gradle 9.4.1 binary checksum")
    print("PASS AGP 9.2.1 built-in Kotlin 2.2.10 + Compose compiler 2.2.10 + Compose UI 1.11.4 + JVM 17 + font integration")

def require_visible_source() -> None:
    global JVM_STATE_STATUS
    missing = [rel for rel in REQUIRED_SOURCE if not (UI / rel).is_file()]
    if missing:
        raise RuntimeError("missing visible UI Genesis source: " + ", ".join(missing))
    run(["git", "diff", "--check"], cwd=ROOT)
    run([sys.executable, "tools/source_verify.py"], cwd=UI)
    run([sys.executable, "tools/accessibility_verify.py"], cwd=UI)
    root_gradle = (UI / "build.gradle.kts").read_text(encoding="utf-8")
    app_gradle = (UI / "app/build.gradle.kts").read_text(encoding="utf-8")
    if 'id("org.jetbrains.kotlin.android")' in root_gradle or 'id("org.jetbrains.kotlin.android")' in app_gradle:
        raise RuntimeError("AGP 9 shell must use built-in Kotlin; kotlin-android plugin is incompatible")
    if 'id("com.android.application") version "9.2.1"' not in root_gradle:
        raise RuntimeError("unexpected Android Gradle Plugin version")
    if 'id("org.jetbrains.kotlin.plugin.compose") version "2.2.10"' not in root_gradle:
        raise RuntimeError("Compose compiler plugin must match AGP 9.2 built-in Kotlin line")
    jvm = run(["bash", "tools/jvm_state_gate.sh"], cwd=UI, check=False)
    if jvm.returncode == 0:
        JVM_STATE_STATUS = "PASS"
    elif jvm.returncode == 2 and shutil.which("kotlinc") is None:
        JVM_STATE_STATUS = "SKIP_KOTLINC_UNAVAILABLE"
        print("JVM state gate skipped: kotlinc is unavailable on this runner; Android instrumentation remains mandatory.")
    else:
        raise RuntimeError(f"JVM state gate failed with exit code {jvm.returncode}")
    print(f"PASS visible source files={len(REQUIRED_SOURCE)} ACCESSIBILITY=PASS JVM_STATE={JVM_STATE_STATUS}")


def verify_palette_contrast() -> None:
    source = (UI / "app/src/main/java/com/tsunami/shell/theme/TsunamiTheme.kt").read_text(encoding="utf-8")

    def relative_luminance(rgb: str) -> float:
        values = [int(rgb[i:i+2], 16) / 255 for i in (0, 2, 4)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    def ratio(a: str, b: str) -> float:
        hi, lo = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    for palette_name in ("LightPalette", "DarkPalette"):
        match = re.search(rf"val {palette_name}=TsunamiPalette\((.*?)\)\n", source, re.S)
        if not match:
            raise RuntimeError(f"unable to parse {palette_name}")
        block = match.group(1)
        colors = dict(re.findall(r"(ground|ink|ink2|ink3|selected|possession|danger)=Color\(0xFF([0-9A-Fa-f]{6})\)", block))
        if set(colors) != {"ground", "ink", "ink2", "ink3", "selected", "possession", "danger"}:
            raise RuntimeError(f"incomplete contrast roles in {palette_name}: {sorted(colors)}")
        ground = colors["ground"]
        failures = []
        for role in ("ink", "ink2", "ink3", "selected", "possession", "danger"):
            value = ratio(colors[role], ground)
            if value < 4.5:
                failures.append(f"{role}={value:.2f}:1")
        if failures:
            raise RuntimeError(f"{palette_name} text contrast below 4.5:1: " + ", ".join(failures))
    print("PASS light/dark text-role contrast >= 4.5:1")


def generate_and_build() -> Path:
    REPORT.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "tools/prepare_fonts.py"], cwd=UI)
    generated = sorted((UI / "app/src/main/res/font").glob("tsunami_sans_*.ttf"))
    if len(generated) != 5:
        raise RuntimeError(f"expected five TSUNAMI Sans masters, found {len(generated)}")
    from fontTools.ttLib import TTFont
    required_text = "TSUNAMI Listen Library Find Signal Settings Afterglow 0123456789 · ‑ – — − → … []{}<>^~ × ÷ & ? @ Ææ Œœ Øø Ðð Þþ ß Ññ éüç"
    literal_chars = set(required_text)
    ui_source_root = UI / "app/src/main/java/com/tsunami/shell"
    for source in ui_source_root.rglob("*.kt"):
        source_text = source.read_text(encoding="utf-8")
        for match in re.finditer(r'"(?:\\.|[^"\\])*"', source_text):
            literal_chars.update(ch for ch in match.group(0)[1:-1] if ch not in "\r\n\t")
    expected_weights = {300, 400, 500, 600, 700}
    seen_weights = set()
    for font_path in generated:
        if font_path.stat().st_size < 5_000:
            raise RuntimeError(f"generated font is implausibly small: {font_path.name}")
        font = TTFont(font_path)
        try:
            cmap = {codepoint for table in font["cmap"].tables for codepoint in table.cmap}
            missing = sorted({char for char in literal_chars if ord(char) not in cmap})
            if missing:
                raise RuntimeError(f"{font_path.name} misses rendered/source UI glyphs: {missing}")
            os2=font["OS/2"]
            seen_weights.add(int(os2.usWeightClass))
            if int(os2.sxHeight) != 500 or int(os2.sCapHeight) != 710 or str(os2.achVendID) != "TSNM":
                raise RuntimeError(f"{font_path.name} has inconsistent optical metadata")
            names=font["name"]
            family=next((n.toUnicode() for n in names.names if n.nameID==1), None)
            version=next((n.toUnicode() for n in names.names if n.nameID==5), None)
            if family != "TSUNAMI Sans" or version != "Version 4.800":
                raise RuntimeError(f"{font_path.name} has inconsistent family/version metadata: {family!r} {version!r}")
            glyph_map={cp:g for table in font["cmap"].tables for cp,g in table.cmap.items()}
            glyf=font["glyf"]
            for left,right in (("I","l"),("l","1"),("O","0"),("c","e"),("v","y")):
                a,b=glyph_map[ord(left)],glyph_map[ord(right)]
                ga,gb=glyf[a],glyf[b]
                sig_a=(ga.xMin,ga.yMin,ga.xMax,ga.yMax,len(getattr(ga,"coordinates",[]) or []))
                sig_b=(gb.xMin,gb.yMin,gb.xMax,gb.yMax,len(getattr(gb,"coordinates",[]) or []))
                if sig_a == sig_b:
                    raise RuntimeError(f"{font_path.name} ambiguous control pair collapsed: {left}/{right}")
            if "GPOS" not in font:
                raise RuntimeError(f"{font_path.name} is missing the TSUNAMI Sans kerning feature")
        finally:
            font.close()
    if seen_weights != expected_weights:
        raise RuntimeError(f"unexpected TSUNAMI Sans weight classes: {sorted(seen_weights)}")
    manifest = load_font_manifest()
    expected_font_hashes = manifest_font_hashes(manifest)
    first_font_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in generated}
    if first_font_hashes != expected_font_hashes:
        raise RuntimeError(f"TSUNAMI Sans master hashes drifted: actual={first_font_hashes} expected={expected_font_hashes}")
    for name, meta in manifest["weights"].items():
        path = UI / "app/src/main/res/font" / f"tsunami_sans_{name.lower()}.ttf"
        if path.stat().st_size != int(meta["bytes"]):
            raise RuntimeError(f"{path.name} byte-size drift: {path.stat().st_size} != {meta['bytes']}")
    print("PASS TSUNAMI Sans canonical manifest hashes + byte sizes")
    run([sys.executable, "tools/prepare_fonts.py"], cwd=UI)
    second_font_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in generated}
    if first_font_hashes != second_font_hashes:
        raise RuntimeError(f"TSUNAMI Sans generation is not byte-reproducible: {first_font_hashes} != {second_font_hashes}")
    print("PASS TSUNAMI Sans byte-reproducibility")

    proofs = [
        UI / "tools/proofs/tsunami-sans-proof.png",
        UI / "tools/proofs/tsunami-sans-ui-proof.png",
    ]
    missing_proofs = [p.name for p in proofs if not p.is_file() or p.stat().st_size < 10_000]
    if missing_proofs:
        raise RuntimeError("TSUNAMI Sans proof generation incomplete: " + ", ".join(missing_proofs))
    proof_manifest = manifest.get("proofs", {})
    for proof in proofs:
        meta = proof_manifest.get(proof.name)
        if not meta:
            raise RuntimeError(f"TSUNAMI Sans manifest misses proof: {proof.name}")
        digest = hashlib.sha256(proof.read_bytes()).hexdigest()
        if digest != meta["sha256"] or proof.stat().st_size != int(meta["bytes"]):
            raise RuntimeError(f"TSUNAMI Sans proof drift: {proof.name} sha={digest} bytes={proof.stat().st_size}")
    print("PASS TSUNAMI Sans proof hashes + byte sizes")

    gradle_env = os.environ.copy()
    gradle_env["TSUNAMI_FONT_PYTHON"] = sys.executable
    run(gradle_command(":app:assembleDebug", ":app:assembleDebugAndroidTest", "--console=plain", "--stacktrace"), cwd=UI, env=gradle_env)
    apk = UI / "app/build/outputs/apk/debug/app-debug.apk"
    if not apk.is_file() or apk.stat().st_size == 0:
        raise RuntimeError("UI Genesis APK missing after successful Gradle build")

    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    (REPORT / "apk-sha256.txt").write_text(f"{digest}  {apk.name}\n", encoding="utf-8")
    print(f"PASS shell APK sha256={digest}")
    return apk


def sdk_root() -> Path:
    value = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not value:
        raise RuntimeError("ANDROID_SDK_ROOT/ANDROID_HOME is not set")
    return Path(value)


def sdk_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    sdk = sdk_root()
    candidates = [
        sdk / "cmdline-tools/latest/bin" / name,
        sdk / "emulator" / name,
        sdk / "platform-tools" / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(f"Android SDK tool unavailable: {name}")


def verify_permissions(apk: Path) -> None:
    analyzer = sdk_tool("apkanalyzer")
    cp = run([analyzer, "manifest", "permissions", apk], capture=True)
    text = (cp.stdout or "") + (cp.stderr or "")
    (REPORT / "permissions.txt").write_text(text, encoding="utf-8")
    seen = {line.strip() for line in text.splitlines() if line.strip().startswith("android.permission.")}
    bad = sorted(FORBIDDEN_PERMISSIONS & seen)
    if bad:
        raise RuntimeError("backend-free shell declares forbidden permissions: " + ", ".join(bad))
    print("PASS shell manifest contains no production-facing media/network permissions")


def _attached_emulator(adb: str) -> str | None:
    cp = subprocess.run([adb, "devices"], text=True, capture_output=True)
    for line in cp.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device" and parts[0].startswith("emulator-"):
            boot = subprocess.run([adb, "-s", parts[0], "shell", "getprop", "sys.boot_completed"], text=True, capture_output=True)
            if boot.returncode == 0 and boot.stdout.strip() == "1":
                return parts[0]
    return None


def boot_emulator() -> tuple[subprocess.Popen | None, str]:
    REPORT.mkdir(parents=True, exist_ok=True)
    sdkmanager = sdk_tool("sdkmanager")
    avdmanager = sdk_tool("avdmanager")
    emulator = sdk_tool("emulator")
    adb = sdk_tool("adb")

    existing = _attached_emulator(adb)
    if existing:
        print(f"PASS reusing booted emulator serial={existing}")
        return None, existing

    run([sdkmanager, "emulator", "system-images;android-35;google_apis;x86_64"])
    run([avdmanager, "delete", "avd", "-n", "tsunami-ui-genesis"], check=False)
    run([
        avdmanager, "create", "avd", "-n", "tsunami-ui-genesis",
        "-k", "system-images;android-35;google_apis;x86_64",
        "--device", "pixel_6", "--force",
    ], input_text="no\n")
    config = Path.home() / ".android/avd/tsunami-ui-genesis.avd/config.ini"
    if config.is_file():
        text = config.read_text(encoding="utf-8")
        if re.search(r"^disk\.dataPartition\.size=.*$", text, re.M):
            text = re.sub(r"^disk\.dataPartition\.size=.*$", "disk.dataPartition.size=4G", text, flags=re.M)
        else:
            text += "\ndisk.dataPartition.size=4G\n"
        config.write_text(text, encoding="utf-8")

    log = (REPORT / "emulator.log").open("w", encoding="utf-8")
    proc = subprocess.Popen([
        emulator, "-avd", "tsunami-ui-genesis",
        "-no-window", "-no-audio", "-no-boot-anim",
        "-cores", "2", "-gpu", "host",
        "-no-snapshot", "-wipe-data",
    ], stdout=log, stderr=subprocess.STDOUT, text=True)

    deadline = time.monotonic() + 300
    serial = None
    while time.monotonic() < deadline:
        time.sleep(3)
        serial = _attached_emulator(adb)
        if serial:
            run([adb, "-s", serial, "shell", "input", "keyevent", "82"], check=False)
            run([adb, "-s", serial, "shell", "settings", "put", "global", "window_animation_scale", "0"], check=False)
            run([adb, "-s", serial, "shell", "settings", "put", "global", "transition_animation_scale", "0"], check=False)
            run([adb, "-s", serial, "shell", "settings", "put", "global", "animator_duration_scale", "0"], check=False)
            print(f"PASS emulator booted serial={serial}")
            return proc, serial

    proc.terminate()
    raise RuntimeError("Android emulator did not boot within 300 seconds")


def _install_apk(adb: str, serial: str, apk: Path) -> None:
    remote = f"/data/local/tmp/{apk.name}"
    run([adb, "-s", serial, "push", apk, remote])
    run([adb, "-s", serial, "shell", "pm", "install", "-r", "-t", remote])
    run([adb, "-s", serial, "shell", "rm", "-f", remote], check=False)


def verify_on_emulator(apk: Path) -> None:
    proc, serial = boot_emulator()
    adb = sdk_tool("adb")
    try:
        run([adb, "-s", serial, "shell", "settings", "put", "global", "window_animation_scale", "0"], check=False)
        run([adb, "-s", serial, "shell", "settings", "put", "global", "transition_animation_scale", "0"], check=False)
        run([adb, "-s", serial, "shell", "settings", "put", "global", "animator_duration_scale", "0"], check=False)
        # Preserve ~411x914dp Pixel-6 geometry while cutting instrumentation raster load.
        # capture_verify.sh sets each canonical visual state explicitly afterward.
        run([adb, "-s", serial, "shell", "wm", "size", "720x1600"], check=False)
        run([adb, "-s", serial, "shell", "wm", "density", "280"], check=False)
        test_apk = UI / "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
        if not test_apk.is_file() or test_apk.stat().st_size == 0:
            raise RuntimeError("UI Genesis AndroidTest APK missing after successful Gradle build")
        _install_apk(adb, serial, apk)
        _install_apk(adb, serial, test_apk)
        run([adb, "-s", serial, "logcat", "-c"], check=False)
        cp = subprocess.run([
            adb, "-s", serial, "shell", "am", "instrument", "-w",
            "-e", "class", "com.tsunami.shell.GenesisInteractionTest",
            "com.tsunami.shell.test/androidx.test.runner.AndroidJUnitRunner",
        ], text=True, capture_output=True)
        test_text = (cp.stdout or "") + (cp.stderr or "")
        (REPORT / "instrumentation.txt").write_text(test_text, encoding="utf-8")
        if cp.returncode != 0 or "OK (38 tests)" not in test_text:
            print(test_text[-12_000:])
            raise RuntimeError("UI Genesis instrumentation did not report OK (38 tests)")

        env = os.environ.copy()
        env["ANDROID_SERIAL"] = serial
        env["PATH"] = str(Path(adb).parent) + os.pathsep + env.get("PATH", "")
        env["TSUNAMI_UI_SHELL_APK"] = str(apk)
        run(["bash", "tools/capture_verify.sh"], cwd=UI, env=env)
        run([sys.executable, "tools/derive_review_images.py"], cwd=UI, env=env)
        run([sys.executable, "tools/visual_sanity_verify.py"], cwd=UI, env=env)

        verification = UI / "build/verification"
        base = [
            p for p in verification.glob("*.png")
            if "-mono" not in p.stem and "-squint" not in p.stem and p.stem != "contact-sheet"
        ]
        if len(base) != 45:
            raise RuntimeError(f"visual verification set must contain exactly 45 base states, found {len(base)}")
        if not (verification / "contact-sheet.png").is_file():
            raise RuntimeError("visual verification contact sheet missing")
        logcat = (verification / "logcat-tail.txt").read_text(encoding="utf-8", errors="replace")
        crash_terms = ("FATAL EXCEPTION", "Process: com.tsunami.shell")
        if all(term in logcat for term in crash_terms):
            raise RuntimeError("UI Genesis crash signature found in verification logcat")
        (REPORT / "device.txt").write_text(
            f"SERIAL={serial}\n"
            f"MODEL={subprocess.run([adb, '-s', serial, 'shell', 'getprop', 'ro.product.model'], text=True, capture_output=True).stdout.strip()}\n"
            f"SDK={subprocess.run([adb, '-s', serial, 'shell', 'getprop', 'ro.build.version.sdk'], text=True, capture_output=True).stdout.strip()}\n",
            encoding="utf-8",
        )
        print(f"PASS instrumentation=38 visual states={len(base)} serial={serial}")
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()


def package_evidence(apk: Path) -> Path:
    verification = UI / "build/verification"
    proofs = UI / "tools/proofs"
    REPORT.mkdir(parents=True, exist_ok=True)

    shutil.copy2(apk, REPORT / "TSUNAMI-UI-Genesis-debug.apk")
    review_protocol=ROOT / "docs/TSUNAMI-UI-GENESIS-VISUAL-REVIEW.md"
    if not review_protocol.is_file():
        raise RuntimeError("mandatory visual-review protocol is missing")
    shutil.copy2(review_protocol, REPORT / review_protocol.name)
    for directory, label in ((verification, "visual"), (proofs, "font-proofs")):
        target = REPORT / label
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(directory, target)

    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    (REPORT / "gate.txt").write_text(
        "BUILD_CONFIGURATION=PASS\n"
        "VISIBLE_SOURCE=PASS\n"
        "SOURCE_CONTRACT=PASS\n"
        f"JVM_STATE_BEHAVIOR={JVM_STATE_STATUS}\n"
        "BACKEND_FREE_SOURCE=PASS\n"
        "TEXT_CONTRAST=PASS\n"
        "FONT_GENERATION=PASS\n"
        "FONT_CMAP_WEIGHTS_METADATA_KERNING=PASS\n"
        "FONT_AMBIGUOUS_PAIRS_DISTINCT=PASS\n"
        "FONT_UI_SIZE_PROOF=PASS\n"
        "FONT_REPRODUCIBILITY=PASS\n"
        "FONT_CANONICAL_HASHES=PASS\n"
        "BUILD=PASS\n"
        "INSTRUMENTATION=PASS\n"
        "VISUAL_CAPTURE=PASS\n"
        "VISUAL_SANITY=PASS\n"
        "MONOCHROME_REVIEW_DERIVATION=PASS\n"
        "SQUINT_REVIEW_DERIVATION=PASS\n"
        "CRASH_SCAN=PASS\n"
        "FORBIDDEN_PERMISSION_SCAN=PASS\n"
        f"APK_SHA256={digest}\n",
        encoding="utf-8",
    )

    out = REPORT / "TSUNAMI-UI-Genesis-verification.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(REPORT.rglob("*")):
            if path.is_file() and path != out:
                zf.write(path, path.relative_to(REPORT))
    return out

def main() -> int:
    ensure_tool_python()
    verify_build_configuration()
    require_visible_source()
    verify_palette_contrast()
    apk = generate_and_build()
    verify_permissions(apk)
    verify_on_emulator(apk)
    package_evidence(apk)
    print("UI_SHELL_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
