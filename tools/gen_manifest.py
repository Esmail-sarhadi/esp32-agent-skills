#!/usr/bin/env python3
"""Generate the packaging manifests from the skills directory.

Nothing in ``agent.yaml`` or ``.claude-plugin/`` is typed by hand: every count
and every name is read from ``skills/``, ``tools/`` and ``VERSION``.  Run it
after adding a skill, and run it with ``--check`` in CI to fail when a manifest
has drifted from the tree.

    python tools/gen_manifest.py
    python tools/gen_manifest.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
TOOLS = os.path.join(ROOT, "tools")
PLUGIN_DIR = os.path.join(ROOT, ".claude-plugin")

# tools that are part of the command-line surface, in the order `--list` shows
CLI_MODULES = [
    "pincheck", "partition_check", "power_budget", "panic_decode", "airtime",
    "modbus_map_check", "modbus_frame", "mqtt_topic_check", "flash_layout",
    "i2c_address_check",
]


def read_version() -> str:
    path = os.path.join(ROOT, "VERSION")
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def parse_frontmatter(text: str) -> dict:
    """Return the frontmatter of a SKILL.md as a flat dict of strings."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("no frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith(" ") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def collect_skills() -> list:
    """Every skill directory, sorted, with its frontmatter."""
    out = []
    for name in sorted(os.listdir(SKILLS)):
        path = os.path.join(SKILLS, name, "SKILL.md")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            fields = parse_frontmatter(handle.read())
        out.append({
            "name": name,
            "description": fields.get("description", ""),
            "license": fields.get("license", ""),
        })
    return out


def collect_tools() -> list:
    return [name for name in CLI_MODULES
            if os.path.isfile(os.path.join(TOOLS, name + ".py"))]


def count_tests() -> int:
    """Number of test functions, so the description never claims a stale figure."""
    total = 0
    tests_dir = os.path.join(ROOT, "tests")
    for name in sorted(os.listdir(tests_dir)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        with open(os.path.join(tests_dir, name), "r", encoding="utf-8") as handle:
            total += len(re.findall(r"^    def test_", handle.read(), re.M))
    return total


def build_agent_yaml(skills, tools, version) -> str:
    lines = [
        'spec_version: "0.1.0"',
        "name: esp32-agent-skills",
        'version: "%s"' % version,
        "description: >-",
        "  Agent skills and checkers for ESP32 firmware: %d skills across pin safety,"
        % len(skills),
        "  power, partitioning, industrial protocols and field failures, plus %d"
        % len(tools),
        "  command-line checkers that exit non-zero on a real problem.",
        "author: Esmail Sarhadi",
        "license: MIT",
        "homepage: https://esmail-sarhadi.github.io/esp32-agent-skills/",
        "repository: https://github.com/Esmail-sarhadi/esp32-agent-skills",
        "keywords:",
    ]
    for word in ("esp32", "embedded", "firmware", "industrial", "modbus", "skills"):
        lines.append("  - %s" % word)
    lines.append("skills:")
    for skill in skills:
        lines.append("  - %s" % skill["name"])
    lines.append("checkers:")
    for tool in tools:
        lines.append("  - tools/%s.py" % tool)
    lines.append("install:")
    lines.append("  claude: .claude-plugin/plugin.json")
    lines.append("  codex: .agents/skills/ (install.sh --harness codex)")
    lines.append("  opencode: ~/.config/opencode/skills/ (install.sh --harness opencode)")
    lines.append("  cursor: .cursor/rules/esp32-domain.mdc")
    lines.append("  gemini: GEMINI.md")
    lines.append("  generic: skills/")
    return "\n".join(lines) + "\n"


def build_plugin_json(skills, tools, version) -> str:
    payload = {
        "name": "esp32-agent-skills",
        "version": version,
        "description": (
            "%d ESP32 firmware skills and %d checkers that stop an agent writing "
            "code which compiles and then kills the board: pin safety, flash "
            "layout, power budget, panic decoding, Modbus, industrial protocols."
            % (len(skills), len(tools))
        ),
        "author": {
            "name": "Esmail Sarhadi",
            "url": "https://github.com/Esmail-sarhadi",
        },
        "homepage": "https://esmail-sarhadi.github.io/esp32-agent-skills/",
        "repository": "https://github.com/Esmail-sarhadi/esp32-agent-skills",
        "license": "MIT",
        "keywords": [
            "esp32", "embedded", "firmware", "skills", "agents",
            "modbus", "rs485", "lora", "industrial", "hardware",
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def build_marketplace_json(skills, tools, version) -> str:
    payload = {
        "name": "esp32-agent-skills",
        "owner": {
            "name": "Esmail Sarhadi",
            "url": "https://github.com/Esmail-sarhadi",
        },
        "metadata": {
            "description": (
                "ESP32 firmware skills and checkers for coding agents: the "
                "hardware failures that compile cleanly and then stop the board."
            )
        },
        "plugins": [
            {
                "name": "esp32-agent-skills",
                "source": "./",
                "description": (
                    "%d skills and %d checkers for ESP32, ESP32-S3, -C3, -C6 and "
                    "-H2 firmware." % (len(skills), len(tools))
                ),
                "version": version,
                "author": {
                    "name": "Esmail Sarhadi",
                    "url": "https://github.com/Esmail-sarhadi",
                },
                "homepage": "https://esmail-sarhadi.github.io/esp32-agent-skills/",
                "repository": "https://github.com/Esmail-sarhadi/esp32-agent-skills",
                "license": "MIT",
                "keywords": ["esp32", "embedded", "firmware", "skills"],
            }
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def targets():
    skills = collect_skills()
    tools = collect_tools()
    version = read_version()
    return [
        (os.path.join(ROOT, "agent.yaml"), build_agent_yaml(skills, tools, version)),
        (os.path.join(PLUGIN_DIR, "plugin.json"), build_plugin_json(skills, tools, version)),
        (os.path.join(PLUGIN_DIR, "marketplace.json"),
         build_marketplace_json(skills, tools, version)),
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if a manifest on disk differs from the tree")
    args = parser.parse_args(argv)

    os.makedirs(PLUGIN_DIR, exist_ok=True)
    drifted = []
    for path, content in targets():
        current = None
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as handle:
                current = handle.read()
        if current == content:
            continue
        drifted.append(os.path.relpath(path, ROOT))
        if not args.check:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)

    if args.check:
        for name in drifted:
            print("out of date: %s" % name, file=sys.stderr)
        if drifted:
            print("run: python tools/gen_manifest.py", file=sys.stderr)
            return 1
        print("manifests match the tree")
        return 0

    print("wrote %d manifest(s): %s" % (len(drifted), ", ".join(drifted) or "none changed"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
