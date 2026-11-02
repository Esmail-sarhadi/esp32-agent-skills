#!/usr/bin/env python3
"""Check MQTT topic names against the rules in the specification.

Topic bugs are silent: the broker accepts a publish to `a/+/b` (it should not),
the subscriber never matches it, and nothing anywhere reports an error. This
tool applies the rules from MQTT 3.1.1 section 4.7 and the Sparkplug B namespace
so a topic scheme can be checked before it is baked into firmware.

Rules enforced:

- A topic is 1 to 65535 bytes of UTF-8, with no null character.
- `+` and `#` are wildcards and are only legal in a subscription filter.
- In a filter, `+` must occupy an entire level, and `#` must be the last level
  and occupy it entirely (`sport/#` matches `sport`, `sport/` does not match it
  the same way - the tool reports both forms).
- A leading `$` marks a broker-reserved topic (`$SYS/...`); a `#` or `+` at the
  first level does not match those.
- Sparkplug B topics must follow `spBv1.0/<group>/<type>/<node>[/<device>]` with
  a known message type.

Usage:
    python tools/mqtt_topic_check.py --topic "plant/line1/temp" --publish
    python tools/mqtt_topic_check.py --topic "plant/+/temp" --subscribe
    python tools/mqtt_topic_check.py --topic "spBv1.0/plant/NDATA/esp32-01"
    python tools/mqtt_topic_check.py --topic "a/#/b" --subscribe --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Optional

MAX_BYTES = 65535

SPARKPLUG_TYPES = {
    "NBIRTH", "NDEATH", "NDATA", "NCMD",
    "DBIRTH", "DDEATH", "DDATA", "DCMD",
    "STATE",
}

RESERVED_FIRST = ("$SYS", "$share")


def check_topic(topic: str, subscribe: bool = False) -> dict:
    """Return a report for one topic. ``ok`` is False when a rule is broken."""
    problems = []
    notes = []

    if not topic:
        problems.append("a topic cannot be empty")
        return {"topic": topic, "ok": False, "problems": problems, "notes": notes}

    encoded = topic.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        problems.append("topic is %d bytes, the limit is %d" % (len(encoded), MAX_BYTES))
    if "\x00" in topic:
        problems.append("a topic cannot contain a null character")

    levels = topic.split("/")
    if any(level == "" for level in levels):
        notes.append("an empty level (%r) is legal but almost always a mistake" % topic)

    has_hash = "#" in topic
    has_plus = "+" in topic

    if not subscribe and (has_hash or has_plus):
        problems.append("wildcards are only legal in a subscription filter, not in a publish topic")

    if subscribe:
        for index, level in enumerate(levels):
            if "#" in level:
                if level != "#":
                    problems.append("'#' must occupy an entire level, found %r" % level)
                if index != len(levels) - 1:
                    problems.append("'#' must be the last level, found it at level %d of %d"
                                    % (index + 1, len(levels)))
            if "+" in level and level != "+":
                problems.append("'+' must occupy an entire level, found %r" % level)

    if levels and levels[0].startswith("$"):
        notes.append("a leading '$' marks a broker-reserved topic; a wildcard at the "
                     "first level does not match it")
        if subscribe and levels[0] in ("+", "#"):
            problems.append("a wildcard at the first level never matches a '$' topic")

    sparkplug = None
    if levels and levels[0] == "spBv1.0":
        sparkplug = _check_sparkplug(levels)
        if sparkplug["problems"]:
            problems.extend(sparkplug["problems"])
        if sparkplug["notes"]:
            notes.extend(sparkplug["notes"])

    return {
        "topic": topic,
        "levels": len(levels),
        "bytes": len(encoded),
        "subscribe": subscribe,
        "sparkplug": sparkplug is not None,
        "ok": not problems,
        "problems": problems,
        "notes": notes,
    }


def _check_sparkplug(levels):
    problems = []
    notes = []
    if len(levels) < 4:
        problems.append("Sparkplug needs spBv1.0/<group>/<type>/<node>, found %d levels"
                        % len(levels))
        return {"problems": problems, "notes": notes}
    if len(levels) > 5:
        problems.append("Sparkplug allows at most 5 levels, found %d" % len(levels))
    group, kind, node = levels[1], levels[2], levels[3]
    if not group:
        problems.append("the group id cannot be empty")
    if kind not in SPARKPLUG_TYPES:
        problems.append("%r is not a Sparkplug message type" % kind)
    if not node:
        problems.append("the edge node id cannot be empty")
    if kind in ("DBIRTH", "DDEATH", "DDATA", "DCMD") and len(levels) < 5:
        problems.append("%s requires a device id as the fifth level" % kind)
    if kind in ("NBIRTH", "NDEATH", "NDATA", "NCMD") and len(levels) == 5:
        notes.append("a node-level message with a device id is unusual")
    return {"problems": problems, "notes": notes}


def matches(filter_topic: str, topic: str) -> bool:
    """Does a subscription filter match a publish topic? Used to test a scheme."""
    if filter_topic.startswith("$") != topic.startswith("$"):
        return False
    f_levels = filter_topic.split("/")
    t_levels = topic.split("/")
    for index, part in enumerate(f_levels):
        if part == "#":
            return True
        if index >= len(t_levels):
            return False
        if part == "+":
            continue
        if part != t_levels[index]:
            return False
    return len(f_levels) == len(t_levels)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate MQTT topics and filters.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--subscribe", action="store_true", help="treat it as a filter")
    parser.add_argument("--publish", action="store_true", help="treat it as a publish topic")
    parser.add_argument("--matches", help="check that the filter matches this topic")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.subscribe and args.publish:
        parser.error("choose one of --subscribe and --publish")

    result = check_topic(args.topic, subscribe=args.subscribe)
    if args.matches is not None:
        result["matches"] = matches(args.topic, args.matches)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    print("%s  (%d levels, %d bytes)" % (result["topic"], result["levels"], result["bytes"]))
    if result["sparkplug"]:
        print("  recognised as a Sparkplug B topic")
    for problem in result["problems"]:
        print("  ERROR  %s" % problem)
    for note in result["notes"]:
        print("  note   %s" % note)
    if "matches" in result:
        print("  %s %r" % ("matches" if result["matches"] else "does NOT match", args.matches))
    print("")
    print("  %s" % ("ok" if result["ok"] else "rejected"))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
