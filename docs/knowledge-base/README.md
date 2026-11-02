# ESP32 Embedded & Industrial Knowledge Base

This directory is the evidence-oriented engineering layer of ESP32 Agent Skills.
It is designed for coding agents, firmware engineers, hardware engineers and
field-service teams. It complements the short, task-triggered skills in
`skills/`; it does not replace datasheets or electrical design review.

## Knowledge layers

| Layer | Purpose | Required output |
|---|---|---|
| Skills | Task-time instructions for an agent | Constraints, safe sequence, API/version notes |
| Field failures | Reusable incident knowledge | Symptom, context, root cause, fix status, regression |
| Protocol dossiers | Protocol and physical-layer design | Framing, timing, electrical limits, interoperability |
| Hardware dossiers | Component-specific integration | Datasheet facts, schematic checks, driver notes |
| Test patterns | Repeatable verification | Host, simulator, target and HIL tests |
| Decision records | Trade-offs and architecture | Assumptions, alternatives, failure consequences |

## Current expansion tranche

The first two tranches add twenty-five industrial, instrumentation and reliability skills plus a sourced
field-failure casebook. The casebook deliberately separates confirmed behavior
from hypotheses and open reports. References point to the original discussions
and upstream implementation; no forum post is treated as a universal design rule.

## Evidence grades

- **A — upstream verified:** fix or behavior is confirmed by upstream code,
  release notes, official docs, or a reproducible regression test.
- **B — reproducible field fix:** credible report with enough hardware and
  software detail to reproduce, but not independently validated here.
- **C — anecdotal:** useful symptom pattern; root cause or fix remains uncertain.
- **D — unresolved:** an open issue or incomplete investigation. Never present
  this as a solved case.

Every case must also state the chip family, framework and version when known.
A fix without a version boundary is incomplete knowledge.

## Agent retrieval contract

1. Identify exact SoC, module, board revision, framework, core/IDF version,
   peripheral part number, supply topology and wiring.
2. Search this knowledge base by symptom and subsystem before proposing code.
3. Distinguish electrical, protocol, driver, scheduler and application layers.
4. Prefer official documentation and upstream fixes over copied forum snippets.
5. State what is known, what is assumed and what must be measured.
6. Produce a minimal reproduction before changing several variables.
7. Add a regression test for every accepted fix.
8. Never claim hardware verification unless a real target was flashed and tested.

## Contribution format

Use `templates/field-failure.md` for incidents and
`templates/protocol-dossier.md` for protocol notes. Add a source URL, access
date, exact versions, reproduction steps, expected/observed result and a
regression test. Do not copy long forum answers; extract the engineering lesson
and cite the original source.

## Scope

The roadmap in [expansion-roadmap.md](expansion-roadmap.md) defines the target
coverage and release gates. Counts in that document are goals, not claims about
the current repository.
