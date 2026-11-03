# AGENTS.md

Instructions for a coding agent working in this repository, or using it on a
project. Read this before the README: the README explains what is here, this
file says what to do with it.

## What this repository is

101 skills and 10 checkers for ESP32-family firmware. A skill is a decision
document: which pin is forbidden, which partition layout bricks the board,
which number in the datasheet decides the design. A checker is the executable
half of the same fact, so the claim can be re-run instead of remembered.

## The rule that matters

**Run the checker before writing the code, and again before flashing.**

```bash
python tools/pincheck.py --soc esp32s3 --assign "4=sda,5=scl,48=led"
python tools/partition_check.py --file partitions.csv --flash 4MB --ota
python tools/power_budget.py --battery 3000 --wakes-per-hour 12 --wake-ms 2000
python tools/flash_layout.py --flash 4MB 0x0 boot.bin 0x8000 part.bin 0x10000 app.bin
```

Every one of them exits non-zero on a real problem, so they belong in CI and in
a pre-flash hook, not only in a terminal someone remembers to open.

Do not answer a pin question from memory. `data/esp32-pins.json` is the only
source of truth in this repository for which GPIO exists, which one is consumed
by flash, and which one changes the boot mode. If a SoC is not in that file,
say so and stop: a wrong `reserved_flash` entry is worse than a missing chip.

## Choosing a skill

`skills/` is one directory per topic, and the `description` line in each
`SKILL.md` starts with "Use when" precisely so it can be matched against a
request. Match on the failure, not the feature: a request to "use a W5500" is
really a request about SPI timing, DHCP failure and the 3.3 V rail.

If two skills apply, read the one that names the failure you are trying to
avoid, then the other. If none apply, say that instead of improvising: this
corpus is explicit about what it does not cover.

## What the claims in this repository are worth

- **Verified on hardware**: a handful of pins and one board
  (`ESP32-D0WD-V3`). Where a skill says so, it was measured.
- **From the datasheet or the driver source**: most of the corpus. The skill
  names the register, the header or the errata it came from.
- **From a field report**: the `esp32-field-gotchas` skill and the field notes
  carry the thread each one came from.

Do not upgrade a claim's confidence when quoting it. If a skill says "the
datasheet lists 60 mA per LED", do not write "measured".

## Adding a skill

```bash
mkdir -p skills/esp32-your-topic
$EDITOR skills/esp32-your-topic/SKILL.md
cp LICENSE skills/esp32-your-topic/LICENSE.txt
python tools/validate_skills.py      # frontmatter, name, length, no TODO
python tools/gen_manifest.py         # agent.yaml and .claude-plugin stay in step
python -m unittest discover -s tests
```

`tests/test_skills_corpus.py` generates one test per skill from the directory
listing, so a skill cannot be added without a test. `tools/gen_manifest.py
--check` fails in CI when a manifest has drifted from the tree.

## Commands

| Command | What it is for |
|---|---|
| `python tools/validate_skills.py` | frontmatter and shape of every skill |
| `python tools/gen_manifest.py --check` | manifests match the tree |
| `python tools/esp32_skills_cli.py --list` | the ten checkers, one entry point |
| `python build.py` | zipapp and Windows executable into `dist/` |
| `python -m unittest discover -s tests` | the full suite |

## Style

Short sentences. A number with a source, or no number. No emoji. When
something is unknown, write that it is unknown - the corpus has more value as
a record of what is not known than as a confident-sounding summary.
