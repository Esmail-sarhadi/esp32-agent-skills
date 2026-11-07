#!/usr/bin/env python3
"""Turn an ESP32 panic dump into an addr2line command.

The serial output after a crash is a wall of hex. The useful part is the
backtrace, and the only way to read it is to feed the addresses to addr2line
with the exact ELF that was flashed. Doing that by hand is where people
copy the wrong addresses or lose the frame that matters.

This extracts the addresses, keeps the order the CPU printed them (frame 0 is
the innermost), and emits the command ready to paste.

Usage:
    python tools/panic_decode.py --file crash.txt
    python tools/panic_decode.py --file crash.txt --elf .pio/build/esp32dev/firmware.elf
    cat crash.txt | python tools/panic_decode.py

The output is a report, not a decoded trace: decoding needs the toolchain that
built the firmware, which this script deliberately does not assume.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import List, Optional

PANIC_RE = re.compile(r"(Guru Meditation Error|panic'ed|abort\(\) was called)[^\n]*")
REASON_RE = re.compile(r"panic'ed \(([^)]+)\)")
CORE_RE = re.compile(r"Core\s+(\d)")
PC_RE = re.compile(r"^PC\s*:\s*(0x[0-9a-fA-F]{8})", re.MULTILINE)
EXCVADDR_RE = re.compile(r"EXCVADDR\s*[:=]\s*(0x[0-9a-fA-F]+)")
BACKTRACE_RE = re.compile(r"Backtrace:\s*([0-9a-fA-Fx:\s]+)")
ADDR_RE = re.compile(r"0x[0-9a-fA-F]{8}")

REASON_HINTS = {
    "LoadProhibited": "a read through a bad pointer - null, freed, or out of bounds",
    "StoreProhibited": "a write through a bad pointer - often a buffer overrun",
    "IllegalInstruction": "execution reached data, usually a corrupted function pointer",
    "IntegerDivideByZero": "a division by zero",
    "InstrFetchProhibited": "the CPU jumped to an address that is not code",
    "Unhandled debug exception": "a breakpoint or a watchpoint fired",
}


def parse(text: str) -> dict:
    reason_match = REASON_RE.search(text)
    core_match = CORE_RE.search(text)
    pc_match = PC_RE.search(text)
    excvaddr_match = EXCVADDR_RE.search(text)

    frames: List[str] = []
    bt_match = BACKTRACE_RE.search(text)
    if bt_match:
        for token in bt_match.group(1).split():
            addresses = ADDR_RE.findall(token)
            if addresses:
                frames.append(addresses[0].lower())

    if not frames and pc_match:
        frames = [pc_match.group(1).lower()]

    reason = reason_match.group(1) if reason_match else None
    return {
        "reason": reason,
        "hint": REASON_HINTS.get(reason or "", None),
        "core": int(core_match.group(1)) if core_match else None,
        "pc": pc_match.group(1).lower() if pc_match else None,
        "excvaddr": excvaddr_match.group(1).lower() if excvaddr_match else None,
        "frames": frames,
        "is_panic": bool(reason or PANIC_RE.search(text)),
    }


def addr2line_command(frames: List[str], elf: str, tool: str) -> str:
    return "%s -pfiaC -e %s %s" % (tool, elf, " ".join(frames))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Decode an ESP32 panic dump into an addr2line command.")
    parser.add_argument("--file", help="file with the serial output, omit to read stdin")
    parser.add_argument("--elf", default="firmware.elf", help="ELF that was flashed")
    parser.add_argument("--tool", default="xtensa-esp32-elf-addr2line",
                        help="addr2line binary for your toolchain")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as exc:
            parser.error(str(exc))
    else:
        text = sys.stdin.read()

    result = parse(text)
    command = addr2line_command(result["frames"], args.elf, args.tool) if result["frames"] else None
    result["command"] = command

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["is_panic"] else 1

    if not result["is_panic"]:
        print("no panic found in the input")
        return 1

    print("panic      %s" % (result["reason"] or "unknown"))
    if result["hint"]:
        print("meaning    %s" % result["hint"])
    if result["core"] is not None:
        print("core       %d" % result["core"])
    if result["excvaddr"]:
        print("address    %s  <- the pointer that was dereferenced" % result["excvaddr"])
    print("frames     %d" % len(result["frames"]))
    for index, frame in enumerate(result["frames"]):
        print("  [%d] %s" % (index, frame))

    if command:
        print("")
        print("run this with the ELF that was flashed:")
        print("  %s" % command)
        print("")
        print("frame 0 is the innermost call, it is the one to read first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
