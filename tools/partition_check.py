#!/usr/bin/env python3
"""Validate an ESP32 partition table before it bricks a board.

A partition table is the one file where a wrong number produces a device that
flashes "successfully" and then boot-loops with no readable error. This checks
the things that actually go wrong: overlapping regions, a misaligned app
partition, an app that does not fit, and an OTA setup with only one slot.

Usage:
    python tools/partition_check.py --file examples/partitions.csv --flash 4MB --ota
    python tools/partition_check.py --file partitions.csv --json

Exit code is 1 when at least one error is found, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Dict, List, Optional, Tuple

ERROR = "error"
WARN = "warn"
INFO = "info"

# The bootloader lives at 0x1000 and the partition table itself at 0x8000.
BOOTLOADER_END = 0x8000
PARTITION_TABLE_END = 0x9000
APP_ALIGN = 0x10000

SIZE_RE = re.compile(r"^\s*(0x[0-9a-fA-F]+|\d+)\s*([kKmM]?)[bB]?\s*$")


def parse_size(text: str) -> int:
    match = SIZE_RE.match(text or "")
    if not match:
        raise ValueError("cannot read size %r, expected 0x10000, 65536, 64K, 1M or 4MB" % text)
    value = int(match.group(1), 0)
    suffix = match.group(2).lower()
    if suffix == "k":
        value *= 1024
    elif suffix == "m":
        value *= 1024 * 1024
    return value


def human(value: int) -> str:
    if value >= 1024 * 1024 and value % (1024 * 1024) == 0:
        return "%dMB" % (value // (1024 * 1024))
    if value >= 1024 and value % 1024 == 0:
        return "%dKB" % (value // 1024)
    return "0x%X" % value


def parse_table(path: str) -> List[dict]:
    rows: List[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            fields = [f.strip() for f in line.split(",")]
            if fields[0].lower() == "name":
                continue
            if len(fields) < 5:
                raise ValueError("line %d: expected Name,Type,SubType,Offset,Size" % lineno)
            name, ptype, subtype, offset, size = fields[:5]
            rows.append({
                "name": name,
                "type": ptype.lower(),
                "subtype": subtype.lower(),
                "offset": parse_size(offset) if offset else None,
                "size": parse_size(size),
                "line": lineno,
            })
    return rows


def resolve_offsets(rows: List[dict]) -> None:
    """Fill in omitted offsets the same way gen_esp32part.py does: append, 4K aligned."""
    cursor = PARTITION_TABLE_END
    for row in rows:
        if row["offset"] is None:
            cursor = (cursor + 0xFFF) & ~0xFFF
            row["offset"] = cursor
        cursor = row["offset"] + row["size"]


def check(rows: List[dict], flash: int, ota: bool) -> Tuple[List[dict], List[Tuple[str, str]], int]:
    findings: List[Tuple[str, str]] = []
    errors = 0

    ordered = sorted(rows, key=lambda r: r["offset"])

    for row in ordered:
        if row["offset"] < PARTITION_TABLE_END:
            findings.append((ERROR, "%s starts at %s, inside the bootloader or the partition table "
                                    "itself (must be >= 0x9000)"
                             % (row["name"], human(row["offset"]))))
        end = row["offset"] + row["size"]
        if end > flash:
            findings.append((ERROR, "%s ends at %s, past the end of %s of flash"
                             % (row["name"], human(end), human(flash))))
        if row["size"] <= 0:
            findings.append((ERROR, "%s has a zero size" % row["name"]))
        if row["type"] == "app" and row["offset"] % APP_ALIGN != 0:
            findings.append((ERROR, "%s is an app partition at %s, app partitions must be aligned "
                                    "to 0x10000" % (row["name"], human(row["offset"]))))

    for previous, current in zip(ordered, ordered[1:]):
        prev_end = previous["offset"] + previous["size"]
        if current["offset"] < prev_end:
            findings.append((ERROR, "%s (%s-%s) overlaps %s (%s-%s)"
                             % (previous["name"], human(previous["offset"]), human(prev_end),
                                current["name"], human(current["offset"]),
                                human(current["offset"] + current["size"]))))

    names = {r["name"].lower() for r in rows}
    apps = [r for r in rows if r["type"] == "app" and r["subtype"].startswith("ota")]
    factory = [r for r in rows if r["type"] == "app" and r["subtype"] == "factory"]

    if ota:
        if "otadata" not in names:
            findings.append((ERROR, "OTA is enabled but there is no otadata partition"))
        if len(apps) < 2:
            findings.append((ERROR, "OTA is enabled but there are %d ota app slots, two are "
                                    "required so an update can be written while the other runs"
                             % len(apps)))
        elif len({r["size"] for r in apps}) > 1:
            findings.append((ERROR, "the ota app slots do not have the same size, ota_0 and "
                                    "ota_1 must match"))
        if factory and factory[0]["size"] < max((r["size"] for r in apps), default=0):
            findings.append((WARN, "the factory partition is smaller than an ota slot, a build "
                                   "that fits ota_0 will not fit factory"))
    else:
        if len(apps) + len(factory) == 0:
            findings.append((ERROR, "no app partition at all"))
        if apps and not factory:
            findings.append((INFO, "only ota app slots, the first boot goes to ota_0"))
        if "otadata" in names:
            findings.append((INFO, "otadata present but --ota was not passed, the second slot "
                                   "will not be used"))

    if "nvs" not in names:
        findings.append((WARN, "no nvs partition, Wi-Fi calibration and Preferences have "
                               "nowhere to live"))

    used = sum(r["size"] for r in rows)
    if used <= flash:
        findings.append((INFO, "%s of %s used (%.1f%%), %s free"
                         % (human(used), human(flash), 100.0 * used / flash,
                            human(flash - used))))
    else:
        findings.append((INFO, "%s of %s used, %s over budget"
                         % (human(used), human(flash), human(used - flash))))

    for severity, _ in findings:
        if severity == ERROR:
            errors += 1

    report = []
    for row in ordered:
        report.append({
            "name": row["name"],
            "type": row["type"],
            "subtype": row["subtype"],
            "offset": row["offset"],
            "size": row["size"],
        })
    return report, findings, errors


def print_report(report: List[dict], findings: List[Tuple[str, str]]) -> None:
    print("%-14s %-6s %-10s %-10s %-10s" % ("NAME", "TYPE", "SUBTYPE", "OFFSET", "SIZE"))
    for row in report:
        print("%-14s %-6s %-10s 0x%-8X %-10s"
              % (row["name"], row["type"], row["subtype"], row["offset"], human(row["size"])))

    order = {ERROR: 0, WARN: 1, INFO: 2}
    print("")
    for severity, message in sorted(findings, key=lambda f: order[f[0]]):
        print("  %-5s %s" % (severity.upper(), message))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an ESP32 partition table.")
    parser.add_argument("--file", required=True, help="partition table in CSV format")
    parser.add_argument("--flash", default="4MB", help="flash size, e.g. 4MB, 8MB, 0x400000")
    parser.add_argument("--ota", action="store_true", help="require a valid OTA layout")
    parser.add_argument("--json", action="store_true", help="machine readable output")
    args = parser.parse_args(argv)

    try:
        flash = parse_size(args.flash)
        rows = parse_table(args.file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if not rows:
        parser.error("the partition table is empty")

    resolve_offsets(rows)
    report, findings, errors = check(rows, flash, args.ota)

    if args.json:
        print(json.dumps({
            "flash": flash,
            "errors": errors,
            "partitions": report,
            "findings": [{"severity": s, "message": m} for s, m in findings],
        }, indent=2))
    else:
        print_report(report, findings)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
