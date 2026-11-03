---
name: psram-performance-tradeoffs
description: Psram Performance Tradeoffs for ESP32 embedded engineering.
---

# Psram Performance Tradeoffs

## Purpose
A repeatable engineering method for psram performance tradeoffs on ESP32 products. This guidance does not replace the exact SoC/module datasheet, board schematic, component datasheet, applicable standard or physical measurement.

## Required context
- Exact ESP32 SoC, module/package, board revision and schematic.
- Framework/toolchain and version (ESP-IDF, Arduino-ESP32 or PlatformIO).
- Component part numbers, wiring, electrical ratings and environment.
- Relevant source, configuration, logs, build artifacts and firmware revision.
- Product requirements, failure behavior, deployment constraints and available test equipment.

If a missing fact can change silicon capability, pin legality, electrical safety or an irreversible security setting, stop and request it. Otherwise state the assumption and its impact.

## Procedure
1. Identify exact target, board, framework/toolchain versions and project configuration.
2. Read target-specific Espressif documentation, datasheets, errata and component documentation; record revision and applicability.
3. Inspect source, Kconfig/sdkconfig, partition table, board definitions and resolved dependency versions; do not infer active settings from examples.
4. Map constraints and resource budgets relevant to this task: pins, timing, CPU, stack, heap, flash, bandwidth, power, thermal and RF.
5. Analyze startup, reset, disconnect, malformed input, resource exhaustion, power loss and recovery paths where applicable.
6. Propose bounded changes with explicit ownership, range checks, timeouts, state transitions and observable error handling.
7. Run relevant checkers, host tests and target builds. State what requires a real board, instrument, fixture or external service.
8. Report findings with severity, evidence, affected conditions, mitigation, test results and residual uncertainty.

## Domain checklist
- Psram Performance Tradeoffs: verify behavior against exact target and component revisions.
- Check normal operation, boundary values, invalid configuration and failure recovery.
- Check version compatibility with the pinned SDK/framework and dependency graph.
- Record measurable budgets and margins; do not substitute estimates for measurements.
- Ensure logs identify state and failure cause without exposing credentials or private data.
- Separate silicon capability from module wiring and board-level implementation.

## Safety and security
- Never invent GPIO capabilities, voltage tolerance, radio limits, memory capacity or peripheral availability.
- Never disable brownout detection, watchdogs, TLS verification or security controls to hide a defect.
- Never treat an ESP32 as a safety-rated controller or replacement for independent protective hardware.
- Keep credentials, private keys and sensitive device telemetry out of source, logs and examples.
- Treat eFuse, secure-boot, flash-encryption and production provisioning operations as irreversible/human-approved actions.
- A successful build does not prove electrical, RF, EMC, thermal or field reliability.

## Validation matrix
| Level | Evidence | Limitation |
|---|---|---|
| Static | Source/configuration checks and cited constraints | Cannot prove runtime behavior |
| Host | Deterministic parser/state/budget tests | Does not emulate silicon or electrical behavior |
| Build | Pinned SDK/toolchain build and artifact metadata | Does not prove board wiring or peripheral operation |
| Hardware | Named board, wiring, instruments, conditions and logs | Applies only to the tested configuration |

## Deliverable
Return target/version scope, confirmed facts and unknowns, ranked findings, evidence references, remediation, rollback considerations, exact commands and test outcomes, plus hardware-only validation still required.

## References
- ESP-IDF programming guide: https://docs.espressif.com/projects/esp-idf/en/stable/
- Espressif technical documents and datasheets: https://www.espressif.com/en/support/documents/technical-documents
- ESP-IDF component registry: https://components.espressif.com/
