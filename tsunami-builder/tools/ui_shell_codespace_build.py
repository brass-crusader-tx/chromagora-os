#!/usr/bin/env python3
"""Build the isolated TSUNAMI UI Genesis shell through the repository's GitHub Codespace.

This is a fallback for environments where GitHub-hosted Actions cannot start. It deliberately does
not touch the production Android graph: the snapshot is unpacked into a throwaway directory inside
TSUNAMI Builder and Gradle runs from ui-shell/. The resulting APK is copied back with a SHA-256
manifest; optional ADB installation targets an explicitly named device serial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = "brass-crusader-tx/TSUNAMI"
DISPLAY_NAME = "TSUNAMI Builder"
REMOTE_ROOT = "/workspaces/.tsunami-ui-genesis"
OUT = ROOT / "dist"


class BuildError(RuntimeError):
    pass


def command(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        raise BuildError(f"required command unavailable: {name}")
    return exe


def run(cmd: list[str], *, capture: bool = False, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(shlex.quote(str(x)) for x in cmd), flush=True)
    cp = subprocess.run(list(map(str, cmd)), cwd=ROOT, text=True, capture_output=capture, env=env)
    if check and cp.returncode:
        tail = ((cp.stdout or "") + (cp.stderr or ""))[-8000:]
        raise BuildError(f"command failed ({cp.returncode}): {' '.join(map(str, cmd))}\n{tail}")
    return cp


def codespaces() -> list[dict]:
    cp = run([
        command("gh"), "codespace", "list", "-R", REPO,
        "--json", "name,displayName,state,lastUsedAt",
    ], capture=True)
    return json.loads(cp.stdout or "[]")


def ensure_builder() -> str:
    rows = codespaces()
    row = next((r for r in rows if r.get("displayName") == DISPLAY_NAME), None)
    if row:
        return str(row["name"])
    run([
        command("gh"), "codespace", "create", "-R", REPO, "-b", "main",
        "-d", DISPLAY_NAME, "-m", "basicLinux32gb",
        "--idle-timeout", "30m", "--retention-period", "720h",
        "--default-permissions", "--status",
    ])
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        time.sleep(3)
        row = next((r for r in codespaces() if r.get("displayName") == DISPLAY_NAME), None)
        if row:
            return str(row["name"])
    raise BuildError("TSUNAMI Builder was not discoverable after Codespace creation")


def remote(name: str, shell: str, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return run([command("gh"), "codespace", "ssh", "-c", name, shell], capture=capture)


def cp_to(name: str, source: Path, remote_path: str) -> None:
    run([command("gh"), "codespace", "cp", "-c", name, str(source), f"remote:{remote_path}"])


def cp_from(name: str, remote_path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run([command("gh"), "codespace", "cp", "-c", name, f"remote:{remote_path}", str(dest)])


def one_physical_device() -> str:
    adb = command("adb")
    cp = run([adb, "devices", "-l"], capture=True)
    serials = []
    for line in cp.stdout.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 2 or fields[1] != "device":
            continue
        serial = fields[0]
        if serial.startswith("emulator-"):
            continue
        serials.append(serial)
    if len(serials) != 1:
        raise BuildError(f"--auto-device requires exactly one connected physical Android device; found {len(serials)}")
    return serials[0]


def review_python() -> str:
    """Return a small local Python environment with Pillow for derived visual evidence."""
    cache = ROOT / "build" / ".ui-shell-toolchain" / "codespace-review-venv"
    py = cache / "bin" / "python"
    if not py.is_file():
        host = os.environ.get("PYTHON", "python3")
        run([host, "-m", "venv", str(cache)])
        run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--quiet", "pillow==12.3.0"])
    else:
        probe = run([str(py), "-c", "import PIL"], check=False, capture=True)
        if probe.returncode:
            run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--quiet", "pillow==12.3.0"])
    return str(py)


def snapshot() -> Path:
    run([os.environ.get("PYTHON", "python3"), "tools/ui_shell_static_check.py"])
    td = Path(tempfile.mkdtemp(prefix="tsunami-ui-genesis-snapshot-"))
    archive = td / "snapshot.tar.gz"
    tracked = run(["git", "ls-files", "-z"], capture=True).stdout.split("\0")
    wanted = [
        p for p in tracked
        if p and (
            p.startswith("ui-shell/")
            or p.startswith("brand/")
            or p.startswith("docs/TSUNAMI-UI-GENESIS-")
            or p in {"tools/ui_shell_gate.py", "tools/ui_shell_static_check.py"}
        )
    ]
    if not wanted:
        raise BuildError("no UI Genesis source selected for snapshot")
    with tarfile.open(archive, "w:gz", compresslevel=1) as tf:
        for rel in sorted(wanted):
            path = ROOT / rel
            if path.is_file():
                tf.add(path, arcname=rel)
    return archive


def build(serial: str | None, capture_matrix: bool, instrument: bool) -> dict:
    name = ensure_builder()
    archive = snapshot()
    snapshot_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    source_dirty = bool(run([
        "git", "status", "--porcelain", "--untracked-files=all", "--",
        "ui-shell", "brand", "docs", "tools/ui_shell_gate.py", "tools/ui_shell_static_check.py", "tools/ui_shell_codespace_build.py",
    ], capture=True).stdout.strip())
    build_id = f"ui-genesis-{int(time.time())}-{os.getpid()}"
    remote_archive = f"{REMOTE_ROOT}/{build_id}.tar.gz"
    remote_work = f"{REMOTE_ROOT}/{build_id}"
    remote_apk = f"{remote_work}/ui-shell/app/build/outputs/apk/debug/app-debug.apk"
    remote_test_apk = f"{remote_work}/ui-shell/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
    try:
        remote(name, f"mkdir -p {shlex.quote(REMOTE_ROOT)}")
        cp_to(name, archive, remote_archive)
        shell = " && ".join([
            f"rm -rf {shlex.quote(remote_work)}",
            f"mkdir -p {shlex.quote(remote_work)}",
            f"SNAPSHOT_SHA=$(sha256sum {shlex.quote(remote_archive)} | awk '{{print $1}}') && printf 'SNAPSHOT_SHA=%s\\n' \"$SNAPSHOT_SHA\"",
            f"tar -xzf {shlex.quote(remote_archive)} -C {shlex.quote(remote_work)}",
            "test -f /workspaces/.tsunami-codespace/env.sh || bash /workspaces/TSUNAMI/.devcontainer/bootstrap-codespace.sh",
            f"source /workspaces/.tsunami-codespace/env.sh",
            f"cd {shlex.quote(remote_work)}/ui-shell",
            "python3 -m pip install --user --disable-pip-version-check fonttools==4.63.0 shapely==2.1.2 pillow==12.3.0",
            "python3 tools/source_verify.py",
            "python3 tools/accessibility_verify.py",
            "python3 tools/prepare_fonts.py",
            "bash tools/bootstrap_gradle.sh --version | grep -q 'Gradle 9.4.1'",
            "bash tools/bootstrap_gradle.sh :app:assembleDebug :app:assembleDebugAndroidTest --console=plain --stacktrace",
            "test -s app/build/outputs/apk/debug/app-debug.apk",
            "test -s app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
            "APP_SHA=$(sha256sum app/build/outputs/apk/debug/app-debug.apk | awk '{print $1}') && printf 'APP_SHA=%s\\n' \"$APP_SHA\"",
            "TEST_SHA=$(sha256sum app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk | awk '{print $1}') && printf 'TEST_SHA=%s\\n' \"$TEST_SHA\"",
        ])
        remote_result = remote(name, shell, capture=True)
        print(remote_result.stdout, end="")
        def marker(prefix: str) -> str:
            for line in reversed(remote_result.stdout.splitlines()):
                if line.startswith(prefix):
                    value=line.split("=",1)[1].strip().lower()
                    if len(value)==64 and all(ch in "0123456789abcdef" for ch in value):
                        return value
            raise BuildError(f"remote build did not emit {prefix} SHA-256")

        remote_snapshot_digest = marker("SNAPSHOT_SHA=")
        remote_digest = marker("APP_SHA=")
        remote_test_digest = marker("TEST_SHA=")
        if remote_snapshot_digest != snapshot_digest:
            raise BuildError(f"Codespace snapshot hash mismatch: {remote_snapshot_digest} != {snapshot_digest}")
        OUT.mkdir(parents=True, exist_ok=True)
        apk = OUT / "TSUNAMI-UI-Genesis-debug.apk"
        test_apk = OUT / "TSUNAMI-UI-Genesis-debug-androidTest.apk"
        cp_from(name, remote_apk, apk)
        cp_from(name, remote_test_apk, test_apk)
        digest = hashlib.sha256(apk.read_bytes()).hexdigest()
        test_digest = hashlib.sha256(test_apk.read_bytes()).hexdigest()
        if digest != remote_digest:
            raise BuildError(f"Codespace/local APK hash mismatch: {remote_digest} != {digest}")
        if test_digest != remote_test_digest:
            raise BuildError(f"Codespace/local test APK hash mismatch: {remote_test_digest} != {test_digest}")
        evidence = {
            "status": "BUILT",
            "backend": "github-codespaces",
            "codespace": name,
            "branch": run(["git", "branch", "--show-current"], capture=True).stdout.strip(),
            "commit": run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip(),
            "source_dirty": source_dirty,
            "snapshot_sha256": snapshot_digest,
            "remote_snapshot_sha256": remote_snapshot_digest,
            "snapshot_hash_match": True,
            "apk": str(apk.relative_to(ROOT)),
            "canonical_dist": str(OUT.relative_to(ROOT)),
            "bytes": apk.stat().st_size,
            "sha256": digest,
            "remote_sha256": remote_digest,
            "hash_match": True,
            "test_apk": str(test_apk.relative_to(ROOT)),
            "test_apk_bytes": test_apk.stat().st_size,
            "test_apk_sha256": test_digest,
            "remote_test_apk_sha256": remote_test_digest,
            "test_apk_hash_match": True,
            "remote_source_verify": "PASS",
            "remote_accessibility_verify": "PASS",
            "remote_gradle": "9.4.1",
        }
        if serial:
            adb = command("adb")
            run([adb, "-s", serial, "install", "-r", str(apk)])
            run([adb, "-s", serial, "shell", "am", "force-stop", "com.tsunami.shell"])
            launch = run([
                adb, "-s", serial, "shell", "am", "start", "-W",
                "-n", "com.tsunami.shell/.MainActivity",
            ], capture=True)
            evidence["device_serial"] = serial
            evidence["install"] = "PASS"
            evidence["launch_output"] = launch.stdout.strip()
            if instrument or capture_matrix:
                run([adb, "-s", serial, "install", "-r", str(test_apk)])
                instrumentation = run([
                    adb, "-s", serial, "shell", "am", "instrument", "-w",
                    "com.tsunami.shell.test/androidx.test.runner.AndroidJUnitRunner",
                ], capture=True)
                evidence["instrumentation_output"] = instrumentation.stdout.strip()
                if "OK (" not in instrumentation.stdout:
                    raise BuildError("physical-device instrumentation did not report OK")
                evidence["instrumentation"] = "PASS"
                instrumentation_path = OUT / "TSUNAMI-UI-Genesis-instrumentation.txt"
                instrumentation_path.write_text(instrumentation.stdout, encoding="utf-8")
                evidence["instrumentation_evidence"] = str(instrumentation_path.relative_to(ROOT))
            if capture_matrix:
                env = dict(os.environ)
                env["ANDROID_SERIAL"] = serial
                env["TSUNAMI_UI_SHELL_APK"] = str(apk)
                run(["bash", "ui-shell/tools/capture_verify.sh"], env=env)
                verification = ROOT / "ui-shell" / "build" / "verification"
                base_captures = sorted(
                    p for p in verification.glob("[0-9][0-9]-*.png")
                    if "-mono" not in p.stem and "-squint" not in p.stem
                )
                evidence["device_capture_count"] = len(base_captures)
                if len(base_captures) != 45:
                    raise BuildError(f"device visual matrix incomplete: {len(base_captures)} base captures")
                logcat = verification / "logcat-tail.txt"
                if logcat.is_file():
                    text_log = logcat.read_text(encoding="utf-8", errors="replace")
                    if "FATAL EXCEPTION" in text_log and "com.tsunami.shell" in text_log:
                        raise BuildError("device review found TSUNAMI shell fatal exception")

                py = review_python()
                run([py, "ui-shell/tools/derive_review_images.py"])
                sanity = run([py, "ui-shell/tools/visual_sanity_verify.py"], capture=True)
                evidence["visual_sanity_output"] = sanity.stdout.strip()
                if "VISUAL_SANITY=PASS" not in sanity.stdout:
                    raise BuildError("visual sanity verifier did not report PASS")
                contact_sheet = verification / "contact-sheet.png"
                if not contact_sheet.is_file() or contact_sheet.stat().st_size < 10_000:
                    raise BuildError("device review contact sheet missing or implausibly small")

                review_base = OUT / "TSUNAMI-UI-Genesis-device-review"
                archive = Path(shutil.make_archive(str(review_base), "zip", root_dir=verification))
                review_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
                evidence["device_review"] = "PASS"
                evidence["visual_sanity"] = "PASS"
                evidence["contact_sheet"] = str(contact_sheet.relative_to(ROOT))
                evidence["device_review_archive"] = str(archive.relative_to(ROOT))
                evidence["device_review_archive_sha256"] = review_digest
        report = OUT / "codespace-build.json"
        report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))
        return evidence
    finally:
        shutil.rmtree(archive.parent, ignore_errors=True)
        try:
            remote(name, f"rm -rf {shlex.quote(remote_work)} {shlex.quote(remote_archive)}", capture=True)
        except Exception as cleanup_error:
            print(f"warning: remote cleanup failed: {cleanup_error}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    device = ap.add_mutually_exclusive_group()
    device.add_argument("--serial", help="explicit ADB serial to install/launch after build")
    device.add_argument("--auto-device", action="store_true", help="use the only connected non-emulator Android device")
    ap.add_argument("--capture-matrix", action="store_true", help="capture the full visual QA matrix after install")
    ap.add_argument("--instrument", action="store_true", help="install the AndroidTest APK and run Compose instrumentation")
    args = ap.parse_args()
    serial = one_physical_device() if args.auto_device else args.serial
    if (args.capture_matrix or args.instrument) and not serial:
        ap.error("--capture-matrix/--instrument requires --serial or --auto-device")
    try:
        build(serial, args.capture_matrix, args.instrument)
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
