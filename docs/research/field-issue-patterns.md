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

## Follow-up research: ESP-IDF security advisories and fresh issue reports

Research date: 2026-11-11. Advisory versions and release availability below were checked against Espressif's GitHub Security Advisories and release list on this date.

| Source | Scope and preconditions | Severity / versions | Action and evidence limit |
|---|---|---|---|
| GHSA-49x8-xqjg-2pjg: https://github.com/espressif/esp-idf/security/advisories/GHSA-49x8-xqjg-2pjg | ESP-TEE on ESP32-C5/C6/C61/H2; unvalidated REE stack pointer is used before switching to trusted TEE stack on ecall and interrupt entry. Requires local code execution in REE. | Critical 9.3; affected v5.5.5, v6.0.3, v6.1; fixed v5.5.6, v6.0.4 and v6.1.1. | Added esp32-tee-privilege-switch-boundary-audit. No runtime workaround. On 2026-11-11 v6.0.4/v6.1.1 were listed as pending; inspect component presence and exact commit. |
| GHSA-ch63-jxm5-vmvf: https://github.com/espressif/esp-idf/security/advisories/GHSA-ch63-jxm5-vmvf | lwIP cached DNS lookup writes multiple cached A/AAAA records through a single ip_addr_t output when CONFIG_LWIP_DNS_MAX_HOST_IP > 1. Trigger is a later cache hit, not the first network lookup. | High 7.4; affected v5.2.3–5.2.8, v5.3.2–5.3.6, v5.4.0–5.4.4, v5.5.0–5.5.5, v6.0.0–6.0.2. | Added esp32-lwip-dns-cache-multi-address-bounds. v5.5.6 and v6.0.3 are fixed; v5.3.7/v5.4.5 pending; v5.2 EOL has no fix. Keep the setting at its default of 1 until patched. Stack protection detects but does not prevent the overwrite. |
| GHSA-rjvf-fxv5-x87j: https://github.com/espressif/esp-idf/security/advisories/GHSA-rjvf-fxv5-x87j | BLE Mesh GATT read, Bluedroid host, PB-GATT or GATT Proxy bearer. Negative signed callback return is interpreted as an unsigned length. NimBLE adapter is not affected. | High 7.1; affected v5.2.7, v5.3.5, v5.4.4, v5.5.5, v6.0.2. | Extended esp32-ble-malformed-packet-hardening. v5.2.8, v5.3.6, v5.5.6 and v6.0.3 are fixed; v5.4.5 pending; v6.1+ not affected. |
| GHSA-c26h-gm53-qg83: https://github.com/espressif/esp-idf/security/advisories/GHSA-c26h-gm53-qg83 | OpenThread Border Router ND6 parser; requires CONFIG_OPENTHREAD_BORDER_ROUTER=y and a crafted ICMPv6 Router Advertisement on the infrastructure link. Thread end devices and non-BR builds are outside scope. | High 7.1; affected v5.2.7, v5.3.5, v5.4.4, v5.5.4, v6.0.2. | Added to security-advisory triage. Fixed v5.2.8, v5.3.6, v5.5.5 and v6.0.3; v5.4.5 pending; v6.1+ not affected. No runtime workaround; restrict infrastructure-link reachability until patched. |
| ESP-IDF #19415: https://github.com/espressif/esp-idf/issues/19415 | ESP32-C3, ESP-IDF v5.5.5, NimBLE central, BLE 1M; intermittent ATT timeout and multi-second notification delivery gaps. | Opened 2026-11-11; issue report has no raw controller capture and is not a maintainer-confirmed regression. | Existing BLE throughput, connection-budget and notification-backpressure skills cover the investigation class. No new skill added; require HCI/VHCI trace and independent reproduction. |

### Release and ecosystem snapshot

- ESP-IDF releases visible on 2026-11-11: v5.5.6 (2026-10-16), v6.0.3 (2026-09-02), v6.1 (2026-08-27), v5.3.6 (2026-09-15), v5.2.8 (2026-09-11). v5.2 reached EOL in August 2026.
- Arduino-ESP32 latest stable visible: 3.3.12, based on ESP-IDF v5.5.5 (2026-09-18). 4.0.0-RC1 is a pre-release based on ESP-IDF v6.1 (2026-09-23). The base IDF version is a risk indicator only; verify the actual bundled component and configuration before declaring a product exposed.
- PlatformIO platform-espressif32 v8.0.0 was published 2026-10-19. Issue #1792 about a DFRobot FireBeetle 2 flash-size/partition confusion was closed 2026-11-06. Pin the platform and inspect the resolved framework package; do not assume PlatformIO's platform tag equals an ESP-IDF release tag.
- Arduino-ESP32 #13096 remains open and awaiting triage (ESP32-S3 HWCDC disconnect on latest master, Windows 11 + WSL2); #13102 is an open USB CDC feature request, not a confirmed defect.
- No recent Stack Overflow or Reddit discussion located in this scan independently confirms the exact upstream advisory or issue mechanisms. User discussions are not used as a substitute for Espressif's advisory or issue evidence.

No Google search-volume or popularity ranking is claimed. Affected-version ranges are advisory-specific; do not merge them into one generic "ESP-IDF vulnerable" range.


## 2026-11-18 weekly follow-up: reset state, SMP scheduling, ADC and radio lifecycle

This scan reviewed new ESP-IDF issues opened 2026-11-10 through 2026-11-18, Arduino-ESP32 releases/issues, PlatformIO and pioarduino release/issues, current ESP-IDF releases and Espressif security advisories. New issue reports are not treated as universal defects; the exact target, revision, SDK commit and reproduction conditions are retained.

### High-priority engineering findings

- **ESP32-C6 Secure Boot V2 / ECC reset state — [esp-idf#19421](https://github.com/espressif/esp-idf/issues/19421), opened 2026-11-11.** C6 QFN32 rev0.2, ROM esp32c6-20220919, DevKitM-1, IDF v6.1 fff9895, Secure Boot V2 ECDSA P-256 and release flash encryption. After PSA hardware ECC use followed by esp_restart(), ROM ECDSA verification reports zero valid key blocks and halts; power-on and USB-Serial-JTAG reset succeed. Reporter traces retained PCR_ECC_MEM_PD through the CPU-level reset and reports a device-tested linker-wrap workaround. Issue was open and assigned on Nov16. Confidence: high for the exact reported C6 tuple, not vendor-confirmed or generalizable. Added a dedicated reset/power-state audit skill; hardware qualification and vendor patch mapping remain required.
- **ESP32-S31 ADC/PHY lock-order inversion — [esp-idf#19433](https://github.com/espressif/esp-idf/issues/19433), opened 2026-11-13.** Korvo-1, 16 MB flash, octal PSRAM, release/v6.1 f0114250e2, Arduino 4.0.0-rc1 component. Wi-Fi WIFI_PS_MAX_MODEM, Bluedroid BR/EDR A2DP and periodic ADC1 oneshot reads on the other core produced a dual-core interrupt WDT after 5–15 minutes. The ADC path appears to hold rtc_spinlock then request regi2c; the PHY wake path appears to take regi2c then request rtc_spinlock. The PHY is closed source, so this is a lock-order hypothesis. Espressif said on Nov16 it would fix the issue; no fix commit was mapped at scan time. Added a dedicated S31-only investigation skill.
- **Cross-core scheduler suspension — [esp-idf#19450](https://github.com/espressif/esp-idf/issues/19450) and [#19456](https://github.com/espressif/esp-idf/issues/19456), both opened 2026-11-17.** On S3, #19450 reports cross-core task notifications/resume not waking a core-1 pinned task when core 1 resumes its scheduler; the reported code path puts the task on the ISR core's pending-ready list. Reported in IDF v6.1, master and release/v5.5. #19456 reports synchronous esp_ipc_call() from a 1 kHz esp_timer callback never returning while core 1 continuously reads flash, stalling all timer callbacks; reproduced on v6.3-dev and v5.3, not v5.2.2. Two separate fixes were proposed: PR #19451 (ISR pending-ready-list path, commit 7266fdc) and PR #19457 (task-context SMP yield path, commit dfaa88f). Both remained open against master; their new S3 tests passed, but neither was merged or mapped to a release. Updated the existing multicore/IPC skill rather than adding a duplicate.
- **OTA failed-erase cleanup — [esp-idf#19439](https://github.com/espressif/esp-idf/issues/19439), opened 2026-11-14.** IDF v6.1 fff9895, reproduced on C3 rev0.4; code path reported target-independent. If esp_ota_begin() publishes an entry/handle before erase and the erase fails, the entry can remain live, the next valid begin returns ESP_ERR_OTA_ALREADY_IN_PROGRESS, and dangerous write protection may remain disabled for bootloader/partition-table targets. A maintainer reproduced it; the reporter verified the patch on ESP32-C3 hardware and QEMU, and separately confirmed the v6.1 backport on release/v6.1 at c1d1695. The regression test passes with the patch and fails without it. The issue remained under review, and multi-stage reset cases were not run. Updated the existing OTA power-loss/lifecycle guidance.
- **ESP32-S3 ADC oneshot pad release — [esp-idf#19442](https://github.com/espressif/esp-idf/issues/19442), opened 2026-11-14.** S3 rev2, IDF v5.4.2-25-g858a988d6e, ADC1 channel 5/GPIO6, 47 kΩ/100 kΩ divider, 100 nF and 1 Hz sampling. The reporter sees the pin fall by about 1 V and stay loaded between reads; sar1_en_pad cleanup is suspected because the S3 disable-all helper is a no-op. Issue was in review. Updated the ADC skill with explicit evidence limits.
- **ESP32-C6 OpenThread TX-done ISR assertion — [esp-idf#19425](https://github.com/espressif/esp-idf/issues/19425), opened 2026-11-12.** C6 rev0.2, IDF v6.1, C6-WROOM-1U; after hours with about 100 CSL children, a frame-pointer assertion in esp_ieee802154_transmit_done() is reported in ISR context followed by interrupt WDT. Non-deterministic, no standalone reproducer. A user comment proposes moving ieee802154_enter_critical() earlier in ieee802154_transmit_at(), but reports only an unverified no-crash observation. Updated the existing C6 802.15.4 skill; do not suppress the assertion or treat the proposed code movement as vendor-approved.
- **BLE controller after internal-DMA allocation failure — [esp-idf#19461](https://github.com/espressif/esp-idf/issues/19461), opened 2026-11-18.** S3 with 8 MB PSRAM, IDF v6.1; a NimBLE notification burst under MALLOC_CAP_INTERNAL|MALLOC_CAP_DMA pressure logs BLE_INIT: Malloc failed, then fragments are silently missing even after memory/credits recover and after reconnect; reset reportedly clears it. No standalone reproducer yet. Updated the existing BLE backpressure skill as a high-priority watch item, not a confirmed universal bug.

### Additional watchlist (not promoted to new skills)

- [esp-idf#19436](https://github.com/espressif/esp-idf/issues/19436): ESP32-PICO-V3-02 / classic ESP32 v3.1, IDF v6.1 Wi-Fi library; one 40.1-hour run entered a tight loop in wifi_rf_phy_enable() and triggered task WDT. Not reproducible on demand; preserve ELF/coredump and await vendor analysis.
- [esp-idf#19431](https://github.com/espressif/esp-idf/issues/19431): S31 BR/EDR outbound ACL completion stalls in a complex A2DP/AVRCP + Wi-Fi + ESP-NOW setup; 4/10 and 5/10 attempts on two v6.1 commits. Inbound ACL/HCI remain alive. No root cause confirmed.
- [esp-idf#19435](https://github.com/espressif/esp-idf/issues/19435): C3 rev0.4 / v6.1-dev report of roughly 36-byte leak when BLE is active and Wi-Fi is deinitialized immediately after a cancelled scan.
- [esp-idf#19443](https://github.com/espressif/esp-idf/issues/19443): C3 report of repeated PMF-protected disassociation retransmissions during esp_wifi_stop(); retain as a driver lifecycle watch item until the exact fix and reproduction are established.
- [arduino-esp32#13104](https://github.com/espressif/arduino-esp32/issues/13104): v3.3.12 NimBLE central can report status 2 if the peripheral starts ATT MTU exchange first; report covers C3/S3/C6/H2, not classic ESP32 Bluedroid. Closed issue; no matching fix was called out in 3.3.13 release notes, so re-test before relying on it.
- [arduino-esp32#13122](https://github.com/espressif/arduino-esp32/issues/13122): WROVER-E TouchRead T3/GPIO15 returned zero, but the board uses GPIO15 for microSD CMD and likely has a pull-up. Issue was closed as a board-level pin conflict, not an Arduino core defect; Freenove schematic was not published to confirm the resistor.

### Toolchain and release notes

- ESP-IDF [v6.1.1](https://github.com/espressif/esp-idf/releases/tag/v6.1.1) was released 2026-11-16. ESP-IDF v5.5.6 remains the current v5.5 maintenance release. The ESP-TEE stack-pointer advisory is fixed in v6.1.1 and v5.5.6; v6.0.4 was still listed as a future patched release at this scan. Keep the advisory's exact affected-version matrix.
- Arduino-ESP32 [3.3.13](https://github.com/espressif/arduino-esp32/releases/tag/3.3.13) was released 2026-11-17 on ESP-IDF v5.5.6+. It includes I2C slave fixes for newer SoCs, USB FAT registration correction for IDF 6+, Wi-Fi SSID behavior correction, a pioarduino SCons 4.11.1 build-script fix and other additions. Do not confuse 3.3.13 with Arduino 4.0.0-rc1 / IDF 6.1.
- PlatformIO platform-espressif32 v8.0.0 issues #1794 (IDF includes missing for .S files) and #1793 (IRAM growth due missing -Os) were reported as fixed by updating the global platformio/framework-arduinoespressif32 package; #1794 was confirmed by the reporter on Nov17. Pioarduino issue #563, caused by a PEP 440 6.2.0.post1 versus semver engine-range mismatch, was closed with Arduino 3.3.13; pioarduino 55.03.313 was released Nov17.
- Security advisories reviewed: ESP-TEE unvalidated stack pointer (Critical, GHSA-49x8-xqjg-2pjg), BLE Mesh GATT signed-to-unsigned read length (High, GHSA-rjvf-fxv5-x87j), and Thread Border Router ND6 option length (High, GHSA-c26h-gm53-qg83). These are already covered by the repository's security advisory skills; no duplicate skills were added. Apply the advisory's component/configuration and release matrix, not a blanket version label.

### Coverage and evidence limits

The new and updated skills are issue-driven documentation; they do not prove the bugs on every board. No hardware was attached to this scan. The new C6 secure-boot reset, S31 ADC/PHY lock cycle, S3 ADC pad loading, C6 OpenThread ISR and BLE controller memory-pressure reports all require target hardware validation. No Google search-volume or popularity ranking is claimed. No new Skill was created for reports already covered by the PSRAM/OTA/AES-GCM corpus or for reports that still lack sufficient independent reproduction.

## Weekly follow-up research: 2026-11-25

### Release and toolchain baseline

- ESP-IDF v6.1.1 was published 2026-11-16 as a bug-fix release; v5.5.6 remains the latest listed v5.5 patch in this scan.
- Arduino-ESP32 3.3.13 was published 2026-11-17 on the v5.5.6+ line; Arduino-ESP32 4.0.0 was published 2026-11-19 on ESP-IDF v6.1.1. Test the two core lines separately.
- PlatformIO espressif32 v8.0.0 was published 2026-10-19. Its release notes list Arduino 3.3.12 and ESP-IDF 6.0.0, not Arduino 3.3.13 or 4.0.0. Pin resolved framework/package versions; do not infer support from the platform version alone.
- The official Espressif advisory index showed no newly dated security advisory in 2026-11-18..2026-11-25. Latest listed security items include AR2026-005 (2026-06-11, ESP32-S3 AES key recovery via voltage fault injection) and AR2026-001 (2026-04-08, CPA/XTS-AES on ESP32-C5 and other listed series).

### New or materially updated upstream reports

| Source | Target and version | Symptom / evidence | Confidence and action |
|---|---|---|---|
| [ESP-IDF #19496](https://github.com/espressif/esp-idf/issues/19496) | ESP32-P4 rev1.3, IDF v6.0.1, custom board | JPEG encoder reportedly returns ESP_OK while a 64-byte cache-line block is zeroed under PSRAM traffic, about 1/100 busy encodes. | Medium: detailed cache-line/source analysis, newly opened and no maintainer response. Verify pre-DMA cache ownership and preserve CPU-written header. |
| [ESP-IDF #19494](https://github.com/espressif/esp-idf/issues/19494) | ESP32-P4 rev1.3, IDF v6.0.1 and master source review | Hardware AES-GCM initialization can leak earlier DMA descriptor/alignment allocations when a later allocation such as len_buf fails. | Medium-high for the allocation-unwind path: equivalent fix reportedly passed 10 injected failures and 384 buffer cases on v6.1.0/P4; rebased master patch has not been built on hardware. |
| [ESP-IDF #19493](https://github.com/espressif/esp-idf/issues/19493) | ESP32-H2 v1.2 and C6 v0.2, IDF v5.5.5 (same path reported on master) | With PM/tickless idle and 802.15.4 sleep, an ISR path can reach esp_phy_disable() and a mutex; lock_acquire_generic() aborts if the ISR cannot take it immediately. | Medium-high source-path confidence; reporter observed one H2 failure during Zigbee OTA with BLE active and supplied a lock-hammer reproducer. No maintainer confirmation yet. |
| [ESP-IDF #19492](https://github.com/espressif/esp-idf/issues/19492) | ESP32-H4HR2 ECO2 rev0.2, IDF v6.1.1 | Even hello_world boot loops with CPU_LOCKUP. Maintainer response says H4 ECO2 needs release/v6.2 or master; v6.1.x ROM linker script supports earlier H4 revisions only. | High confidence as a target/version compatibility boundary from maintainer response. Re-run idf.py --preview set-target esp32h4 and rebuild with the supported branch. |
| [ESP-IDF #19487](https://github.com/espressif/esp-idf/issues/19487) | Classic ESP32 D0WD-Q5 hardware revision 1.01 (read via Arduino core; not re-queried with esptool), IDF v6.1.1, dual-core, 16 MB external flash; Arduino 3.3.11 as component in minimal repro | Reading the non-running OTA slot with esp_ota_get_state_partition() after tasks on both cores start can assert in esp_ipc_isr_release_other_cpu(); a later minimal repro reports 3/3 WDT resets. | Medium: later reproducer is strong, but an earlier maintainer stress attempt did not reproduce the original assert. Keep panic and WDT signatures distinct; no confirmed root cause or fix. |
| [ESP-IDF #19462](https://github.com/espressif/esp-idf/issues/19462) | ESP32-P4 rev1.3, IDF v6.1.1, PPA / DSI rotation | Two of 116 tested geometries stalled when the remaining tail equaled 1536 bits; on_trans_done did not fire. A local '<=' comparison completed all 116 geometries, but other 1536-bit shapes passed. | Medium-high reproducibility on reporter's setup; patch not upstream-verified. Sweep shape/rotation/scanout combinations before adopting. |
| [ESP-IDF #19464](https://github.com/espressif/esp-idf/issues/19464) | ESP32-C5 rev1.0, IDF v6.0.3 and release/v6.0, external 32.768 kHz RTC crystal | WIFI_PS_MAX_MODEM + listen interval 30 + automatic light sleep reportedly misses about 3/4 beacon windows; measured 190–206 ms radio-on and 16.2–17.3 mAs per wake. | Medium: detailed current and Wi-Fi counters, but no stock-example reproducer and no confirmed root cause/workaround. |
| [ESP-IDF #19463](https://github.com/espressif/esp-idf/issues/19463) | ESP32-S3 Border Router + ESP32-C6 Thread RCP, IDF v6.0.2 | DNS-SD discovery-proxy queries reportedly leak 32 bytes per lookup; heap tracing saw nine 32-byte blocks in two hours. Relevant implementation ships prebuilt. | Medium-high reporter evidence; not reproduced on newer hardware/SDK and no direct source patch available. |
| [ESP-IDF #19466](https://github.com/espressif/esp-idf/issues/19466) | Classic ESP32 rev1.0, IDF v6.1.1, 240 MHz | One of six tested chips reportedly misread RTC fast-memory words at 240 MHz; task stacks placed there after heap-order changes, causing a boot loop. 80/160 MHz and other tested chips did not show it. | Medium, highly chip-specific. Disabling CONFIG_ESP_SYSTEM_ALLOW_RTC_FAST_MEM_AS_HEAP avoided the reporter's failure but changes available heap; verify exact silicon and official errata. |
| [ESP-IDF #19468](https://github.com/espressif/esp-idf/issues/19468) | ESP32-D0WD-V3 rev3.0, IDF v6.1/v6.1.1, ESP32-CAM | I2C slave initialization aborts in lock_acquire_generic() when I2C debug logging is enabled; stack reaches i2c_select_periph_clock(). | Low-medium: debug logging was enabled, but why the log call triggers the lock abort remains unclear. Needs a minimal reproducer and maintainer analysis. |
| [ESP-IDF #19495](https://github.com/espressif/esp-idf/issues/19495) | ESP32-S3, IDF v5.5.5 (ESPHome 2026.11.0) | Cancelling a Bluedroid LE connection during link formation reportedly leaves the GATT TCB closing; later opens to that peer fail with status 133 until reboot. | Low-medium: one live incident, no deliberate reproducer; code-path analysis is plausible but v5.5.6/v6.1.1/master were not re-run. |
| [Arduino-ESP32 #13137](https://github.com/espressif/arduino-esp32/issues/13137) and [PR #13138](https://github.com/espressif/arduino-esp32/pull/13138) | ESP32-S3 native USB Serial/JTAG, Arduino 3.3.13; reporter also says 4.0.0 | Host data arriving before Serial.begin() can leave RX permanently NAKed because HWCDC::begin() clears the pending OUT-receive flag. Proposed PR preserves that flag; author reports 5/5 early-write tests pass with the patch vs 0/5 on 3.3.13. | High reporter-side reproduction, but PR remains open and unreleased. Do not call it fixed in a released core. |
| [Arduino-ESP32 #13141](https://github.com/espressif/arduino-esp32/issues/13141) | ESP32-S3 native USB Serial/JTAG, Arduino 3.3.13, IDF 5.5.6, pioarduino 55.03.313 | With host port open, IN-token ISR reportedly consumes about 20% CPU at 80 MHz and causes UART0 RX overflow/loss in an 8.2 KB transfer at 230400 baud. | Medium-high measurements from one custom board; investigation remains open. Separate from #13137 and not fixed by PR #13138. |
| [Arduino-ESP32 #13159](https://github.com/espressif/arduino-esp32/issues/13159) | ESP32-C6, Arduino 4.0.0 / IDF 6.1.1; 3.3.13 reportedly works | Stock Zigbee Contact Switch example boot loops with Load access fault in setAttributePersistent() during global construction. | Low: one report awaiting triage. Compare Zigbee mode/partition scheme and initialization order; do not generalize to all Zigbee endpoints. |

### Domain coverage this week

- **Wi-Fi / power save:** C5 beacon-window misses (#19464); no verified workaround.
- **BLE / Bluedroid:** GATT cancel-open race (#19495); native USB regressions are a separate peripheral path.
- **IEEE 802.15.4 / Zigbee:** ISR-to-PHY-lock abort (#19493); Arduino C6 Zigbee global-constructor boot loop (#13159).
- **FreeRTOS / SMP:** OTA non-running-slot assertion (#19487); earlier #19450/#19456 remain tracked separately.
- **Memory / PSRAM / DMA:** P4 JPEG cache-line corruption (#19496), P4 AES-GCM allocation leak (#19494), OpenThread BR leak (#19463), classic ESP32 RTC fast-memory anomaly (#19466).
- **Flash / OTA:** #19487 is a runtime state-query issue, not evidence of general OTA image or partition corruption.
- **Display / DMA:** P4 PPA exact-tail stall (#19462).
- **USB / UART:** Arduino #13137/#13141; PR #13138 remains open.
- **I2C:** #19468 needs a minimal reproducer and maintainer diagnosis.
- **TLS/MQTT, Modbus/RS485/LoRa, ADC, Ethernet:** no new high-confidence issue from the selected primary sources this week.

### Community-source cross-check and limits

A targeted Reddit/Stack Overflow search did not surface an independent, current reproduction of these exact November 2026 regressions. Older USB/JTAG troubleshooting discussions are not evidence for the 3.3.13 regressions and were not used to infer root cause. No search-volume or popularity claims are made.

All issue reports above are scoped to the reporter's exact target/revision/framework tuple. A proposed patch, reporter-side test, maintainer comment, merged upstream fix and released fix are different evidence states. Hardware, RF, power, cache-coherency and silicon-anomaly claims still require the exact board and instrumentation.
