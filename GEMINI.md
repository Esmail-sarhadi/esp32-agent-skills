# ESP32 Agent Skills — Gemini CLI Context

This repository is an ESP32 and embedded-systems engineering knowledge pack.

Before implementation:
- Read `AGENTS.md` for repository workflow and commands.
- Search `skills/` for a matching `SKILL.md` and read its references.
- Use `rules/common/agent-workflow.md` and
  `rules/embedded/hardware-safety.md` for hardware-sensitive work.
- Identify exact SoC, board, framework/version and toolchain.
- Run relevant checkers in `tools/` and report exact outcomes.
- Keep datasheet facts, reproduced tests, upstream fixes and anecdotal reports
  clearly distinguished.
- Do not claim hardware validation from a successful software build.
- Never recommend disabling brownout detection as a power fix or treating an
  ESP32 as a safety-rated controller.

The canonical skills live in `skills/<id>/SKILL.md`. Use only the relevant
skill for the current task rather than loading the entire corpus.
