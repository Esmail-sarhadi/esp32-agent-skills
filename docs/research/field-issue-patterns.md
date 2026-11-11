# Field issue research: recurring ESP32 failure patterns

Research date: 2026-11-07

## Scope and evidence standard

This expansion is based on recurring symptom clusters found in Espressif documentation, public ESP-IDF/Arduino-ESP32/ESPHome issue trackers and troubleshooting searches. Search result frequency is not a verified Google search-volume ranking. Public issue reports are treated as incident evidence for the reporter's exact hardware/software tuple, not as proof of a universal defect or confirmed root cause.

## Observed problem clusters

| Cluster | Recurring user-visible symptom | Engineering response added |
|---|---|---|
| Wi-Fi lifecycle | Authentication loops, disconnect reasons, link-up without IP/DNS, stale sessions | Reason-code forensics, credential recovery, event/IP lifecycle and provisioning recovery |
| Radio coexistence | BLE scan misses, Wi-Fi watchdogs, C6 Wi-Fi/802.15.4 starvation | Version-pinned coexistence regression matrix and long-duration RF soak |
| Power/reset | Brownout on RF or actuator events, ambiguous reset cause, unsafe outputs during reset | Rail transient measurement, reset classification and safe actuator defaults |
| Crash/memory | Guru Meditation, invalid backtrace, stack overflow, heap corruption | ELF-matched symbolication, stack watermark and allocation forensics |
| Storage/update | NVS no-free-pages, flash wear, OTA rollback, image/partition mismatch, power loss | Safe migration, write-rate budget, pending-verify qualification and fault injection |
| Low power | Immediate deep-sleep wake, missed timer wake, Wi-Fi latency after power save | Wake-source electrical review and measured latency/current qualification |
| Serial/fieldbus | Upload timeout, blank logs, UART overflow, RS485 truncation, Modbus timing and map errors | USB/UART path audit, direction timing, frame-gap validation and typed register mapping |
| Network security | TLS failure after sleep, SNI/time mismatch, DNS stale cache, MQTT duplicates | TLS time/SNI diagnostics, resolver lifecycle and idempotent MQTT session recovery |
| Peripheral reliability | I2C bus stuck, PSRAM/DMA capability mismatch, ADC2/Wi-Fi conflict, GPIO strap loading | Bus recovery, capability-aware allocation, target-specific ADC arbitration and boot strap audit |
| Engineering process | Regressions after SDK/controller updates, missing field evidence | Version bisect and minimal crash telemetry record |

## Primary sources consulted

### Espressif documentation
- Fatal errors, panic, watchdog, brownout, stack and heap checks: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/fatal-errors.html
- ESP-IDF error code reference: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/error-codes.html
- Wi-Fi programming guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html
- Radio coexistence: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/coexist.html
- NVS: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/nvs_flash.html
- OTA and rollback: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html
- Sleep modes: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/sleep_modes.html
- UART: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/uart.html
- ESP-Modbus protocol aspects: https://docs.espressif.com/projects/esp-modbus/en/main/esp32/modbus_protocol_aspects.html

### Public issue reports (reporter-specific evidence)
- ESP-IDF #19306: ESP32-C6 Wi-Fi/802.15.4 receive stall reported after BLE idle; workaround is reporter-verified, root-cause mechanism is explicitly a hypothesis: https://github.com/espressif/esp-idf/issues/19306
- ESP-IDF #18838: Wi-Fi/802.15.4 coexistence stuck while a frequency-switch poll appears to spin: https://github.com/espressif/esp-idf/issues/18838
- ESP-IDF #18931: BLE scan behavior regression reported under Wi-Fi coexistence: https://github.com/espressif/esp-idf/issues/18931
- ESP-IDF #6743: Wi-Fi task watchdog under load/coexistence: https://github.com/espressif/esp-idf/issues/6743
- ESP-IDF #18702: Wi-Fi authentication retry loop after AP password change: https://github.com/espressif/esp-idf/issues/18702
- ESP-IDF #13598: Wi-Fi transmit path blocked after a specific BLE scan/software reset sequence on classic ESP32: https://github.com/espressif/esp-idf/issues/13598
- ESPHome #19803: ESP32-S3 deep-sleep timer wake reliability report: https://github.com/esphome/esphome/issues/19803
- ESPHome #9850: immediate wake from configured deep-sleep pin: https://github.com/esphome/esphome/issues/9850
- ESPHome #17180: Modbus RTU device interoperability issue after inter-frame delay change: https://github.com/esphome/esphome/issues/17180
- Arduino-ESP32 #440: classic ESP32 ADC2/Wi-Fi limitation: https://github.com/espressif/arduino-esp32/issues/440
- Arduino-ESP32 troubleshooting: flashing timeout, boot mode, cable and serial path: https://github.com/espressif/arduino-esp32/blob/master/docs/en/troubleshooting.rst

## Interpretation and limits

- The search identifies recurring *problem classes*, not statistically validated query rankings or population incidence.
- Upstream issues can be open, version-specific, board-specific or unresolved. Their workaround must not be copied blindly.
- Skills instruct agents to freeze the target/version tuple, preserve raw evidence, isolate a reproducer, test competing hypotheses and separate host tests from hardware qualification.
- Hardware/RF/power/EMC and safety claims still require the actual board, instruments and applicable standards.


## Follow-up research: runtime, storage and security edge cases

Research date: 2026-11-10

This wave targets narrow failure modes surfaced in current upstream reports and Espressif advisories. Reports are configuration-specific evidence, not proof that every ESP32 target is affected.

| Evidence | Engineering risk | Added skill |
|---|---|---|
| ESP-IDF external RAM guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/external-ram.html | PSRAM-backed task stacks and buffers may be inaccessible during cache-disabled flash operations or deep-sleep transitions | esp32-psram-stack-flash-boundary |
| Fatal error guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/fatal-errors.html | IRAM-safe ISR paths must not call flash-resident code or access inaccessible data while cache is disabled | esp32-flash-cache-disabled-isr-audit |
| ESP-IDF #19403: https://github.com/espressif/esp-idf/issues/19403 | Reported wear-leveling page-edge access can cause silent data loss in a specific implementation path | esp32-wear-leveling-page-boundary-integrity |
| ESP-IDF #19400: https://github.com/espressif/esp-idf/issues/19400 | Reported interaction between ISR and task timer dispatch may lose or fail to re-arm timer events | esp32-esp-timer-isr-task-race-audit |
| ESP-IDF #19378: https://github.com/espressif/esp-idf/issues/19378 | Non-blocking TLS/select state may fail to progress after timeout in a reported configuration | esp32-tls-nonblocking-select-recovery |
| ESP32-C5 advisory: https://documentation.espressif.com/AR2025-008_ESP32-C5_Series_Chips_Bug_Advisory_EN.html | Version-scoped PSRAM reset, crypto alignment and sleep coexistence defects require exact affected/fixed commit checks | esp32-c5-psram-crypto-alignment-qualification; esp32-c5-reset-psram-ota-rollback-interaction |
| ESP-IDF #19409: https://github.com/espressif/esp-idf/issues/19409 | EAP-TLS reauthentication can stall critical Wi-Fi processing on a reported setup | esp32-wifi-eap-tls-reauth-starvation |
| ESP-IDF #19405: https://github.com/espressif/esp-idf/issues/19405 | ESP-NOW TX queue ownership problems can wedge transmit and exhaust buffers | esp32-espnow-tx-queue-ownership |
| ESP-IDF #19402: https://github.com/espressif/esp-idf/issues/19402 | SDMMC teardown and mutex lifetime can create priority/lifecycle deadlocks | esp32-sdmmc-host-lifecycle-lock-order |
| ESP-IDF #19395: https://github.com/espressif/esp-idf/issues/19395 | RGB panel scan-out needs explicit recovery and bandwidth qualification under concurrent memory load | esp32-rgb-panel-bounce-buffer-recovery |
| ESP-IDF security advisories: https://github.com/espressif/esp-idf/security/advisories | Product exposure requires component, version, commit, target and configuration matching against SBOM/build provenance | esp32-security-advisory-version-triage |

Issue titles and descriptions are used to derive testable investigation scenarios. No Google search-volume ranking is claimed. Security exposure and silicon errata must be checked against the exact firmware dependency graph, affected version range and target revision before deciding impact.


## Follow-up research: cryptographic streaming, OTA retries and concurrency

Research date: 2026-11-11

The following reports were opened or updated between 2026-11-05 and 2026-11-11. They are incident evidence tied to the stated target/version tuple, not universal defects. Issue status was checked on 2026-11-11; recheck before using a workaround in a production release.

| Source | Target and version reported | Symptom / evidence | Engineering action and evidence limit |
|---|---|---|---|
| ESP-IDF #19406: https://github.com/espressif/esp-idf/issues/19406 | release/v5.5, v5.5.x tags; originally reproduced on ESP32-C6 and classic ESP32 with CONFIG_MBEDTLS_HARDWARE_AES=y | Multipart AES-GCM updates with non-16-byte chunk lengths can produce wrong plaintext and tag. The report gives a deterministic 381-byte failing chunk and 368-byte aligned control. | Added esp32-aes-gcm-multipart-stream-integrity. Reporter identifies fixes on master, v6.0 and v6.1; no v5.5 backport was present at filing. Verify the actual branch and hardware AES path. |
| ESP-IDF #19413: https://github.com/espressif/esp-idf/issues/19413 | ESP32-C6 rev v0.2, ESP-IDF v6.0.1 and master commit de1e5035b5; Waveshare ESP32-C6-LCD-1.3 | After a failed otadata write, a retry of esp_ota_mark_app_valid_cancel_rollback() reportedly returns ESP_OK although the running app is not valid and is not the next boot target. The reporter has not observed it on-device; the suggested reproducer injects one failed write. | Extended OTA rollback qualification with readback of running partition state and boot partition. Open issue; the readback is reporter-proposed defensive handling, not an upstream fix. |
| ESP-IDF #19411: https://github.com/espressif/esp-idf/issues/19411 | ESP32-S3 rev v0.2, 2 MB PSRAM; IDF v5.5.4, v5.5.6 and master commit 0e6b480f85 | A PSRAM-resident pthread_once_t may skip the initializer if external-RAM compare-and-set returns false while external_ram_cas_lock is busy. | Extended PSRAM allocation audit. Keep once-control in internal DRAM on the reported combination until the upstream issue is resolved; validate dual-core contention on target. |
| ESP-IDF #19408 and #19409: https://github.com/espressif/esp-idf/issues/19408 ; https://github.com/espressif/esp-idf/issues/19409 | ESP32-S3 and ESP32-C5, ESP-IDF v6.1 development build v6.1-830-g0eddff3320f, WPA2-Enterprise EAP-TLS | One report describes a retransmitted 424-byte EAP-TLS fragment being treated as new input after a 1408-byte message; another measures about 887 ms of Wi-Fi task blocking during TLS processing. | Extended the existing EAP-TLS skill. The relationship between the two failure reports and disconnect reason 23 is not established; test duplicate-fragment handling and driver latency separately. |
| ESP-IDF #19399: https://github.com/espressif/esp-idf/issues/19399 | ESP32-C6FH4 rev v0.2 / M5Stack NanoC6; v5.5.6 versus v5.5.4 libphy | Wi-Fi scans reportedly return no APs on v5.5.6 while v5.5.4 connects reliably with the same board/AP. Plain ESP-IDF minimal example reproduction was not yet supplied. | Needs further investigation; do not generalize to all C6 boards or blame application code before an ESP-IDF-only reproduction. |
| ESP-IDF #19394: https://github.com/espressif/esp-idf/issues/19394 | ESP32-P4 rev v3.2, ESP-IDF v6.1, custom board using TPS62825 external DC-DC | Deep-sleep timer wake reportedly hangs before second-stage boot when the external regulator actively discharges its output while disabled. | Hardware-specific power sequencing case. Needs oscilloscope/current measurements and Espressif confirmation before adopting the proposed register workaround. |
| ESP-IDF #19370: https://github.com/espressif/esp-idf/issues/19370 | ESP32-C5 rev v1.2, ESP-IDF v6.0.2 | Security 2 SRP salt may lose a leading zero byte; the reporter measured 11 affected generations in 2,000 (~1/256) and identifies a caller-side heap over-read. | High-priority security triage; issue status was Reviewing. Verify upstream fix and exact call path before declaring exposure. |
| ESP-IDF #19377: https://github.com/espressif/esp-idf/issues/19377 | ESP32-S31, ESP-IDF v6.1, Korvo-1 | BLE scan with BR/EDR A2DP source plus Wi-Fi reportedly triggers a BTDM NULL dereference; issue is In Progress. | Keep the exact coexistence tuple and firmware library provenance; hardware/stack qualification required. |
| ESP-IDF #19414: https://github.com/espressif/esp-idf/issues/19414 | ESP32-C5 rev v1.2, ESP-IDF v6.1, secured NAN NDP | Follow-up messages from the same phone reportedly stop arriving after a secured NDP ends; open service works and NAN stop/start or reset clears it. | Newly filed on 2026-11-11; needs maintainer response and a minimal reproducer before skill creation. |
| Arduino-ESP32 #13096: https://github.com/espressif/arduino-esp32/issues/13096 | ESP32-S3, latest master, Windows 11 + WSL2 | HWCDC connection reportedly becomes inactive after a settings save taking about 1200 ms; issue is awaiting triage. | Track against the referenced PR #13048; isolate host/USB handoff and firmware blocking before treating it as a general USB CDC regression. |
| PlatformIO #1792: https://github.com/platformio/platform-espressif32/issues/1792 | DFRobot FireBeetle 2 16 MB board configuration | Flash-size/partition-size confusion was reported on 2026-11-04 and closed on 2026-11-06. | No new unresolved PlatformIO issue in the scanned window warranted a new skill. |

## Release and advisory watch

- ESP-IDF v5.5.6 was published on 2026-10-16. Its release notes include Wi-Fi supplicant security updates and other bug fixes; it does not establish that every open v5.5.6 issue is fixed. https://github.com/espressif/esp-idf/releases/tag/v5.5.6
- Espressif AR2026-008 marks the ESP-IDF v5.2 release branch end-of-life; the advisory was published 2026-09-15. New production work should use a supported branch and verify the support policy. https://www.espressif.com/en/support/documents/advisories
- Arduino-ESP32's latest stable release visible in the release list on 2026-11-11 was 3.3.12 (based on ESP-IDF v5.5.5, published 2026-09-18); 4.0.0-RC1 is a pre-release based on ESP-IDF v6.1 (published 2026-09-23). The release list did not show a final 4.0.0 tag on 2026-11-11. https://github.com/espressif/arduino-esp32/releases
- Espressif AR2026-006 remains relevant to ECDSA Secure Boot on ESP32-H2/C5/C61/P4/S31 affected revisions. The advisory says no software fix is available for affected ROM verification, recommends RSA-based Secure Boot where supported, and states application-layer ECDSA verification/OTA is not affected. https://documentation.espressif.com/AR2026-006_Security_Advisory_Concerning_ECDSA_Secure_Boot_Issue_in_ESP32-H2_ESP32-C5_ESP32-C61_ESP32-P4_ESP32-S31_EN.html

No Google search-volume or popularity ranking is claimed. Open user reports remain version- and target-scoped until reproduced or confirmed by maintainers.
