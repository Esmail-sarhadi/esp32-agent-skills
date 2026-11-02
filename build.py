#!/usr/bin/env python3
"""Build the release artifacts for the platform you are on.

Two shapes come out of here:

- `dist/esp32-skills.pyz`, a single file that runs on any Python 3.8 or newer
  with no installation. This is the one to keep in a repository or copy to a
  machine that already has Python.
- `dist/esp32-skills` (or `esp32-skills.exe` on Windows), a real executable built
  with PyInstaller, for machines that do not have Python at all.

PyInstaller cannot cross-compile: a Windows executable has to be built on
Windows and a Linux binary on Linux. That is why `.github/workflows/release.yml`
runs the same script on both, and why running this locally only produces the
artifact for the machine you are sitting at.

Usage:
    python build.py                # zipapp + native executable
    python build.py --zipapp-only  # skip PyInstaller
    python build.py --clean        # remove dist/ and build/ first
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipapp

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "build")
STAGE = os.path.join(BUILD, "stage")

MODULES = [
    "pincheck",
    "partition_check",
    "power_budget",
    "panic_decode",
    "airtime",
    "modbus_map_check",
    "modbus_frame",
    "mqtt_topic_check",
    "flash_layout",
    "i2c_address_check",
    "esp32_skills_cli",
]

MAIN = """import sys
from esp32_skills_cli import main

if __name__ == "__main__":
    sys.exit(main())
"""


def clean() -> None:
    for path in (DIST, BUILD):
        if os.path.isdir(path):
            shutil.rmtree(path)


def build_zipapp() -> str:
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)

    for module in MODULES:
        shutil.copy2(os.path.join(TOOLS, module + ".py"), os.path.join(STAGE, module + ".py"))

    # pincheck reads data/esp32-pins.json; without it the zipapp starts and then
    # fails on the first pin, which is worse than not shipping it.
    data_dir = os.path.join(STAGE, "data")
    os.makedirs(data_dir, exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "data", "esp32-pins.json"),
                 os.path.join(data_dir, "esp32-pins.json"))

    with open(os.path.join(STAGE, "__main__.py"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(MAIN)

    os.makedirs(DIST, exist_ok=True)
    target = os.path.join(DIST, "esp32-skills.pyz")
    zipapp.create_archive(STAGE, target, interpreter="/usr/bin/env python3", compressed=True)
    return target


def build_executable() -> str:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed; skipping the native executable.")
        print("  python -m pip install pyinstaller")
        return ""

    entry = os.path.join(STAGE, "entry.py")
    with open(entry, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(MAIN)

    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name", "esp32-skills",
        "--distpath", DIST,
        "--workpath", os.path.join(BUILD, "pyinstaller"),
        "--specpath", BUILD,
        "--paths", TOOLS,
        "--paths", STAGE,
        "--add-data", os.path.join(ROOT, "data", "esp32-pins.json") + os.pathsep + "data",
        entry,
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    suffix = ".exe" if os.name == "nt" else ""
    return os.path.join(DIST, "esp32-skills" + suffix)


def smoke(path: str) -> bool:
    """Run the artifact once. A build that does not start is not a build."""
    if not path:
        return False
    if path.endswith(".pyz"):
        command = [sys.executable, path, "--list"]
    else:
        command = [path, "--list"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    ok = result.returncode == 0 and "pincheck" in result.stdout

    # --list only proves the binary starts. Run a real command too, because a
    # dynamically imported module is exactly the thing PyInstaller can miss.
    if ok:
        real = command[:-1] + ["airtime", "--sf", "7", "--payload", "13"]
        second = subprocess.run(real, capture_output=True, text=True, check=False)
        ok = second.returncode == 0 and "46.336" in second.stdout
        if not ok:
            result = second

    print("  smoke %s: %s" % (os.path.basename(path), "ok" if ok else "FAILED"))
    if not ok:
        print(result.stdout)
        print(result.stderr)
    return ok


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the esp32-skills artifacts.")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--zipapp-only", action="store_true")
    args = parser.parse_args(argv)

    if args.clean:
        clean()

    print("platform: %s %s" % (sys.platform, sys.version.split()[0]))
    archive = build_zipapp()
    print("  wrote %s (%d KB)" % (archive, os.path.getsize(archive) // 1024))
    smoke(archive)

    if not args.zipapp_only:
        binary = build_executable()
        if binary:
            print("  wrote %s (%d KB)" % (binary, os.path.getsize(binary) // 1024))
            smoke(binary)

    print("")
    print("dist/ is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
