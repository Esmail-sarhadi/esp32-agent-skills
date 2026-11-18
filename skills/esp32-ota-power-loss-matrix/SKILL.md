---
name: esp32-ota-power-loss-matrix
description: Use when reviewing or implementing esp32 ota power loss matrix on an ESP32 target.
license: MIT
---

# Esp32 Ota Power Loss Matrix

## Purpose
A repeatable engineering method for esp32 ota power loss matrix on ESP32 products. This guidance does not replace exact SoC/module datasheets, board schematics, component datasheets, applicable standards or physical measurement.

## Required context
- Exact ESP32 SoC, module/package, board revision and schematic.
- Framework/toolchain and version (ESP-IDF, Arduino-ESP32 or PlatformIO).
- Component part numbers, wiring, electrical ratings and environment.
- Relevant source, configuration, logs, build artifacts and firmware revision.
- Product requirements, failure behavior, deployment constraints and test equipment.

## Procedure
1. Identify exact target, board, framework/toolchain versions and project configuration.
2. Read target-specific Espressif documentation, datasheets, errata and component documentation; record revision and applicability.
3. Inspect source, Kconfig/sdkconfig, partition table, board definitions and resolved dependency versions.
4. Map relevant constraints and budgets: pins, timing, CPU, stack, heap, flash, bandwidth, power, thermal and RF.
5. Analyze startup, reset, disconnect, malformed input, resource exhaustion, power loss and recovery paths.
6. Propose bounded changes with explicit ownership, range checks, timeouts, state transitions and observable errors.
7. Run relevant checkers, host tests and target builds; state what requires physical hardware.
8. Report findings with severity, evidence, affected conditions, mitigation, test results and residual uncertainty.

## Domain checklist
- Esp32 Ota Power Loss Matrix: verify behavior against exact target and component revisions.
- Check normal operation, boundary values, invalid configuration and failure recovery.
- Check compatibility with the pinned SDK/framework and dependency graph.
- Record measurable budgets and margins; do not substitute estimates for measurements.
- Ensure logs identify failure causes without exposing credentials or private data.
- Separate silicon capability from module wiring and board-level implementation.

## Safety and security
- Never invent GPIO capabilities, voltage tolerance, radio limits, memory capacity or peripheral availability.
- Never disable brownout detection, watchdogs, TLS verification or security controls to hide a defect.
- Never treat an ESP32 as a safety-rated controller or replacement for independent protective hardware.
- Keep credentials, private keys and sensitive device telemetry out of source, logs and examples.
- Treat eFuse, secure-boot, flash-encryption and production provisioning as irreversible/human-approved operations.
- A successful build does not prove electrical, RF, EMC, thermal or field reliability.

## Validation matrix
| Level | Evidence | Limitation |
|---|---|---|
| Static | Source/configuration checks and cited constraints | Cannot prove runtime behavior |
| Host | Deterministic parser/state/budget tests | Does not emulate silicon or electrical behavior |
| Build | Pinned SDK/toolchain build and artifact metadata | Does not prove board wiring or peripheral operation |
| Hardware | Named board, wiring, instruments, conditions and logs | Applies only to tested configuration |

## Deliverable
Return target/version scope, confirmed facts and unknowns, ranked findings, evidence references, remediation, rollback considerations, exact commands and test outcomes, plus hardware-only validation still required.

## Failed erase cleanup in esp_ota_begin()

[ESP-IDF #19439](https://github.com/espressif/esp-idf/issues/19439) reports an OTA resource leak on IDF v6.1 commit fff9895 and master as of 2026-11-13, reproduced on ESP32-C3 rev0.4; the reporter notes the code path is target-independent. esp_ota_begin() inserts an entry and publishes out_handle before erasing. If esp_partition_erase_range() fails, the function returns without removing the entry or restoring dangerous write protection for bootloader/partition-table targets. A later valid begin can return ESP_ERR_OTA_ALREADY_IN_PROGRESS until reboot.

A maintainer reproduced the failure and prepared a patch. The reporter then confirmed the patch on an ESP32-C3 board and in QEMU: the failed-erase regression test fails without the change (a handle is returned and the next begin reports ESP_ERR_OTA_ALREADY_IN_PROGRESS) and passes with it. The v6.1 backport also passed on release/v6.1 at c1d1695f8. The patch restores write protection, removes/frees the partial entry and publishes the handle only after erase succeeds. The issue remained under review at this scan; a tested patch is not the same as a merged or released fix.

Regression test: request an erase range larger than the partition, assert the first call fails without a usable handle, then assert a second valid begin succeeds and protection/state are restored. The reporter tested the board and QEMU single-stage cases; multi-stage reset cases were not run. Also test bootloader and partition-table partition guards on a disposable test image. Never use a production bootloader or partition table as a destructive fault-injection target.

## References
- ESP-IDF programming guide: https://docs.espressif.com/projects/esp-idf/en/stable/
- Espressif technical documents: https://www.espressif.com/en/support/documents/technical-documents
- ESP-IDF component registry: https://components.espressif.com/
