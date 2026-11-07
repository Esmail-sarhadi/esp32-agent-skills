#!/usr/bin/env python3
"""Validate every SKILL.md against schemas/skill.schema.json.

Standard library only: the rules in the schema are re-implemented here rather
than pulled in with a JSON Schema library, so the checker runs anywhere Python
does.  The schema file stays the readable statement of the contract; this file
is the executable one, and ``tests/test_packaging.py`` keeps them in step.

    python tools/validate_skills.py
    python tools/validate_skills.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
SCHEMA = os.path.join(ROOT, "schemas", "skill.schema.json")

NAME_RE = re.compile(r"^(?:esp32-)?[a-z0-9]+(?:-[a-z0-9]+)*$")
DESCRIPTION_PREFIX = "Use when"
REQUIRED = ("name", "description", "license")
ALLOWED = set(REQUIRED) | {"metadata", "tools", "version"}


def parse_frontmatter(text: str):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None, "no YAML frontmatter between --- markers"
    fields = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith(" ") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, None


def validate_skill(directory: str):
    """Return a list of problems for one skill directory."""
    problems = []
    path = os.path.join(SKILLS, directory, "SKILL.md")
    if not os.path.isfile(path):
        return ["%s: SKILL.md is missing" % directory]

    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    fields, error = parse_frontmatter(text)
    if error:
        return ["%s: %s" % (directory, error)]

    for key in REQUIRED:
        if not fields.get(key):
            problems.append("%s: frontmatter is missing %r" % (directory, key))

    name = fields.get("name", "")
    if name and name != directory:
        problems.append("%s: name is %r, which does not match the directory"
                        % (directory, name))
    if name and not NAME_RE.match(name):
        problems.append("%s: name does not match %s" % (directory, NAME_RE.pattern))

    description = fields.get("description", "")
    if description and not description.startswith(DESCRIPTION_PREFIX):
        problems.append("%s: description must start with %r" % (directory, DESCRIPTION_PREFIX))
    if len(description) < 40:
        problems.append("%s: description is too short to route on (%d characters)"
                        % (directory, len(description)))

    unknown = sorted(set(fields) - ALLOWED)
    if unknown:
        problems.append("%s: unknown frontmatter keys: %s"
                        % (directory, ", ".join(unknown)))

    body = text[text.find("\n---\n", 3) + 5:] if "\n---\n" in text else ""
    if len(body) < 1200:
        problems.append("%s: body is %d characters, too thin to be a skill"
                        % (directory, len(body)))
    if "TODO" in body or "FIXME" in body:
        problems.append("%s: body still contains TODO/FIXME" % directory)
    return problems


def validate_all():
    if not os.path.isdir(SKILLS):
        return ["skills/ directory is missing"]
    problems = []
    directories = sorted(name for name in os.listdir(SKILLS)
                         if os.path.isdir(os.path.join(SKILLS, name)))
    if not directories:
        return ["skills/ contains no directories"]
    for directory in directories:
        problems.extend(validate_skill(directory))
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)

    problems = validate_all()
    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, indent=2))
    else:
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            print("%d problem(s) across the corpus" % len(problems), file=sys.stderr)
        else:
            print("all skills valid")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
