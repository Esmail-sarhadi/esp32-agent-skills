#!/usr/bin/env bash
#
# Install the ESP32 skills into an agent harness.
#
#   ./install.sh                        # into ~/.claude/skills
#   ./install.sh --target ~/.codex/skills
#   ./install.sh --list                 # print skill names and exit
#   ./install.sh --dry-run              # show what would be copied
#
# Copies only; it never deletes or overwrites a directory it did not create
# without --force, and it never touches anything outside the target.

set -eu

ROOT=$(cd "$(dirname "$0")" && pwd)
TARGET="${HOME}/.claude/skills"
LIST_ONLY=0
DRY_RUN=0
FORCE=0

usage() {
    sed -n '3,10p' "$0" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --target)  TARGET="${2:?--target needs a directory}"; shift 2 ;;
        --list)    LIST_ONLY=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --force)   FORCE=1; shift ;;
        -h|--help) usage 0 ;;
        *) echo "unknown option: $1" >&2; usage 1 ;;
    esac
done

SKILLS_DIR="${ROOT}/skills"
[ -d "$SKILLS_DIR" ] || { echo "no skills/ next to this script" >&2; exit 1; }

if [ "$LIST_ONLY" -eq 1 ]; then
    for dir in "$SKILLS_DIR"/*/; do
        [ -f "${dir}SKILL.md" ] || continue
        basename "$dir"
    done
    exit 0
fi

count=0
skipped=0
for dir in "$SKILLS_DIR"/*/; do
    [ -f "${dir}SKILL.md" ] || continue
    name=$(basename "$dir")
    dest="${TARGET}/${name}"

    if [ -e "$dest" ] && [ "$FORCE" -eq 0 ]; then
        skipped=$((skipped + 1))
        continue
    fi
    count=$((count + 1))
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "would install ${name} -> ${dest}"
        continue
    fi
    mkdir -p "$dest"
    cp "${dir}SKILL.md" "$dest/SKILL.md"
    [ -f "${dir}LICENSE.txt" ] && cp "${dir}LICENSE.txt" "$dest/LICENSE.txt"
    [ -d "${dir}reference" ] && cp -R "${dir}reference" "$dest/"
done

if [ "$DRY_RUN" -eq 1 ]; then
    echo "${count} skill(s) would be installed into ${TARGET}"
else
    echo "${count} skill(s) installed into ${TARGET}"
fi
if [ "$skipped" -gt 0 ]; then
    echo "${skipped} already present, left alone (use --force to overwrite)"
fi
