#!/usr/bin/env bash
#
# Install the ESP32 skills into a supported agent harness.
#
#   ./install.sh --harness claude
#   ./install.sh --harness codex
#   ./install.sh --harness opencode
#   ./install.sh --harness all
#   ./install.sh --target /custom/skills --dry-run
#
# Existing skill directories are left alone unless --force is supplied.

set -eu

ROOT=$(cd "$(dirname "$0")" && pwd)
HARNESS="claude"
TARGET=""
CUSTOM_TARGET=0
LIST_ONLY=0
DRY_RUN=0
FORCE=0

usage() {
    cat <<'EOF'
Usage: ./install.sh [options]
  --harness NAME   claude | codex | opencode | all (default: claude)
  --target DIR     install into a custom Agent Skills directory
  --list           list canonical skill names
  --dry-run        show planned writes without changing files
  --force          overwrite existing skill directories
  -h, --help       show this help

Harness destinations:
  claude    ~/.claude/skills
  codex     ~/.agents/skills
  opencode  ~/.config/opencode/skills
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --harness) HARNESS="${2:?--harness needs a name}"; shift 2 ;;
        --target) TARGET="${2:?--target needs a directory}"; CUSTOM_TARGET=1; shift 2 ;;
        --list) LIST_ONLY=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --force) FORCE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage >&2; exit 1 ;;
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

if [ "$CUSTOM_TARGET" -eq 1 ]; then
    TARGETS="$TARGET"
else
    case "$HARNESS" in
        claude) TARGETS="${HOME}/.claude/skills" ;;
        codex) TARGETS="${HOME}/.agents/skills" ;;
        opencode) TARGETS="${HOME}/.config/opencode/skills" ;;
        all) TARGETS="${HOME}/.claude/skills
${HOME}/.agents/skills
${HOME}/.config/opencode/skills" ;;
        *) echo "unsupported harness: $HARNESS" >&2; usage >&2; exit 2 ;;
    esac
fi

install_to_target() {
    target=$1
    count=0
    skipped=0
    for dir in "$SKILLS_DIR"/*/; do
        [ -f "${dir}SKILL.md" ] || continue
        name=$(basename "$dir")
        dest="${target}/${name}"
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
        if [ -d "${dir}reference" ]; then
            rm -rf "$dest/reference"
            cp -R "${dir}reference" "$dest/"
        fi
    done
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "${count} skill(s) would be installed into ${target}"
    else
        echo "${count} skill(s) installed into ${target}"
    fi
    [ "$skipped" -eq 0 ] || echo "${skipped} already present, left alone (use --force to overwrite)"
}

printf '%s\n' "$TARGETS" | while IFS= read -r target; do
    [ -n "$target" ] || continue
    install_to_target "$target"
done
