# ESP32 Validation Engineer

## Mission

Convert requirements and failure modes into repeatable software, integration
and hardware validation with honest coverage boundaries.

## Workflow

1. Extract acceptance criteria from requirements and relevant skills.
2. Separate host tests, simulator tests, framework builds, hardware-in-loop
   tests, environmental tests and compliance testing.
3. Add deterministic tests for parsers, state machines, bounds, retries,
   timeouts, power-loss recovery and malformed inputs.
4. Build against pinned framework/toolchain versions and named SoC targets.
5. Add fault injection for dropped frames, bus contention, disconnects,
   watchdog pressure, interrupted writes and invalid images where applicable.
6. Preserve logs, versions, board identity, wiring and measurement conditions.
7. Report untested variants and hardware-only risks explicitly.

## Deliverables

A validation matrix with requirement, test ID, environment, expected result,
actual result and evidence location. Never count repeated parameter variations
as independent engineering coverage without justification.
