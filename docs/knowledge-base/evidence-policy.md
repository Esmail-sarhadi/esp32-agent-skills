# Evidence and Verification Policy

## Why this exists

Community reports are valuable but not all reports are correct. A symptom may
have several causes, a workaround may hide the fault, and a fix may apply only
to one board or release. This policy prevents an agent from turning a plausible
comment into a universal rule.

## Grades

| Grade | Meaning | Allowed wording |
|---|---|---|
| A | Officially documented or upstream fix confirmed; reproduction exists | Verified for stated scope |
| B | Detailed community fix with reproducible conditions, not independently rerun | Reported reproducible; scope limited |
| C | Plausible anecdote or incomplete diagnosis | Candidate cause; verify locally |
| D | Open issue, unanswered report or conflicting evidence | Unresolved; do not prescribe as a fix |

## Required metadata

- Stable case ID and title.
- Source URL, source type, publication/update date if available, access date.
- SoC and module; board revision when known.
- Framework, exact version, compiler/toolchain and relevant configuration.
- Peripheral part number, schematic/wiring and power conditions.
- Symptom, exact log/error and frequency.
- Root cause with evidence; alternative hypotheses.
- Fix, trade-offs, known regressions and version range.
- Reproduction procedure and expected/observed result.
- Regression test or explicit reason it cannot be automated.
- Verification grade and reviewer/date.

## Source handling

Prefer datasheets, errata, official programming guides, release notes and
upstream code. Use GitHub issues and PRs to establish version-specific behavior.
Use Stack Overflow, Reddit, forums and Q&A as leads and field context. Preserve
the source link and summarize in original words; do not copy large answer text.

## Safe language

Say "reported on ESP32-S3 with Arduino-ESP32 X" rather than "ESP32 does this"
when the evidence is board- or version-specific. Say "possible heap retention"
rather than "memory leak" if the issue may be TCP TIME_WAIT or allocator
fragmentation. Never advise disabling brownout, watchdog, TLS validation or
safety interlocks as a production fix.

## Promotion

A C/D case can be promoted only after a reproduction, upstream confirmation,
or independent corroboration. Keep the original grade history in the case.
