# Research Execution and Acceptance Matrix

## Purpose

This document translates the project's executive research brief into an
auditable implementation tracker. The brief defines the target scope, scale,
evidence grades and delivery expectations; it is not itself an itemized
catalogue of newly verified incidents or fixes. New technical claims must still
be supported by their primary sources and assigned an evidence grade.

## Baseline snapshot

Snapshot: PR #1 branch `feat/industrial-field-knowledge-expansion`, head
`44f543ce2c0b2fcfe363ef2e8c26ff3b4e8242e4`.

| Deliverable | Executive-brief target | Current repository baseline | Remaining gap / qualification |
|---|---:|---:|---|
| Task skills | 300–500 | 79 | 221–421 additional skills; avoid thin variants and duplicates |
| Field-failure cases | 2,000–3,000 | 23 | 1,977–2,977 cases; each needs source, scope, evidence grade and fix status |
| Software tests | 1,500–2,500 | 350 | 1,150–2,150 additional tests; current count includes corpus/structural checks and is not a hardware-test count |
| Buildable examples | 300–500 | 2 CI-built example projects | 298–498 additional independently documented examples; count only pinned, CI-compiled examples |
| Evidence classification | A–D on every finding | Policy and initial casebook in place | Audit every case and preserve unresolved D-grade reports |
| CI/toolchains | ESP-IDF, Arduino-ESP32 and PlatformIO; Linux, macOS and Windows | Python 3.10/3.12/3.13 tests and PlatformIO compile job pass | Add framework build jobs and OS coverage; do not infer cross-platform coverage from Python matrix alone |
| SoC/board coverage | ESP32 family, including S2/S3/C3/P4/C5 and related variants | Pin data currently includes classic ESP32, ESP32-S3 and ESP32-C3 | Add datasheet-backed profiles and keep SoC facts separate from board overlays |
| HIL/fault injection | Repeatable hardware/software validation | One documented physical-board bring-up; no broad HIL suite claimed | Add fixtures, wiring, measured acceptance limits and repeatable fault injection |

The two example projects counted above are the `examples/compiled` and
`examples/board-facts` PlatformIO projects. CSV fixtures, logs and pin-map
fixtures are useful test data, but are not counted as independent buildable
firmware examples.

The 350-test figure is the repository's software/unit/structural test count.
It must not be represented as 350 hardware tests or 350 independently
reproduced field-failure regressions. Case-linked regression coverage needs its
own explicit inventory.

## Scope-to-repository traceability

| Executive-brief area | Existing repository coverage | Next implementation focus |
|---|---|---|
| ESP32 family and board constraints | Pin checker and three SoC data profiles | Add S2, C6, H2, P4, C5 and board overlays from primary datasheets |
| Industrial serial and fieldbus | UART/RS485 skills, Modbus TCP dossier and map checker, RS232/RS422 and CAN-FD boundary skills | Modbus RTU simulator, framing/timeout regression suite, transceiver and isolation examples |
| Ethernet and IP networking | W5500/RMII skills and dossier; lwIP diagnostics | LAN8720/W5500 buildable examples, link/DHCP loss injection and socket lifecycle tests |
| Radio and wireless | LoRa/SX126x/CC1101 and Wi-Fi roaming skills; radio planning dossier | Region-specific RF constraints, packet-loss/retry simulation and radio family matrix |
| Analog and instrumentation | 4–20 mA, RTD, thermocouple, load-cell and voltage/current coverage | Calibration fixtures, ADC noise/linearity tests, input protection examples and uncertainty budgets |
| Runtime, memory and reliability | FreeRTOS, heap, DMA/PSRAM, watchdog and power skills; incident seed cases | Host-testable state machines, fuzzing, soak tests and version-scoped reproductions |
| Storage, boot and OTA | Existing storage, partition and secure OTA skills/checkers | Interrupted-write/update fault injection, rollback and NVS migration examples |
| Safety and environment | Safety interlock and thermal derating skills | Measured thermal/power cases, restart-inhibit tests and explicit safety-controller boundaries |
| Verification and CI | 350 software tests, six checkers and PlatformIO compilation | Expand framework/OS matrix, examples matrix, fuzz harnesses and documented HIL fixtures |

## Evidence rules

Use the policy in [evidence-policy.md](evidence-policy.md) without weakening it:

- **A:** official documentation, upstream-confirmed fix, or reproducible
  regression with a clear scope.
- **B:** detailed and credible field fix with reproducible conditions but not
  independently rerun in this repository.
- **C:** anecdotal or incomplete diagnosis; treat as a lead, not a prescription.
- **D:** unresolved, unanswered or conflicting report; never present as solved.

Every case must record its SoC/module, board where known, framework and exact
version, peripheral, electrical conditions, source URL, observed symptom,
root-cause evidence, fix status, reproduction and regression status. Keep
alternative hypotheses and confidence visible.

## Delivery gates

1. **Inventory and normalization:** deduplicate the existing 79 skills and 23
   cases; assign stable IDs and metadata; map every claim to a source.
2. **Industrial core:** reach 50–80 high-quality skills, 150 complete cases,
   50 pinned buildable examples and at least five tested checkers. The current
   skill/checker counts meet the numeric portion, but the case and example
   gates remain open.
3. **Broad coverage:** reach 150 skills, 500 cases and 300 deterministic
   regression scenarios; include a family/version matrix.
4. **Scale:** reach the brief's 300–500 skills, 2,000–3,000 cases,
   1,500–2,500 classified software/integration/regression tests and
   300–500 buildable examples.
5. **Production validation:** add HIL fixtures, power-loss/bus-noise/OTA
   interruption testing, manufacturing and calibration workflows, and release
   evidence. Software CI must never be described as proof of electrical
   safety, EMC, thermal margin or radio compliance.

## Counting policy

- A skill counts only when it has a unique trigger, actionable guidance,
  explicit platform/version limits, meaningful verification and sources.
- A case counts only when required metadata and evidence grade are present;
  unresolved cases are allowed but must remain labelled D.
- A test counts only when it asserts a distinct expected behavior. Do not count
  parameter permutations or duplicated assertions as separate engineering
  coverage without justification.
- An example counts only when it is independently understandable, has a
  pinned target/toolchain, and builds in CI. State whether it is host-only,
  simulator-based, or requires physical hardware.
- A hardware result counts only when the named board was actually exercised
  and measurements/logs are retained.

## Current validation reference

PR #1: https://github.com/Esmail-sarhadi/esp32-agent-skills/pull/1

Latest validated head at the snapshot above:
https://github.com/Esmail-sarhadi/esp32-agent-skills/actions/runs/41405909686

That run passed the Python 3.10, 3.12 and 3.13 test jobs and the PlatformIO
compile job. This is software/compile validation, not a claim that every
supported SoC, board, framework, operating system or peripheral has been
hardware-tested.
