#!/usr/bin/env python3
"""Check the layout of a set of images written to flash.

`esptool merge_bin` happily produces a file with two images at the same offset,
and the board then boots the wrong one or nothing at all. This tool takes the
same offset:file pairs and answers the questions that matter before flashing:

- Do any two images overlap?
- Does the total run past the end of the flash?
- Is the bootloader at 0x1000, the partition table at 0x8000 and the app at
  0x10000 (the classic ESP32 layout, and the one every guide assumes)?
- Is the partition table where the bootloader looks for it, and is it aligned?

It reads the files for their size only; it does not parse them.

Usage:
    python tools/flash_layout.py --flash 4MB \\
        0x1000 build/bootloader.bin 0x8000 build/partitions.bin 0x10000 build/app.bin
    python tools/flash_layout.py --flash 8MB --json 0x0 build/merged.bin
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

BOOTLOADER_OFFSET = 0x1000
PARTITION_OFFSET = 0x8000
APP_OFFSET = 0x10000
SECTOR = 0x1000


def parse_size(text: str) -> int:
    """'4MB', '4M', '4096K', '0x400000' or a plain byte count."""
    value = text.strip().lower()
    if value.startswith("0x"):
        return int(value, 16)
    multiplier = 1
    for suffix, factor in (("mb", 1024 * 1024), ("kb", 1024), ("m", 1024 * 1024), ("k", 1024)):
        if value.endswith(suffix):
            multiplier = factor
            value = value[: -len(suffix)]
            break
    return int(float(value) * multiplier)


def human(value: int) -> str:
    if value >= 1024 * 1024:
        return "%.1fMB" % (value / (1024 * 1024))
    if value >= 1024:
        return "%dKB" % (value // 1024)
    return "%d bytes" % value


def layout(entries, flash: int) -> dict:
    """entries: list of (offset, path, size). Returns a report and problems."""
    problems = []
    notes = []
    images = []

    for offset, path, size in entries:
        if offset < 0:
            problems.append("%s has a negative offset" % path)
        if size <= 0:
            problems.append("%s is empty" % path)
        images.append({"offset": offset, "path": path, "size": size,
                       "end": offset + size})

    images.sort(key=lambda item: item["offset"])

    for previous, current in zip(images, images[1:]):
        if current["offset"] < previous["end"]:
            problems.append("%s (0x%X-0x%X) overlaps %s at 0x%X"
                            % (previous["path"], previous["offset"], previous["end"],
                               current["path"], current["offset"]))

    if images:
        end = max(item["end"] for item in images)
        if end > flash:
            problems.append("the images end at %s, past the end of %s of flash"
                            % (human(end), human(flash)))
        top = images[0]
        if top["offset"] == 0:
            notes.append("a single image at 0x0 is a merged binary: it contains the "
                         "bootloader and the partition table, so the layout checks are skipped")
        else:
            offsets = {item["offset"] for item in images}
            if BOOTLOADER_OFFSET not in offsets:
                problems.append("no image at 0x1000: the classic ESP32 bootloader offset")
            if PARTITION_OFFSET not in offsets:
                problems.append("no image at 0x8000: the partition table offset")
            elif APP_OFFSET not in offsets:
                notes.append("no image at 0x10000; if the app offset differs, it must "
                             "match the partition table, not this default")

        for item in images:
            if item["offset"] % SECTOR:
                notes.append("%s starts at 0x%X, not on a 4KB sector boundary"
                             % (item["path"], item["offset"]))

    return {
        "flash": flash,
        "images": images,
        "used": max((item["end"] for item in images), default=0),
        "ok": not problems,
        "problems": problems,
        "notes": notes,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Check a flash layout before merging or flashing.")
    parser.add_argument("--flash", default="4MB", help="flash size, e.g. 4MB or 0x400000")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("pairs", nargs="+", metavar="OFFSET:FILE",
                        help="offset and file, alternating: 0x1000 boot.bin 0x8000 part.bin")
    args = parser.parse_args(argv)

    if len(args.pairs) % 2:
        parser.error("give an offset and a file for each image: 0x1000 bootloader.bin ...")

    entries = []
    for index in range(0, len(args.pairs), 2):
        raw_offset, path = args.pairs[index], args.pairs[index + 1]
        try:
            offset = int(raw_offset, 0)
        except ValueError:
            parser.error("cannot read offset %r" % raw_offset)
        if not os.path.isfile(path):
            parser.error("no such file: %s" % path)
        entries.append((offset, path, os.path.getsize(path)))

    try:
        flash = parse_size(args.flash)
    except ValueError:
        parser.error("cannot read flash size %r" % args.flash)

    report = layout(entries, flash)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    print("%s of flash" % human(flash))
    print("")
    for item in report["images"]:
        print("  0x%06X  %8s  %s" % (item["offset"], human(item["size"]), item["path"]))
    print("")
    print("  ends at   %s (%.1f%% of the flash)"
          % (human(report["used"]), 100.0 * report["used"] / flash if flash else 0.0))
    for problem in report["problems"]:
        print("  ERROR  %s" % problem)
    for note in report["notes"]:
        print("  note   %s" % note)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
