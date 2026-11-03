# Embedded Engineering Context

This repository is a domain knowledge pack for ESP32-family firmware and
industrial IoT. It contains task-specific skills, command-line checkers,
component and protocol notes, examples, and field-failure evidence.

## How to use the knowledge base

- Start with `AGENTS.md` for repository-wide operating instructions.
- Discover a matching directory in `skills/` and read its `SKILL.md`.
- Read adjacent `reference/` material when the skill asks for it.
- Use `rules/common/agent-workflow.md` and
  `rules/embedded/hardware-safety.md` for the always-relevant process.
- Run checkers from `tools/` rather than reimplementing their validations in
  prose.
- Consult `docs/knowledge-base/` for evidence policy, failure cases and
  research coverage.

## Evidence hierarchy

Prefer, in order: official SoC/module datasheets and errata; version-matched
Espressif documentation and source; reproducible repository tests; upstream
issue discussions with confirmed fixes; detailed field reports; community
anecdotes. Preserve the evidence grade and version scope from the source.

## Required task context

Before giving implementation advice, identify what is known and unknown about:
SoC/module, board revision, framework and version, toolchain, power supply,
external components, wiring, environment and intended failure behavior.
Do not block low-risk general explanations on missing details, but clearly mark
assumptions and ask for the one missing detail that changes the design.
